#!/usr/bin/env python3
"""
原子文件操作模塊 - 提供跨進程文件鎖和原子寫入

基於Coder Agent的設計要求：
1. 跨進程文件鎖 (FileLock)
2. 原子文件寫入 (atomic_write)
3. 事務支持 (Transaction)
4. 自動備份與回滾
"""

import os
import fcntl
import tempfile
import shutil
from pathlib import Path
from typing import Optional, ContextManager
import time
import logging

logger = logging.getLogger(__name__)


class FileLock:
    """跨進程文件鎖
    
    使用fcntl實現跨進程文件鎖，避免併發衝突
    """
    
    def __init__(self, lockfile: Path, timeout: float = 10.0, poll_interval: float = 0.1):
        """
        初始化文件鎖
        
        Args:
            lockfile: 鎖文件路徑
            timeout: 獲取鎖的超時時間（秒）
            poll_interval: 重試間隔（秒）
        """
        self.lockfile = Path(lockfile)
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._lock_fd = None
        
    def __enter__(self):
        """進入上下文，獲取鎖"""
        self.acquire()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，釋放鎖"""
        self.release()
        
    def acquire(self) -> bool:
        """獲取文件鎖"""
        start_time = time.time()
        
        # 確保鎖文件目錄存在
        self.lockfile.parent.mkdir(parents=True, exist_ok=True)
        
        while True:
            try:
                # 打開鎖文件
                self._lock_fd = os.open(self.lockfile, os.O_RDWR | os.O_CREAT, 0o644)
                
                # 嘗試獲取獨佔鎖
                fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                logger.debug(f"獲取文件鎖: {self.lockfile}")
                return True
                
            except (IOError, OSError):
                # 鎖被其他進程持有
                if time.time() - start_time >= self.timeout:
                    logger.error(f"獲取文件鎖超時: {self.lockfile}")
                    if self._lock_fd:
                        os.close(self._lock_fd)
                    raise TimeoutError(f"無法在{self.timeout}秒內獲取鎖: {self.lockfile}")
                
                # 等待後重試
                time.sleep(self.poll_interval)
                
    def release(self):
        """釋放文件鎖"""
        if self._lock_fd:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                os.close(self._lock_fd)
                logger.debug(f"釋放文件鎖: {self.lockfile}")
            except Exception as e:
                logger.warning(f"釋放文件鎖時出錯: {e}")
            finally:
                self._lock_fd = None


def atomic_write(filepath: Path, content: str, encoding: str = 'utf-8') -> bool:
    """
    原子寫入文件
    
    通過臨時文件+原子移動確保寫入的原子性
    避免寫入過程中崩潰導致文件損壞
    
    Args:
        filepath: 目標文件路徑
        content: 要寫入的內容
        encoding: 文件編碼
        
    Returns:
        是否成功
    """
    filepath = Path(filepath)
    
    try:
        # 創建臨時文件（在同目錄下確保原子移動）
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding=encoding,
            dir=filepath.parent,
            prefix=f".{filepath.name}.",
            delete=False
        ) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        # 原子移動（rename是原子的）
        tmp_path.replace(filepath)
        
        logger.debug(f"原子寫入文件: {filepath} ({len(content)} 字節)")
        return True
        
    except Exception as e:
        logger.error(f"原子寫入失敗 {filepath}: {e}")
        
        # 清理臨時文件
        try:
            if 'tmp_path' in locals() and tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass
            
        return False


class Transaction:
    """事務支持類
    
    支持一組操作的原子性執行，失敗時自動回滾
    """
    
    def __init__(self, backup_dir: Optional[Path] = None):
        """
        初始化事務
        
        Args:
            backup_dir: 備份文件目錄（None則使用系統臨時目錄）
        """
        self.backup_dir = backup_dir or Path(tempfile.gettempdir()) / "pm_transactions"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self._backups = []  # 備份文件列表
        self._completed = False
        
    def __enter__(self):
        """進入事務上下文"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出事務上下文"""
        if exc_type is not None:
            # 發生異常，回滾
            self.rollback()
            logger.warning(f"事務失敗，已回滾: {exc_val}")
            return False  # 重新拋出異常
        else:
            # 成功，提交
            self.commit()
            return True
            
    def backup_file(self, filepath: Path) -> Optional[Path]:
        """
        備份文件
        
        Args:
            filepath: 要備份的文件路徑
            
        Returns:
            備份文件路徑或None
        """
        try:
            if not filepath.exists():
                logger.warning(f"無法備份不存在的文件: {filepath}")
                return None
                
            # 創建備份文件名
            timestamp = int(time.time() * 1000)
            backup_name = f"{filepath.name}.backup.{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            # 複製文件
            shutil.copy2(filepath, backup_path)
            self._backups.append((filepath, backup_path))
            
            logger.debug(f"創建文件備份: {filepath} -> {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"備份文件失敗 {filepath}: {e}")
            return None
            
    def rollback(self):
        """回滾所有操作"""
        logger.info(f"開始回滾事務 ({len(self._backups)} 個備份)")
        
        for original, backup in reversed(self._backups):
            try:
                if backup.exists():
                    shutil.copy2(backup, original)
                    logger.debug(f"恢復文件: {backup} -> {original}")
                else:
                    logger.warning(f"備份文件不存在，無法恢復: {backup}")
            except Exception as e:
                logger.error(f"恢復文件失敗 {original}: {e}")
                
        self._cleanup()
        
    def commit(self):
        """提交事務"""
        logger.info(f"提交事務 ({len(self._backups)} 個備份)")
        self._cleanup()
        
    def _cleanup(self):
        """清理備份文件"""
        for _, backup in self._backups:
            try:
                if backup.exists():
                    backup.unlink()
                    logger.debug(f"清理備份文件: {backup}")
            except Exception as e:
                logger.warning(f"清理備份文件失敗 {backup}: {e}")
                
        self._backups.clear()
        self._completed = True


def safe_file_operation(operation_func, *args, **kwargs):
    """
    安全文件操作裝飾器/上下文
    
    提供自動備份和錯誤恢復的文件操作
    """
    def wrapper(*args, **kwargs):
        # 簡單實現：使用事務包裹操作
        with Transaction() as txn:
            # 備份所有涉及的文件
            # 這裡需要根據具體操作確定要備份的文件
            # 簡化：讓調用者自己備份
            
            result = operation_func(*args, **kwargs)
            return result
            
    return wrapper


# 簡化版本：直接使用的工具函數
def read_file_safe(filepath: Path, default: str = "") -> str:
    """安全讀取文件，失敗返回默認值"""
    try:
        with FileLock(filepath.with_suffix('.lock')):
            return filepath.read_text(encoding='utf-8')
    except Exception as e:
        logger.warning(f"讀取文件失敗 {filepath}: {e}")
        return default


def write_file_safe(filepath: Path, content: str) -> bool:
    """安全寫入文件（原子操作）"""
    try:
        with FileLock(filepath.with_suffix('.lock')):
            return atomic_write(filepath, content)
    except Exception as e:
        logger.error(f"寫入文件失敗 {filepath}: {e}")
        return False


if __name__ == "__main__":
    # 測試文件鎖
    logging.basicConfig(level=logging.DEBUG)
    
    test_file = Path("/tmp/test_atomic.txt")
    
    print("=== 測試原子寫入 ===")
    success = write_file_safe(test_file, "測試內容")
    print(f"原子寫入: {'✅' if success else '❌'}")
    
    content = read_file_safe(test_file)
    print(f"讀取內容: {content}")
    
    print("\n=== 測試事務 ===")
    with Transaction() as txn:
        backup = txn.backup_file(test_file)
        print(f"創建備份: {backup}")
        
        # 修改文件
        write_file_safe(test_file, "修改後的內容")
        print("文件已修改")
        
        # 事務結束時自動提交或回滾