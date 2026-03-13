#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式選單引擎 - 支持方向鍵選擇和簡單顏色
模仿 openclaw config 的用戶體驗
"""

import sys
import os
import curses
from typing import List, Dict, Any, Optional, Callable


class MenuOption:
    """選單選項類"""
    
    def __init__(self, title: str, description: str = "", callback: Optional[Callable] = None, 
                 data: Any = None, disabled: bool = False):
        self.title = title
        self.description = description
        self.callback = callback
        self.data = data
        self.disabled = disabled
    
    def __str__(self) -> str:
        return f"MenuOption: {self.title}"


class InteractiveMenu:
    """交互式選單類 - 支持方向鍵導航"""
    
    def __init__(self, title: str = "請選擇", subtitle: str = "", 
                 border: bool = True, show_numbers: bool = True):
        self.title = title
        self.subtitle = subtitle
        self.border = border
        self.show_numbers = show_numbers
        self.options: List[MenuOption] = []
        self.selected_index = 0
        self.quit = False
        self.result = None
        
        # 顏色定義
        self.colors = {
            'normal': 1,
            'selected': 2,
            'title': 3,
            'subtitle': 4,
            'border': 5,
            'disabled': 6
        }
    
    def add_option(self, title: str, description: str = "", callback: Optional[Callable] = None,
                   data: Any = None, disabled: bool = False):
        """添加選單選項"""
        option = MenuOption(title, description, callback, data, disabled)
        self.options.append(option)
    
    def add_separator(self):
        """添加分隔線（用空選項表示）"""
        self.options.append(MenuOption("", disabled=True))
    
    def _init_colors(self):
        """初始化顏色對"""
        curses.start_color()
        curses.use_default_colors()
        
        # 定義顏色對
        # 1: 正常文本 (白色)
        curses.init_pair(1, curses.COLOR_WHITE, -1)
        # 2: 選中項 (綠色背景)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
        # 3: 標題 (青色)
        curses.init_pair(3, curses.COLOR_CYAN, -1)
        # 4: 副標題 (黃色)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
        # 5: 邊框 (藍色)
        curses.init_pair(5, curses.COLOR_BLUE, -1)
        # 6: 禁用項 (灰色)
        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_WHITE)
    
    def _draw_border(self, stdscr, height, width):
        """繪製邊框"""
        if not self.border:
            return
        
        border_color = curses.color_pair(self.colors['border'])
        
        # 繪製邊框
        stdscr.attron(border_color)
        stdscr.border(0)
        stdscr.attroff(border_color)
        
        # 繪製標題欄（如果有空間）
        if height >= 3 and width >= len(self.title) + 4:
            title_x = max(1, (width - len(self.title) - 2) // 2)
            stdscr.addstr(0, title_x, f" {self.title} ", border_color)
    
    def _draw_title(self, stdscr, start_y, start_x, width):
        """繪製標題和副標題"""
        # 繪製主標題
        title_color = curses.color_pair(self.colors['title'])
        if self.title:
            title_line = f" {self.title} "
            title_x = start_x + max(0, (width - len(title_line)) // 2)
            stdscr.addstr(start_y, title_x, title_line, title_color | curses.A_BOLD)
            start_y += 2
        
        # 繪製副標題
        if self.subtitle:
            subtitle_color = curses.color_pair(self.colors['subtitle'])
            subtitle_line = f" {self.subtitle} "
            subtitle_x = start_x + max(0, (width - len(subtitle_line)) // 2)
            stdscr.addstr(start_y, subtitle_x, subtitle_line, subtitle_color)
            start_y += 2
        
        return start_y
    
    def _draw_options(self, stdscr, start_y, start_x, width):
        """繪製選項列表"""
        max_height, max_width = stdscr.getmaxyx()
        available_height = max_height - start_y - 2
        
        # 計算可顯示的選項數量
        visible_options = min(len(self.options), available_height)
        
        for i in range(visible_options):
            option = self.options[i]
            line_y = start_y + i
            
            # 檢查是否超出屏幕
            if line_y >= max_height - 1:
                break
            
            # 準備選項文本
            prefix = ""
            if self.show_numbers and not option.disabled and option.title:
                prefix = f"{i+1}. "
            
            option_text = f"{prefix}{option.title}"
            if option.description and width > len(option_text) + 5:
                # 添加描述（如果空間足夠）
                desc_space = width - len(option_text) - 3
                if desc_space > 0:
                    desc = option.description[:desc_space]
                    option_text = f"{option_text} - {desc}"
            
            # 截斷過長文本
            if len(option_text) > width - 2:
                option_text = option_text[:width - 5] + "..."
            
            # 居中對齊
            option_x = start_x + max(0, (width - len(option_text)) // 2)
            
            # 設置顏色
            if option.disabled or not option.title:
                # 分隔線或禁用項
                color = curses.color_pair(self.colors['disabled'])
                if not option.title:
                    # 分隔線
                    separator = "─" * min(width - 2, 30)
                    separator_x = start_x + max(0, (width - len(separator)) // 2)
                    stdscr.addstr(line_y, separator_x, separator, color)
                    continue
            elif i == self.selected_index:
                # 選中項
                color = curses.color_pair(self.colors['selected'])
            else:
                # 正常項
                color = curses.color_pair(self.colors['normal'])
            
            # 繪製選項
            stdscr.addstr(line_y, option_x, option_text, color)
            
            # 如果是選中項，添加指示器
            if i == self.selected_index and not option.disabled:
                stdscr.addstr(line_y, option_x - 2, ">", color)
                stdscr.addstr(line_y, option_x + len(option_text), "<", color)
        
        # 如果選項太多，顯示滾動提示
        if len(self.options) > visible_options:
            scroll_text = f" ↑↓ 查看更多 ({self.selected_index + 1}/{len(self.options)}) "
            scroll_x = start_x + max(0, (width - len(scroll_text)) // 2)
            scroll_y = max_height - 2
            if scroll_y < max_height - 1:
                stdscr.addstr(scroll_y, scroll_x, scroll_text, 
                             curses.color_pair(self.colors['subtitle']))
    
    def _draw_footer(self, stdscr, start_y, width):
        """繪製頁腳說明"""
        max_height, max_width = stdscr.getmaxyx()
        footer_y = max_height - 1
        
        instructions = "方向鍵: 選擇 | 回車: 確認 | ESC: 返回"
        if len(instructions) < width - 2:
            footer_x = max(0, (width - len(instructions)) // 2)
            stdscr.addstr(footer_y, footer_x, instructions, 
                         curses.color_pair(self.colors['normal']) | curses.A_DIM)
    
    def _draw_menu(self, stdscr):
        """繪製完整選單"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # 計算內容區域
        content_width = min(80, width - 4)
        content_height = min(30, height - 6)
        start_x = max(0, (width - content_width) // 2)
        start_y = max(0, (height - content_height) // 2)
        
        # 繪製邊框
        self._draw_border(stdscr, height, width)
        
        # 繪製標題
        content_start_y = self._draw_title(stdscr, start_y, start_x, content_width)
        
        # 繪製選項
        self._draw_options(stdscr, content_start_y, start_x, content_width)
        
        # 繪製頁腳
        self._draw_footer(stdscr, content_start_y, content_width)
        
        stdscr.refresh()
    
    def _handle_input(self, stdscr):
        """處理用戶輸入"""
        key = stdscr.getch()
        
        if key == curses.KEY_UP:
            # 向上移動選擇
            self.selected_index = (self.selected_index - 1) % len(self.options)
            # 跳過禁用項和分隔線
            while self.options[self.selected_index].disabled or not self.options[self.selected_index].title:
                self.selected_index = (self.selected_index - 1) % len(self.options)
        
        elif key == curses.KEY_DOWN:
            # 向下移動選擇
            self.selected_index = (self.selected_index + 1) % len(self.options)
            # 跳過禁用項和分隔線
            while self.options[self.selected_index].disabled or not self.options[self.selected_index].title:
                self.selected_index = (self.selected_index + 1) % len(self.options)
        
        elif key == 10 or key == curses.KEY_ENTER:  # 回車鍵
            # 執行選中的選項
            selected_option = self.options[self.selected_index]
            if not selected_option.disabled and selected_option.callback:
                self.result = selected_option.callback(selected_option.data)
                if self.result is not False:  # False 表示不關閉選單
                    self.quit = True
        
        elif key == 27 or key == 113:  # ESC 或 'q' 鍵
            self.quit = True
            self.result = None
        
        elif key >= ord('1') and key <= ord('9'):
            # 數字鍵選擇
            index = key - ord('1')
            if 0 <= index < len(self.options) and not self.options[index].disabled:
                self.selected_index = index
                # 直接執行（模擬回車）
                selected_option = self.options[self.selected_index]
                if selected_option.callback:
                    self.result = selected_option.callback(selected_option.data)
                    if self.result is not False:
                        self.quit = True
    
    def run(self) -> Any:
        """運行選單並返回結果"""
        def _run(stdscr):
            # 初始化
            curses.curs_set(0)  # 隱藏光標
            stdscr.keypad(True)  # 啟用功能鍵
            stdscr.timeout(-1)  # 阻塞模式
            
            self._init_colors()
            
            # 確保至少有一個可選選項
            if not any(not opt.disabled and opt.title for opt in self.options):
                return None
            
            # 設置初始選擇（第一個可選項）
            for i, opt in enumerate(self.options):
                if not opt.disabled and opt.title:
                    self.selected_index = i
                    break
            
            # 主循環
            self.quit = False
            while not self.quit:
                self._draw_menu(stdscr)
                self._handle_input(stdscr)
            
            return self.result
        
        # 運行 curses 應用
        try:
            return curses.wrapper(_run)
        except KeyboardInterrupt:
            return None
        except Exception as e:
            # 如果 curses 失敗，回退到簡單文本模式
            print(f"警告: curses 模式失敗: {e}")
            print("切換到簡單文本模式...")
            return self._fallback_text_mode()
    
    def _fallback_text_mode(self) -> Any:
        """回退到文本模式"""
        text_menu = TextMenu(self.title, self.subtitle, self.show_numbers)
        for option in self.options:
            text_menu.add_option(option.title, option.description, 
                                option.callback, option.data, option.disabled)
        return text_menu.run()


class TextMenu:
    """簡單文本選單（備用方案）"""
    
    def __init__(self, title: str = "請選擇", subtitle: str = "", show_numbers: bool = True):
        self.title = title
        self.subtitle = subtitle
        self.show_numbers = show_numbers
        self.options: List[MenuOption] = []
    
    def add_option(self, title: str, description: str = "", callback: Optional[Callable] = None,
                   data: Any = None, disabled: bool = False):
        option = MenuOption(title, description, callback, data, disabled)
        self.options.append(option)
    
    def run(self) -> Any:
        """運行文本選單"""
        print(f"\n{'='*60}")
        print(f"  {self.title}")
        if self.subtitle:
            print(f"  {self.subtitle}")
        print(f"{'='*60}")
        
        # 顯示可用選項
        valid_options = []
        for i, option in enumerate(self.options):
            if option.disabled:
                continue
            
            prefix = f"{i+1}. " if self.show_numbers else ""
            line = f"  {prefix}{option.title}"
            if option.description:
                line += f" - {option.description}"
            
            print(line)
            valid_options.append(option)
        
        print(f"{'='*60}")
        print("輸入數字選擇，或按 'q' 退出")
        
        while True:
            try:
                choice = input("選擇: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                if choice.isdigit():
                    index = int(choice) - 1
                    if 0 <= index < len(valid_options):
                        option = valid_options[index]
                        if option.callback:
                            return option.callback(option.data)
                
                print("無效選擇，請重試。")
                
            except (KeyboardInterrupt, EOFError):
                print()
                return None