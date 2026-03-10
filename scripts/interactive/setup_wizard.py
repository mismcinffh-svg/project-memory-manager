#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Memory Manager 設置嚮導
模仿 openclaw config 的交互體驗
支持方向鍵選擇 + 進度條顯示
"""

import sys
import os
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from menu_engine import InteractiveMenu, TextMenu
from progress_bar import ProgressBar, MultiStepProgress, Spinner


class ConfigManager:
    """配置管理器"""
    
    CONFIG_DIR = Path.home() / ".openclaw"
    CONFIG_FILE = CONFIG_DIR / "project-memory-config.json"
    
    DEFAULT_CONFIG = {
        "version": "1.0.0",
        "setup": {
            "completed": False,
            "mode": "quick",
            "timestamp": None
        },
        "git": {
            "configured": False,
            "user": {
                "name": "",
                "email": ""
            },
            "auto_commit": True,
            "auto_push": True
        },
        "github": {
            "enabled": False,
            "method": None,  # "cli" or "pat"
            "username": "",
            "token": "",
            "default_visibility": "public"
        },
        "notifications": {
            "telegram": False,
            "chat_id": "",
            "email": False,
            "desktop": True
        },
        "templates": {
            "preferred": "ai-research",
            "custom_templates": []
        },
        "sync": {
            "platforms": [],
            "auto_sync": True,
            "interval_minutes": 60
        }
    }
    
    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """加載配置"""
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合併默認配置（確保新字段存在）
                cls._merge_configs(cls.DEFAULT_CONFIG, config)
                return config
            except Exception as e:
                print(f"配置加載失敗: {e}")
        
        return cls.DEFAULT_CONFIG.copy()
    
    @classmethod
    def save_config(cls, config: Dict[str, Any]):
        """保存配置"""
        try:
            cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"配置保存失敗: {e}")
            return False
    
    @staticmethod
    def _merge_configs(default: Dict, custom: Dict):
        """遞歸合併配置"""
        for key, value in default.items():
            if key not in custom:
                custom[key] = value
            elif isinstance(value, dict) and isinstance(custom[key], dict):
                ConfigManager._merge_configs(value, custom[key])


class EnvironmentDetector:
    """環境檢測器"""
    
    @staticmethod
    def detect_git() -> Dict[str, Any]:
        """檢測 Git 安裝和配置"""
        result = {
            "installed": False,
            "version": "",
            "user_configured": False,
            "user_name": "",
            "user_email": ""
        }
        
        try:
            # 檢測 Git 安裝
            git_version = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            result["installed"] = True
            result["version"] = git_version.stdout.strip()
            
            # 檢測用戶配置
            try:
                user_name = subprocess.run(
                    ["git", "config", "user.name"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                result["user_name"] = user_name.stdout.strip()
                
                user_email = subprocess.run(
                    ["git", "config", "user.email"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                result["user_email"] = user_email.stdout.strip()
                
                if result["user_name"] and result["user_email"]:
                    result["user_configured"] = True
            except:
                pass
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        return result
    
    @staticmethod
    def detect_github_cli() -> bool:
        """檢測 GitHub CLI 安裝"""
        try:
            subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    @staticmethod
    def detect_telegram_bot() -> Dict[str, Any]:
        """檢測 Telegram Bot 配置"""
        result = {
            "available": False,
            "bot_token": "",
            "chat_id": ""
        }
        
        # 嘗試從 OpenClaw 配置讀取
        openclaw_config = Path.home() / ".openclaw" / "openclaw.json"
        if openclaw_config.exists():
            try:
                with open(openclaw_config, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 查找 Telegram 配置
                if "telegram" in config.get("channels", {}):
                    telegram_config = config["channels"]["telegram"]
                    for account in telegram_config.get("accounts", []):
                        if "token" in account:
                            result["bot_token"] = account["token"]
                            result["available"] = True
                            break
            except:
                pass
        
        return result


class SetupWizard:
    """設置嚮導主類"""
    
    def __init__(self):
        self.config = ConfigManager.load_config()
        self.env = EnvironmentDetector()
        self.progress = None
        
    def run(self):
        """運行設置嚮導"""
        try:
            return self._run_with_curses()
        except Exception as e:
            print(f"curses 模式失敗: {e}")
            return self._run_text_mode()
    
    def _run_with_curses(self):
        """使用 curses 運行嚮導"""
        import curses
        
        def main(stdscr):
            curses.curs_set(0)
            stdscr.keypad(True)
            
            # 顯示歡迎界面
            self._show_welcome(stdscr)
            
            # 主選單
            choice = self._show_main_menu(stdscr)
            
            if choice == "quick":
                self._run_quick_setup(stdscr)
            elif choice == "advanced":
                self._run_advanced_setup(stdscr)
            elif choice == "check":
                self._show_config_check(stdscr)
            elif choice == "repair":
                self._run_repair(stdscr)
            
            # 顯示完成界面
            self._show_completion(stdscr)
            
            return True
        
        return curses.wrapper(main)
    
    def _run_text_mode(self):
        """文本模式運行嚮導"""
        print("\n" + "="*60)
        print("  Project Memory Manager 設置嚮導")
        print("="*60)
        
        print("\n檢測環境...")
        git_info = self.env.detect_git()
        
        if git_info["installed"]:
            print(f"✓ Git {git_info['version']}")
            if git_info["user_configured"]:
                print(f"✓ Git 用戶: {git_info['user_name']} <{git_info['user_email']}>")
            else:
                print("✗ Git 用戶未配置")
        else:
            print("✗ Git 未安裝")
        
        print("\n請選擇設置模式:")
        print("  1. 快速設置（推薦）")
        print("  2. 高級設置")
        print("  3. 檢查當前配置")
        print("  4. 修復問題")
        print("  5. 退出")
        
        while True:
            choice = input("\n選擇 [1-5]: ").strip()
            
            if choice == "1":
                self._text_quick_setup()
                break
            elif choice == "2":
                self._text_advanced_setup()
                break
            elif choice == "3":
                self._text_config_check()
                break
            elif choice == "4":
                self._text_repair()
                break
            elif choice == "5":
                return False
            else:
                print("無效選擇，請重試。")
        
        print("\n設置完成！")
        return True
    
    def _show_welcome(self, stdscr):
        """顯示歡迎界面"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # 顯示標題
        title = " Project Memory Manager 設置嚮導 "
        title_x = max(0, (width - len(title)) // 2)
        title_y = max(0, (height - 10) // 2)
        
        stdscr.addstr(title_y, title_x, title, curses.A_BOLD)
        
        # 顯示版本
        version = f"版本: {self.config.get('version', '1.0.0')}"
        version_x = max(0, (width - len(version)) // 2)
        stdscr.addstr(title_y + 2, version_x, version)
        
        # 顯示提示
        prompt = "按任意鍵繼續..."
        prompt_x = max(0, (width - len(prompt)) // 2)
        stdscr.addstr(title_y + 6, prompt_x, prompt)
        
        stdscr.refresh()
        stdscr.getch()
    
    def _show_main_menu(self, stdscr):
        """顯示主選單"""
        menu = InteractiveMenu(
            title="設置模式選擇",
            subtitle="請選擇適合你的設置方式",
            border=True,
            show_numbers=True
        )
        
        menu.add_option(
            "快速設置（推薦）",
            "自動檢測並配置最常用選項",
            lambda data: "quick"
        )
        
        menu.add_option(
            "高級設置",
            "自定義每個配置選項",
            lambda data: "advanced"
        )
        
        menu.add_separator()
        
        menu.add_option(
            "檢查當前配置",
            "查看和驗證現有配置",
            lambda data: "check"
        )
        
        menu.add_option(
            "修復問題",
            "診斷和修復常見問題",
            lambda data: "repair"
        )
        
        menu.add_separator()
        
        menu.add_option(
            "退出設置",
            "稍後再配置",
            lambda data: "exit"
        )
        
        result = menu.run()
        return result if result else "exit"
    
    def _run_quick_setup(self, stdscr):
        """運行快速設置"""
        # 初始化多步驟進度
        steps = [
            "檢測環境",
            "配置 Git",
            "設置 GitHub",
            "配置通知",
            "保存設置"
        ]
        
        self.progress = MultiStepProgress(steps, "快速設置")
        self.progress.start()
        
        # 步驟1: 檢測環境
        self.progress.next_step("檢測環境")
        git_info = self.env.detect_git()
        github_cli = self.env.detect_github_cli()
        telegram_info = self.env.detect_telegram_bot()
        
        time.sleep(0.5)
        
        # 步驟2: 配置 Git
        self.progress.next_step("配置 Git")
        if not git_info["user_configured"]:
            # 需要配置 Git 用戶
            self._configure_git_user(stdscr)
        else:
            self.config["git"]["configured"] = True
            self.config["git"]["user"]["name"] = git_info["user_name"]
            self.config["git"]["user"]["email"] = git_info["user_email"]
        
        time.sleep(0.5)
        
        # 步驟3: 設置 GitHub
        self.progress.next_step("設置 GitHub")
        if github_cli:
            # 使用 GitHub CLI
            self._setup_github_with_cli(stdscr)
        else:
            # 提供其他選項
            self._setup_github_options(stdscr)
        
        time.sleep(0.5)
        
        # 步驟4: 配置通知
        self.progress.next_step("配置通知")
        if telegram_info["available"]:
            self.config["notifications"]["telegram"] = True
            self.config["notifications"]["chat_id"] = telegram_info.get("chat_id", "")
        
        time.sleep(0.5)
        
        # 步驟5: 保存設置
        self.progress.next_step("保存設置")
        self.config["setup"]["completed"] = True
        self.config["setup"]["mode"] = "quick"
        self.config["setup"]["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        ConfigManager.save_config(self.config)
        time.sleep(0.5)
        
        self.progress.complete()
    
    def _run_advanced_setup(self, stdscr):
        """運行高級設置"""
        # 待實現
        pass
    
    def _show_config_check(self, stdscr):
        """顯示配置檢查"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        title = " 配置檢查 "
        title_x = max(0, (width - len(title)) // 2)
        
        stdscr.addstr(2, title_x, title, curses.A_BOLD)
        
        # 顯示配置狀態
        row = 4
        
        # Git 配置
        git_status = "✓" if self.config["git"]["configured"] else "✗"
        git_text = f"{git_status} Git 配置"
        stdscr.addstr(row, 10, git_text)
        
        if self.config["git"]["configured"]:
            user = self.config["git"]["user"]
            user_text = f"    用戶: {user['name']} <{user['email']}>"
            stdscr.addstr(row + 1, 10, user_text)
            row += 2
        else:
            row += 1
        
        # GitHub 配置
        github_status = "✓" if self.config["github"]["enabled"] else "✗"
        github_text = f"{github_status} GitHub 集成"
        stdscr.addstr(row, 10, github_text)
        
        if self.config["github"]["enabled"]:
            method = self.config["github"]["method"]
            username = self.config["github"]["username"]
            github_detail = f"    方法: {method}, 用戶: {username}"
            stdscr.addstr(row + 1, 10, github_detail)
            row += 2
        else:
            row += 1
        
        # 通知配置
        notifications = self.config["notifications"]
        notify_status = "✓" if any([notifications["telegram"], notifications["email"]]) else "✗"
        notify_text = f"{notify_status} 通知設置"
        stdscr.addstr(row, 10, notify_text)
        
        row += 2
        
        # 提示
        prompt = "按任意鍵返回..."
        prompt_x = max(0, (width - len(prompt)) // 2)
        stdscr.addstr(height - 2, prompt_x, prompt)
        
        stdscr.refresh()
        stdscr.getch()
    
    def _run_repair(self, stdscr):
        """運行修復"""
        # 待實現
        pass
    
    def _configure_git_user(self, stdscr):
        """配置 Git 用戶"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        title = " Git 用戶配置 "
        title_x = max(0, (width - len(title)) // 2)
        
        stdscr.addstr(2, title_x, title, curses.A_BOLD)
        stdscr.addstr(4, 10, "請輸入你的 Git 用戶信息:")
        
        # 獲取用戶名
        stdscr.addstr(6, 10, "用戶名: ")
        curses.echo()
        name = self._get_input(stdscr, 6, 18, 30)
        curses.noecho()
        
        # 獲取郵箱
        stdscr.addstr(8, 10, "郵箱: ")
        curses.echo()
        email = self._get_input(stdscr, 8, 16, 40)
        curses.noecho()
        
        # 配置 Git
        try:
            subprocess.run(["git", "config", "--global", "user.name", name], check=True)
            subprocess.run(["git", "config", "--global", "user.email", email], check=True)
            
            self.config["git"]["configured"] = True
            self.config["git"]["user"]["name"] = name
            self.config["git"]["user"]["email"] = email
            
            stdscr.addstr(10, 10, "✓ Git 用戶配置成功", curses.COLOR_GREEN)
        except Exception as e:
            stdscr.addstr(10, 10, f"✗ Git 配置失敗: {e}", curses.COLOR_RED)
        
        stdscr.addstr(12, 10, "按任意鍵繼續...")
        stdscr.refresh()
        stdscr.getch()
    
    def _setup_github_with_cli(self, stdscr):
        """使用 GitHub CLI 設置"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        title = " GitHub 集成 "
        title_x = max(0, (width - len(title)) // 2)
        
        stdscr.addstr(2, title_x, title, curses.A_BOLD)
        stdscr.addstr(4, 10, "正在使用 GitHub CLI 進行認證...")
        
        try:
            # 嘗試執行 gh auth login
            result = subprocess.run(
                ["gh", "auth", "login", "--hostname", "github.com", "--web"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # 獲取用戶名
                user_result = subprocess.run(
                    ["gh", "api", "user", "--jq", ".login"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                username = user_result.stdout.strip()
                
                self.config["github"]["enabled"] = True
                self.config["github"]["method"] = "cli"
                self.config["github"]["username"] = username
                
                stdscr.addstr(6, 10, f"✓ GitHub 登錄成功: {username}", curses.COLOR_GREEN)
            else:
                stdscr.addstr(6, 10, "✗ GitHub 登錄失敗", curses.COLOR_RED)
                
        except subprocess.TimeoutExpired:
            stdscr.addstr(6, 10, "✗ 登錄超時", curses.COLOR_RED)
        except Exception as e:
            stdscr.addstr(6, 10, f"✗ 錯誤: {e}", curses.COLOR_RED)
        
        stdscr.addstr(8, 10, "按任意鍵繼續...")
        stdscr.refresh()
        stdscr.getch()
    
    def _setup_github_options(self, stdscr):
        """顯示 GitHub 設置選項"""
        menu = InteractiveMenu(
            title="GitHub 集成選項",
            subtitle="檢測到未安裝 GitHub CLI",
            border=True
        )
        
        menu.add_option(
            "安裝 GitHub CLI 並登錄",
            "推薦方式，最安全",
            lambda data: self._install_github_cli(stdscr)
        )
        
        menu.add_option(
            "使用 Personal Access Token",
            "手動創建並輸入 Token",
            lambda data: self._setup_github_with_pat(stdscr)
        )
        
        menu.add_option(
            "跳過 GitHub 設置",
            "稍後再配置",
            lambda data: None
        )
        
        menu.run()
    
    def _show_completion(self, stdscr):
        """顯示完成界面"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        title = " 設置完成！ "
        title_x = max(0, (width - len(title)) // 2)
        
        stdscr.addstr(2, title_x, title, curses.A_BOLD | curses.COLOR_GREEN)
        
        # 顯示摘要
        row = 4
        
        if self.config["git"]["configured"]:
            stdscr.addstr(row, 10, "✓ Git 配置完成", curses.COLOR_GREEN)
            row += 1
        
        if self.config["github"]["enabled"]:
            stdscr.addstr(row, 10, f"✓ GitHub 集成: {self.config['github']['username']}", curses.COLOR_GREEN)
            row += 1
        
        if self.config["notifications"]["telegram"]:
            stdscr.addstr(row, 10, "✓ Telegram 通知已啟用", curses.COLOR_GREEN)
            row += 1
        
        row += 2
        
        # 提示
        tips = [
            "使用提示:",
            "• 創建項目: pm create <項目名>",
            "• 查看項目: pm list",
            "• 獲取幫助: pm --help"
        ]
        
        for tip in tips:
            stdscr.addstr(row, 10, tip)
            row += 1
        
        row += 1
        stdscr.addstr(row, 10, "按任意鍵開始使用...")
        
        stdscr.refresh()
        stdscr.getch()
    
    def _get_input(self, stdscr, y, x, max_len):
        """獲取用戶輸入"""
        input_str = ""
        cursor_pos = 0
        
        while True:
            # 顯示當前輸入
            display = input_str[:max_len]
            stdscr.addstr(y, x, " " * max_len)
            stdscr.addstr(y, x, display)
            stdscr.move(y, x + cursor_pos)
            
            key = stdscr.getch()
            
            if key == 10 or key == curses.KEY_ENTER:  # 回車
                break
            elif key == 27:  # ESC
                return None
            elif key == curses.KEY_BACKSPACE or key == 127:
                if cursor_pos > 0:
                    input_str = input_str[:cursor_pos-1] + input_str[cursor_pos:]
                    cursor_pos -= 1
            elif key == curses.KEY_LEFT:
                cursor_pos = max(0, cursor_pos - 1)
            elif key == curses.KEY_RIGHT:
                cursor_pos = min(len(input_str), cursor_pos + 1)
            elif 32 <= key <= 126:  # 可打印字符
                if len(input_str) < max_len:
                    input_str = input_str[:cursor_pos] + chr(key) + input_str[cursor_pos:]
                    cursor_pos += 1
        
        return input_str
    
    # 文本模式方法（備用）
    def _text_quick_setup(self):
        """文本模式快速設置"""
        print("\n開始快速設置...")
        
        # 檢測環境
        print("\n1. 檢測環境...")
        git_info = self.env.detect_git()
        
        if git_info["installed"]:
            print(f"  ✓ Git {git_info['version']}")
            if not git_info["user_configured"]:
                print("  ✗ Git 用戶未配置")
                name = input("  請輸入用戶名: ").strip()
                email = input("  請輸入郵箱: ").strip()
                
                try:
                    subprocess.run(["git", "config", "--global", "user.name", name], check=True)
                    subprocess.run(["git", "config", "--global", "user.email", email], check=True)
                    print("  ✓ Git 用戶配置成功")
                    
                    self.config["git"]["configured"] = True
                    self.config["git"]["user"]["name"] = name
                    self.config["git"]["user"]["email"] = email
                except Exception as e:
                    print(f"  ✗ Git 配置失敗: {e}")
            else:
                print(f"  ✓ Git 用戶: {git_info['user_name']} <{git_info['user_email']}>")
                self.config["git"]["configured"] = True
                self.config["git"]["user"]["name"] = git_info["user_name"]
                self.config["git"]["user"]["email"] = git_info["user_email"]
        else:
            print("  ✗ Git 未安裝")
        
        # GitHub 設置
        print("\n2. GitHub 設置...")
        github_cli = self.env.detect_github_cli()
        
        if github_cli:
            print("  ✓ 檢測到 GitHub CLI")
            choice = input("  是否使用 GitHub CLI 登錄？[Y/n]: ").strip().lower()
            
            if choice in ['', 'y', 'yes']:
                print("  正在打開瀏覽器進行認證...")
                try:
                    subprocess.run(["gh", "auth", "login", "--hostname", "github.com", "--web"], 
                                  check=True, timeout=30)
                    
                    # 獲取用戶名
                    result = subprocess.run(["gh", "api", "user", "--jq", ".login"],
                                           capture_output=True, text=True, check=True)
                    username = result.stdout.strip()
                    
                    print(f"  ✓ GitHub 登錄成功: {username}")
                    self.config["github"]["enabled"] = True
                    self.config["github"]["method"] = "cli"
                    self.config["github"]["username"] = username
                except Exception as e:
                    print(f"  ✗ GitHub 登錄失敗: {e}")
        else:
            print("  ✗ 未檢測到 GitHub CLI")
            print("  請選擇:")
            print("  1. 安裝 GitHub CLI")
            print("  2. 使用 Personal Access Token")
            print("  3. 跳過 GitHub 設置")
            
            choice = input("  選擇 [1-3]: ").strip()
            
            if choice == "1":
                print("  請手動安裝 GitHub CLI: https://cli.github.com/")
            elif choice == "2":
                token = input("  請輸入 Personal Access Token: ").strip()
                username = input("  請輸入 GitHub 用戶名: ").strip()
                
                if token and username:
                    self.config["github"]["enabled"] = True
                    self.config["github"]["method"] = "pat"
                    self.config["github"]["token"] = token
                    self.config["github"]["username"] = username
                    print("  ✓ GitHub Token 配置成功")
        
        # 通知設置
        print("\n3. 通知設置...")
        telegram_info = self.env.detect_telegram_bot()
        
        if telegram_info["available"]:
            print("  ✓ 檢測到 Telegram Bot 配置")
            choice = input("  是否啟用 Telegram 通知？[Y/n]: ").strip().lower()
            
            if choice in ['', 'y', 'yes']:
                self.config["notifications"]["telegram"] = True
                print("  ✓ Telegram 通知已啟用")
        else:
            print("  ✗ 未檢測到 Telegram Bot 配置")
        
        # 保存配置
        print("\n4. 保存配置...")
        self.config["setup"]["completed"] = True
        self.config["setup"]["mode"] = "quick"
        self.config["setup"]["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        if ConfigManager.save_config(self.config):
            print("  ✓ 配置保存成功")
        else:
            print("  ✗ 配置保存失敗")
    
    def _text_advanced_setup(self):
        """文本模式高級設置"""
        print("\n高級設置模式")
        print("="*60)
        
        # 待實現
        print("\n此功能正在開發中...")
        print("請使用快速設置模式。")
        
        input("\n按回車鍵返回...")
    
    def _text_config_check(self):
        """文本模式配置檢查"""
        print("\n配置檢查")
        print("="*60)
        
        print("\n當前配置狀態:")
        
        # Git 配置
        if self.config["git"]["configured"]:
            user = self.config["git"]["user"]
            print(f"✓ Git: {user['name']} <{user['email']}>")
        else:
            print("✗ Git: 未配置")
        
        # GitHub 配置
        if self.config["github"]["enabled"]:
            method = self.config["github"]["method"]
            username = self.config["github"]["username"]
            print(f"✓ GitHub: {username} ({method})")
        else:
            print("✗ GitHub: 未配置")
        
        # 通知配置
        notifications = self.config["notifications"]
        notify_status = []
        if notifications["telegram"]:
            notify_status.append("Telegram")
        if notifications["email"]:
            notify_status.append("Email")
        if notifications["desktop"]:
            notify_status.append("桌面")
        
        if notify_status:
            print(f"✓ 通知: {', '.join(notify_status)}")
        else:
            print("✗ 通知: 未配置")
        
        print(f"\n設置模式: {self.config['setup'].get('mode', '未設置')}")
        if self.config["setup"].get("completed"):
            print(f"完成時間: {self.config['setup'].get('timestamp', '未知')}")
        
        input("\n按回車鍵返回...")
    
    def _text_repair(self):
        """文本模式修復"""
        print("\n問題修復")
        print("="*60)
        
        print("\n1. 檢測常見問題...")
        
        # 檢測 Git
        git_info = self.env.detect_git()
        if not git_info["installed"]:
            print("✗ 問題: Git 未安裝")
            print("  解決方案: 請安裝 Git https://git-scm.com/")
        elif not git_info["user_configured"]:
            print("✗ 問題: Git 用戶未配置")
            print("  解決方案: 運行 'git config --global user.name \"你的名字\"'")
            print("           運行 'git config --global user.email \"你的郵箱\"'")
        else:
            print("✓ Git 配置正常")
        
        # 檢測配置文件
        config_file = ConfigManager.CONFIG_FILE
        if config_file.exists():
            print(f"✓ 配置文件: {config_file}")
        else:
            print("✗ 問題: 配置文件不存在")
            print("  解決方案: 運行快速設置創建配置")
        
        print("\n2. 修復選項:")
        print("  1. 重新運行快速設置")
        print("  2. 重置為默認配置")
        print("  3. 檢查文件權限")
        print("  4. 返回")
        
        choice = input("\n選擇 [1-4]: ").strip()
        
        if choice == "1":
            self._text_quick_setup()
        elif choice == "2":
            confirm = input("確認重置所有配置？[y/N]: ").strip().lower()
            if confirm == 'y':
                self.config = ConfigManager.DEFAULT_CONFIG.copy()
                ConfigManager.save_config(self.config)
                print("✓ 配置已重置")
        elif choice == "3":
            print("\n檢查文件權限...")
            if config_file.exists():
                import stat
                st = os.stat(config_file)
                print(f"  配置文件: {oct(st.st_mode)[-3:]}")
            print("  通常應為 644 (rw-r--r--)")
        
        input("\n按回車鍵返回...")


# 命令行入口
def main():
    """主函數"""
    try:
        wizard = SetupWizard()
        success = wizard.run()
        
        if success:
            print("\n✅ 設置嚮導完成！")
            print("現在可以使用 Project Memory Manager 了。")
            print("\n常用命令:")
            print("  python scripts/setup_wizard.py  # 重新運行設置")
            print("  python scripts/create.py        # 創建新項目")
            return 0
        else:
            print("\n設置已取消。")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n設置已中斷。")
        return 1
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())