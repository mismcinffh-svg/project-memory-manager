#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
進度條顯示模塊 - 支持百分比進度條
模仿專業工具的進度顯示
"""

import sys
import time
import curses
from typing import Optional


class ProgressBar:
    """進度條類 - 支持 curses 和文本模式"""
    
    def __init__(self, title: str = "處理中", width: int = 50, 
                 show_percentage: bool = True, show_time: bool = True):
        self.title = title
        self.width = width
        self.show_percentage = show_percentage
        self.show_time = show_time
        self.start_time = time.time()
        self.last_update = 0
        self.min_update_interval = 0.05  # 最小更新間隔（秒）
    
    def _curses_progress(self, stdscr, progress: float, message: str = ""):
        """在 curses 環境中顯示進度條"""
        height, width = stdscr.getmaxyx()
        
        # 計算進度條位置（居中）
        bar_width = min(self.width, width - 10)
        bar_x = max(0, (width - bar_width) // 2)
        bar_y = max(0, (height - 5) // 2)
        
        # 清屏
        stdscr.clear()
        
        # 顯示標題
        title = f" {self.title} "
        title_x = max(0, (width - len(title)) // 2)
        stdscr.addstr(bar_y - 2, title_x, title, curses.A_BOLD)
        
        # 繪製進度條邊框
        bar_border = "[" + " " * bar_width + "]"
        border_x = bar_x - 1
        stdscr.addstr(bar_y, border_x, bar_border)
        
        # 繪製進度條內容
        filled_width = int(bar_width * progress)
        if filled_width > 0:
            progress_bar = "█" * filled_width
            stdscr.addstr(bar_y, bar_x, progress_bar, curses.color_pair(2))
        
        # 顯示百分比
        if self.show_percentage:
            percentage = f"{progress*100:5.1f}%"
            percent_x = bar_x + bar_width + 2
            if percent_x + len(percentage) < width:
                stdscr.addstr(bar_y, percent_x, percentage)
        
        # 顯示消息
        if message:
            msg_x = max(0, (width - len(message)) // 2)
            stdscr.addstr(bar_y + 2, msg_x, message)
        
        # 顯示耗時
        if self.show_time:
            elapsed = time.time() - self.start_time
            time_str = f"耗時: {elapsed:.1f}秒"
            time_x = max(0, (width - len(time_str)) // 2)
            stdscr.addstr(bar_y + 3, time_x, time_str)
        
        stdscr.refresh()
    
    def _text_progress(self, progress: float, message: str = ""):
        """在文本模式下顯示進度條"""
        # 清屏或換行
        if progress == 0:
            print("\n" * 2)
        else:
            print("\r", end="", flush=True)
        
        # 計算填充寬度
        filled_width = int(self.width * progress)
        empty_width = self.width - filled_width
        
        # 繪製進度條
        bar = "[" + "█" * filled_width + " " * empty_width + "]"
        
        # 添加百分比
        if self.show_percentage:
            bar += f" {progress*100:5.1f}%"
        
        # 添加消息
        if message:
            bar += f" | {message}"
        
        # 添加耗時
        if self.show_time:
            elapsed = time.time() - self.start_time
            bar += f" | 耗時: {elapsed:.1f}秒"
        
        print(bar, end="", flush=True)
        
        # 完成時換行
        if progress >= 1.0:
            print()
    
    def update(self, progress: float, message: str = "", 
               force: bool = False) -> bool:
        """
        更新進度條
        
        Args:
            progress: 進度 (0.0 - 1.0)
            message: 當前狀態消息
            force: 是否強制更新（忽略最小間隔）
        
        Returns:
            bool: 是否實際進行了更新
        """
        # 限制進度範圍
        progress = max(0.0, min(1.0, progress))
        
        # 檢查是否需要更新（避免過度刷新）
        current_time = time.time()
        if not force and current_time - self.last_update < self.min_update_interval:
            return False
        
        self.last_update = current_time
        
        # 根據環境選擇顯示模式
        try:
            # 嘗試使用 curses 模式
            curses.wrapper(self._curses_progress, progress, message)
            return True
        except:
            # 回退到文本模式
            self._text_progress(progress, message)
            return True
    
    def complete(self, message: str = "完成！"):
        """完成進度條"""
        self.update(1.0, message, force=True)
        time.sleep(0.5)  # 讓用戶看到完成狀態


class Spinner:
    """旋轉指示器（用於不確定進度的任務）"""
    
    def __init__(self, message: str = "處理中"):
        self.message = message
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.running = False
    
    def _curses_spinner(self, stdscr):
        """curses 模式的旋轉指示器"""
        height, width = stdscr.getmaxyx()
        
        # 計算位置
        spinner_char = self.spinner_chars[self.spinner_index]
        spinner_text = f" {spinner_char} {self.message} "
        
        text_x = max(0, (width - len(spinner_text)) // 2)
        text_y = max(0, height // 2)
        
        stdscr.clear()
        stdscr.addstr(text_y, text_x, spinner_text, curses.A_BOLD)
        stdscr.refresh()
        
        # 更新旋轉指針
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
    
    def _text_spinner(self):
        """文本模式的旋轉指示器"""
        spinner_char = self.spinner_chars[self.spinner_index]
        print(f"\r{spinner_char} {self.message}", end="", flush=True)
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
    
    def start(self):
        """開始旋轉指示器"""
        self.running = True
        print()  # 開始前換行
    
    def update(self):
        """更新旋轉指示器"""
        if not self.running:
            return
        
        try:
            # 嘗試使用 curses 模式
            curses.wrapper(self._curses_spinner)
        except:
            # 回退到文本模式
            self._text_spinner()
    
    def stop(self, message: str = "完成"):
        """停止旋轉指示器"""
        self.running = False
        
        # 清空當前行
        try:
            curses.wrapper(lambda stdscr: stdscr.clear())
        except:
            print(f"\r{' ' * 80}\r{message}", flush=True)


class MultiStepProgress:
    """多步驟進度追蹤器"""
    
    def __init__(self, steps: list, title: str = "設置嚮導"):
        self.steps = steps
        self.title = title
        self.current_step = 0
        self.total_steps = len(steps)
        self.progress_bar = ProgressBar(title, show_time=True)
    
    def start(self):
        """開始多步驟進程"""
        print(f"\n{self.title}")
        print("=" * 60)
    
    def next_step(self, message: str = ""):
        """進入下一步"""
        if self.current_step >= self.total_steps:
            return
        
        # 更新進度
        progress = (self.current_step + 1) / self.total_steps
        step_message = f"步驟 {self.current_step + 1}/{self.total_steps}"
        if message:
            step_message += f": {message}"
        
        self.progress_bar.update(progress, step_message, force=True)
        self.current_step += 1
    
    def complete(self):
        """完成所有步驟"""
        self.progress_bar.complete("所有步驟完成！")
        print("=" * 60)


# 測試函數
def test_progress_bar():
    """測試進度條功能"""
    print("測試進度條...")
    
    # 測試基本進度條
    bar = ProgressBar("測試進度", width=40)
    
    for i in range(101):
        progress = i / 100.0
        message = f"處理項目 {i}/100"
        bar.update(progress, message)
        time.sleep(0.02)
    
    bar.complete("測試完成！")


def test_spinner():
    """測試旋轉指示器"""
    print("\n測試旋轉指示器...")
    
    spinner = Spinner("正在加載...")
    spinner.start()
    
    for _ in range(50):
        spinner.update()
        time.sleep(0.1)
    
    spinner.stop("加載完成！")


if __name__ == "__main__":
    # 運行測試
    test_progress_bar()
    test_spinner()