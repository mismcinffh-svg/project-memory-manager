#!/usr/bin/env python3
"""
安全模塊 - 路徑驗證與命令安全

基於Sergio的安全審查要求：
1. 防止路徑遍歷攻擊
2. 驗證所有文件操作在workspace範圍內
3. 提供安全的命令執行指引
"""

import os
import re
from pathlib import Path
from typing import Optional, Tuple, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SecurityValidator:
    """安全驗證器"""
    
    def __init__(self, workspace_root: Optional[Path] = None):
        """初始化安全驗證器
        
        Args:
            workspace_root: OpenClaw workspace根目錄，如果為None則自動檢測
        """
        if workspace_root is None:
            # 嘗試從環境變量獲取
            workspace_env = os.environ.get("OPENCLAW_WORKSPACE")
            if workspace_env:
                self.workspace_root = Path(workspace_env).resolve()
            else:
                # 備用方案：向上查找包含projects/的目錄
                current_dir = Path(__file__).parent
                for _ in range(5):
                    projects_dir = current_dir / "projects"
                    if projects_dir.exists():
                        self.workspace_root = current_dir
                        break
                    current_dir = current_dir.parent
                else:
                    self.workspace_root = Path.cwd()
        else:
            self.workspace_root = Path(workspace_root).resolve()
        
        logger.info(f"安全驗證器初始化，workspace根目錄: {self.workspace_root}")
    
    def validate_path(self, path: Path, allow_absolute: bool = False) -> Tuple[bool, str]:
        """驗證路徑是否在workspace範圍內
        
        Args:
            path: 要驗證的路徑
            allow_absolute: 是否允許絕對路徑（仍必須在workspace內）
            
        Returns:
            (是否安全, 錯誤信息)
        """
        try:
            # 解析路徑
            resolved_path = path.resolve()
            
            # 檢查是否在workspace內
            try:
                # 使用relative_to檢查是否在workspace內
                relative = resolved_path.relative_to(self.workspace_root)
            except ValueError:
                return False, f"路徑不在workspace範圍內: {resolved_path}"
            
            # 額外檢查：防止目錄遍歷攻擊（如../../../etc/passwd）
            # 確保相對路徑不包含父目錄引用
            if ".." in str(relative):
                # 檢查是否實際離開了workspace（已通過relative_to檢查，但謹慎起見）
                normalized = os.path.normpath(str(relative))
                if normalized.startswith("..") or "/../" in normalized:
                    return False, f"路徑包含非法父目錄引用: {relative}"
            
            # 檢查是否為敏感文件
            sensitive_patterns = [
                r'.*\.(pem|key|env|secret)$',
                r'.*password.*',
                r'.*token.*',
                r'.*credential.*',
                r'/\.(git|ssh)/',
            ]
            
            path_str = str(resolved_path)
            for pattern in sensitive_patterns:
                if re.search(pattern, path_str, re.IGNORECASE):
                    logger.warning(f"警告：訪問可能敏感的文件: {path_str}")
                    # 不阻止，但記錄警告
            
            return True, ""
            
        except Exception as e:
            logger.error(f"路徑驗證失敗: {e}")
            return False, f"路徑驗證異常: {e}"
    
    def sanitize_command(self, command: str) -> Tuple[bool, str, Optional[str]]:
        """清理和驗證命令
        
        Args:
            command: 原始命令
            
        Returns:
            (是否安全, 清理後命令, 錯誤信息)
        """
        # 危險命令黑名單
        dangerous_patterns = [
            r'rm\s+-rf',
            r'format\s+',
            r'dd\s+',
            r'mkfs\.',
            r'>/dev/sd',
            r':(){:|:&};:',  # fork炸彈
            r'chmod\s+777',
            r'wget\s+.*\|\s*sh',
            r'curl\s+.*\|\s*sh',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False, command, f"命令包含危險模式: {pattern}"
        
        # 允許的git命令白名單
        allowed_git_commands = [
            r'git\s+add',
            r'git\s+commit',
            r'git\s+push',
            r'git\s+pull',
            r'git\s+status',
            r'git\s+log',
            r'git\s+diff',
            r'git\s+branch',
            r'git\s+tag',
            r'git\s+clone',
            r'git\s+remote',
            r'git\s+config',
            r'git\s+checkout',
            r'git\s+merge',
            r'git\s+fetch',
        ]
        
        # 如果是git命令，檢查是否在白名單內
        if command.strip().startswith('git'):
            is_allowed = any(re.search(pattern, command, re.IGNORECASE) 
                           for pattern in allowed_git_commands)
            if not is_allowed:
                return False, command, f"Git命令不在白名單內: {command}"
        
        # 清理命令：移除多餘空格，但不修改內容
        sanitized = ' '.join(command.split())
        
        return True, sanitized, None
    
    def get_safe_workspace_path(self, relative_path: str) -> Optional[Path]:
        """獲取workspace內的安全路徑
        
        Args:
            relative_path: 相對路徑
            
        Returns:
            安全路徑或None（如果不安全）
        """
        try:
            # 構建路徑
            target_path = (self.workspace_root / relative_path).resolve()
            
            # 驗證
            is_safe, error = self.validate_path(target_path)
            if not is_safe:
                logger.error(f"不安全的路徑: {error}")
                return None
            
            return target_path
            
        except Exception as e:
            logger.error(f"獲取安全路徑失敗: {e}")
            return None
    
    def check_dependencies(self) -> List[str]:
        """檢查系統依賴
        
        Returns:
            缺失的依賴列表
        """
        missing = []
        
        # 檢查Python版本
        import sys
        if sys.version_info < (3, 8):
            missing.append(f"Python 3.8+ (當前: {sys.version})")
        
        # 檢查git
        try:
            import subprocess
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                missing.append("git")
        except:
            missing.append("git")
        
        # 檢查GitHub CLI (可選)
        try:
            import subprocess
            result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning("GitHub CLI (gh) 未安裝，自動創建倉庫功能將不可用")
        except:
            logger.warning("GitHub CLI (gh) 未安裝，自動創建倉庫功能將不可用")
        
        return missing
    
    def create_backup(self, file_path: Path) -> Optional[Path]:
        """創建文件備份
        
        Args:
            file_path: 要備份的文件
            
        Returns:
            備份文件路徑或None
        """
        try:
            # 驗證路徑
            is_safe, error = self.validate_path(file_path)
            if not is_safe:
                logger.error(f"無法備份不安全的路徑: {error}")
                return None
            
            if not file_path.exists():
                logger.warning(f"文件不存在，無需備份: {file_path}")
                return None
            
            # 創建備份路徑
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = file_path.parent / f"{file_path.name}.bak.{timestamp}"
            
            # 複製文件
            import shutil
            shutil.copy2(file_path, backup_path)
            
            logger.info(f"創建備份: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"創建備份失敗: {e}")
            return None
    
    def restore_backup(self, file_path: Path, backup_path: Optional[Path] = None) -> bool:
        """從備份恢復文件
        
        Args:
            file_path: 要恢復的文件
            backup_path: 特定備份文件（None則使用最新）
            
        Returns:
            是否成功
        """
        try:
            if backup_path is None:
                # 查找最新備份
                backup_dir = file_path.parent
                backup_pattern = f"{file_path.name}.bak.*"
                
                backups = list(backup_dir.glob(backup_pattern))
                if not backups:
                    logger.error(f"找不到備份文件: {backup_pattern}")
                    return False
                
                # 按修改時間排序
                backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                backup_path = backups[0]
            
            # 驗證備份路徑
            is_safe, error = self.validate_path(backup_path)
            if not is_safe:
                logger.error(f"不安全的路份路徑: {error}")
                return False
            
            # 恢復文件
            import shutil
            shutil.copy2(backup_path, file_path)
            
            logger.info(f"從備份恢復: {backup_path} -> {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"恢復備份失敗: {e}")
            return False


def safe_execute_operation(operation_func, *args, backup: bool = True, **kwargs):
    """安全執行操作（帶備份和恢復）
    
    Args:
        operation_func: 要執行的函數
        backup: 是否創建備份
        *args, **kwargs: 傳遞給operation_func的參數
        
    Returns:
        (是否成功, 結果, 錯誤信息)
    """
    validator = SecurityValidator()
    
    try:
        # 如果需要備份，檢查是否有文件路徑參數
        if backup and args:
            # 簡單實現：第一個參數如果是Path，嘗試備份
            if isinstance(args[0], Path):
                validator.create_backup(args[0])
        
        # 執行操作
        result = operation_func(*args, **kwargs)
        return True, result, ""
        
    except Exception as e:
        logger.error(f"操作執行失敗: {e}")
        
        # 嘗試恢復備份
        if backup and args and isinstance(args[0], Path):
            validator.restore_backup(args[0])
        
        return False, None, str(e)


if __name__ == "__main__":
    # 測試安全模塊
    import sys
    
    validator = SecurityValidator()
    
    print("=== 安全模塊測試 ===")
    print(f"Workspace根目錄: {validator.workspace_root}")
    
    # 測試路徑驗證
    test_paths = [
        Path("."),
        Path(__file__),
        Path("/etc/passwd"),
        Path("../../etc/passwd"),
    ]
    
    for path in test_paths:
        is_safe, error = validator.validate_path(path)
        print(f"{path}: {'✅ 安全' if is_safe else '❌ 不安全'} {error}")
    
    # 測試命令清理
    test_commands = [
        "git status",
        "rm -rf /",
        "git add . && git commit -m 'test'",
    ]
    
    for cmd in test_commands:
        is_safe, sanitized, error = validator.sanitize_command(cmd)
        print(f"{cmd}: {'✅ 安全' if is_safe else '❌ 不安全'} {error}")
    
    # 檢查依賴
    missing = validator.check_dependencies()
    if missing:
        print(f"❌ 缺失依賴: {missing}")
    else:
        print("✅ 所有依賴已安裝")
    
    print("=== 測試完成 ===")