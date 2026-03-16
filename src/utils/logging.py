#!/usr/bin/env python3
"""
增強日誌系統 - 結構化日誌、上下文管理器、性能監控

基於Coder Agent的設計要求：
1. 結構化日誌格式
2. 上下文管理器
3. 性能監控裝飾器
4. 系統健康檢查
"""

import logging
import logging.handlers
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from functools import wraps
import inspect
import sys

# 默認日誌格式
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
STRUCTURED_LOG_FORMAT = json.dumps({
    "timestamp": "%(asctime)s",
    "logger": "%(name)s",
    "level": "%(levelname)s",
    "message": "%(message)s",
    "module": "%(module)s",
    "function": "%(funcName)s",
    "line": "%(lineno)d"
})

class StructuredFormatter(logging.Formatter):
    """結構化日誌格式化器"""
    
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)
        
    def format(self, record):
        """格式化日誌記錄為結構化JSON"""
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.threadName,
            "process": record.processName
        }
        
        # 添加額外字段
        if hasattr(record, 'extra'):
            log_record.update(record.extra)
            
        # 添加異常信息
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record, ensure_ascii=False)


def setup_logger(
    name: str = "project-memory-manager",
    level: str = "INFO",
    log_file: Optional[Path] = None,
    structured: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    設置日誌記錄器
    
    Args:
        name: 日誌記錄器名稱
        level: 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日誌文件路徑（None則只輸出到控制台）
        structured: 是否使用結構化JSON格式
        max_bytes: 日誌文件最大字節數
        backup_count: 備份文件數量
        
    Returns:
        配置好的日誌記錄器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 移除現有的處理器
    logger.handlers.clear()
    
    # 創建控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    if structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
    logger.addHandler(console_handler)
    
    # 創建文件處理器（如果指定了日誌文件）
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        if structured:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
            
        logger.addHandler(file_handler)
    
    return logger


class LogContext:
    """日誌上下文管理器
    
    在上下文中添加額外的日誌字段
    """
    
    def __init__(self, logger: logging.Logger, **context_fields):
        """
        初始化日誌上下文
        
        Args:
            logger: 日誌記錄器
            **context_fields: 上下文字段
        """
        self.logger = logger
        self.context_fields = context_fields
        self.old_extra = {}
        
    def __enter__(self):
        """進入上下文，設置額外字段"""
        # 保存原有的extra字段
        if hasattr(self.logger, 'extra'):
            self.old_extra = getattr(self.logger, 'extra', {}).copy()
        
        # 合併新的上下文字段
        new_extra = {**self.old_extra, **self.context_fields}
        setattr(self.logger, 'extra', new_extra)
        
        self.logger.debug(f"進入日誌上下文: {self.context_fields}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，恢復原有字段"""
        setattr(self.logger, 'extra', self.old_extra)
        
        if exc_type is not None:
            self.logger.error(f"上下文異常: {exc_val}", exc_info=True)
        else:
            self.logger.debug("退出日誌上下文")
            
        return False  # 不處理異常，繼續傳播


def log_performance(threshold_ms: float = 100.0):
    """
    性能監控裝飾器
    
    記錄函數執行時間，超過閾值時輸出警告
    
    Args:
        threshold_ms: 警告閾值（毫秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            
            start_time = time.time()
            result = None
            error = None
            
            try:
                # 記錄函數開始
                logger.debug(f"開始執行: {func.__name__}")
                
                # 執行函數
                result = func(*args, **kwargs)
                
                # 計算執行時間
                elapsed_ms = (time.time() - start_time) * 1000
                
                # 記錄結果
                if elapsed_ms > threshold_ms:
                    logger.warning(
                        f"函數 {func.__name__} 執行緩慢: {elapsed_ms:.2f}ms "
                        f"(閾值: {threshold_ms}ms)"
                    )
                else:
                    logger.debug(f"函數 {func.__name__} 執行完成: {elapsed_ms:.2f}ms")
                    
                return result
                
            except Exception as e:
                # 記錄異常
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"函數 {func.__name__} 執行失敗: {elapsed_ms:.2f}ms, "
                    f"錯誤: {e}",
                    exc_info=True
                )
                raise
                
        return wrapper
    return decorator


class HealthMonitor:
    """系統健康監控器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.metrics = {}
        self.checkpoints = {}
        
    def start_checkpoint(self, name: str):
        """開始檢查點計時"""
        self.checkpoints[name] = time.time()
        self.logger.debug(f"開始檢查點: {name}")
        
    def end_checkpoint(self, name: str) -> float:
        """結束檢查點並返回耗時（秒）"""
        if name not in self.checkpoints:
            self.logger.warning(f"檢查點不存在: {name}")
            return 0.0
            
        elapsed = time.time() - self.checkpoints[name]
        self.metrics[f"{name}_time"] = elapsed
        
        self.logger.debug(f"結束檢查點 {name}: {elapsed:.3f}s")
        del self.checkpoints[name]
        
        return elapsed
        
    def record_metric(self, name: str, value: float):
        """記錄指標"""
        self.metrics[name] = value
        self.logger.debug(f"記錄指標 {name}: {value}")
        
    def get_health_report(self) -> Dict[str, Any]:
        """獲取健康報告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics.copy(),
            "status": "healthy"
        }
        
        # 簡單的健康檢查邏輯
        if "error_count" in self.metrics and self.metrics["error_count"] > 10:
            report["status"] = "warning"
        if "error_count" in self.metrics and self.metrics["error_count"] > 50:
            report["status"] = "critical"
            
        return report
    
    def log_health_report(self):
        """記錄健康報告到日誌"""
        report = self.get_health_report()
        self.logger.info(f"系統健康報告: {json.dumps(report, ensure_ascii=False)}")


def get_caller_info() -> Dict[str, Any]:
    """獲取調用者信息"""
    frame = inspect.currentframe()
    
    # 向上追溯兩層：get_caller_info -> 調用者
    if frame and frame.f_back and frame.f_back.f_back:
        caller_frame = frame.f_back.f_back
        return {
            "filename": caller_frame.f_code.co_filename,
            "function": caller_frame.f_code.co_name,
            "line": caller_frame.f_lineno,
            "module": inspect.getmodule(caller_frame).__name__ if inspect.getmodule(caller_frame) else "unknown"
        }
    
    return {"filename": "unknown", "function": "unknown", "line": 0, "module": "unknown"}


# 全局健康監控器實例
_health_monitor = None

def get_health_monitor() -> HealthMonitor:
    """獲取全局健康監控器實例"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor


if __name__ == "__main__":
    # 測試日誌系統
    logger = setup_logger("test-logger", level="DEBUG", structured=True)
    
    print("=== 測試基本日誌 ===")
    logger.info("這是一條信息日誌")
    logger.warning("這是一條警告日誌")
    
    print("\n=== 測試日誌上下文 ===")
    with LogContext(logger, user_id="123", request_id="abc"):
        logger.info("在上下文中的日誌")
        logger.info("另一條上下文日誌")
    
    logger.info("上下文外的日誌")
    
    print("\n=== 測試性能監控 ===")
    
    @log_performance(threshold_ms=50)
    def slow_function():
        time.sleep(0.1)  # 100ms
        return "完成"
    
    @log_performance(threshold_ms=200)
    def fast_function():
        time.sleep(0.05)  # 50ms
        return "快速完成"
    
    try:
        slow_function()
        fast_function()
    except Exception as e:
        logger.error(f"測試失敗: {e}")
    
    print("\n=== 測試健康監控 ===")
    monitor = get_health_monitor()
    monitor.start_checkpoint("test_operation")
    time.sleep(0.1)
    monitor.end_checkpoint("test_operation")
    monitor.record_metric("success_count", 5)
    monitor.record_metric("error_count", 2)
    
    report = monitor.get_health_report()
    print(f"健康報告: {json.dumps(report, indent=2)}")