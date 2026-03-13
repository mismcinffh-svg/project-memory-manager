#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示 Project Memory Manager 交互式選單系統
展示方向鍵選擇、顏色和進度條功能
"""

import sys
import os
import time

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_main_menu():
    """演示主選單"""
    from interactive.menu_engine import InteractiveMenu
    
    print("正在加載交互式選單系統...")
    time.sleep(0.5)
    
    menu = InteractiveMenu(
        title="Project Memory Manager 演示",
        subtitle="請體驗方向鍵選擇界面",
        border=True,
        show_numbers=True
    )
    
    # 添加選項
    menu.add_option(
        "快速設置演示",
        "展示快速設置流程",
        lambda data: print("\n開始快速設置演示...")
    )
    
    menu.add_option(
        "進度條演示",
        "展示百分比進度條",
        lambda data: demo_progress_bar()
    )
    
    menu.add_separator()
    
    menu.add_option(
        "環境檢測",
        "檢測系統環境狀態",
        lambda data: demo_environment_check()
    )
    
    menu.add_option(
        "配置檢查",
        "查看當前配置",
        lambda data: demo_config_check()
    )
    
    menu.add_separator()
    
    menu.add_option(
        "退出演示",
        "返回命令行",
        lambda data: print("\n演示結束！")
    )
    
    print("\n" + "="*60)
    print("  按任意鍵進入交互式選單界面...")
    print("  在選單中使用方向鍵 ↑↓ 移動，回車確認")
    print("="*60)
    input()
    
    result = menu.run()
    return result


def demo_progress_bar():
    """演示進度條"""
    from interactive.progress_bar import ProgressBar, MultiStepProgress
    
    print("\n演示進度條功能...")
    
    # 基本進度條
    print("\n1. 基本進度條:")
    bar = ProgressBar("處理任務", width=40, show_percentage=True, show_time=True)
    
    for i in range(101):
        progress = i / 100.0
        message = f"處理項目 {i}/100"
        bar.update(progress, message)
        time.sleep(0.02)
    
    bar.complete("所有任務完成！")
    
    # 多步驟進度
    print("\n\n2. 多步驟進度:")
    steps = ["初始化", "加載數據", "處理文件", "生成報告", "保存結果"]
    multi = MultiStepProgress(steps, "多步驟任務")
    
    multi.start()
    for i in range(len(steps)):
        multi.next_step(f"正在{steps[i]}...")
        time.sleep(0.5)
    
    multi.complete()
    
    input("\n按回車鍵返回主選單...")


def demo_environment_check():
    """演示環境檢測"""
    from interactive.setup_wizard import EnvironmentDetector
    
    print("\n環境檢測演示:")
    print("="*60)
    
    detector = EnvironmentDetector()
    
    # 檢測 Git
    print("\n1. Git 檢測:")
    git_info = detector.detect_git()
    
    if git_info["installed"]:
        print(f"  ✓ 已安裝: {git_info['version']}")
        if git_info["user_configured"]:
            print(f"  ✓ 用戶配置: {git_info['user_name']} <{git_info['user_email']}>")
        else:
            print("  ✗ 用戶未配置")
    else:
        print("  ✗ 未安裝")
    
    # 檢測 GitHub CLI
    print("\n2. GitHub CLI 檢測:")
    if detector.detect_github_cli():
        print("  ✓ 已安裝")
    else:
        print("  ✗ 未安裝")
    
    # 檢測 Telegram
    print("\n3. Telegram Bot 檢測:")
    telegram_info = detector.detect_telegram_bot()
    if telegram_info["available"]:
        print("  ✓ 檢測到配置")
        if telegram_info["bot_token"]:
            print(f"  ✓ Token: {telegram_info['bot_token'][:10]}...")
    else:
        print("  ✗ 未檢測到配置")
    
    print("\n" + "="*60)
    input("按回車鍵返回主選單...")


def demo_config_check():
    """演示配置檢查"""
    from interactive.setup_wizard import ConfigManager
    
    print("\n配置檢查演示:")
    print("="*60)
    
    config = ConfigManager.load_config()
    
    print("\n當前配置:")
    print(f"版本: {config.get('version', '1.0.0')}")
    
    # Git 配置
    git_config = config.get('git', {})
    if git_config.get('configured'):
        user = git_config.get('user', {})
        print(f"Git: {user.get('name', '')} <{user.get('email', '')}>")
    else:
        print("Git: 未配置")
    
    # GitHub 配置
    github_config = config.get('github', {})
    if github_config.get('enabled'):
        print(f"GitHub: {github_config.get('username', '')} ({github_config.get('method', '')})")
    else:
        print("GitHub: 未配置")
    
    # 設置狀態
    setup_config = config.get('setup', {})
    if setup_config.get('completed'):
        print(f"設置狀態: 已完成 ({setup_config.get('mode', '未知模式')})")
        print(f"完成時間: {setup_config.get('timestamp', '未知')}")
    else:
        print("設置狀態: 未完成")
    
    print("\n" + "="*60)
    input("按回車鍵返回主選單...")


def main():
    """主演示函數"""
    print("Project Memory Manager 交互式選單演示")
    print("="*60)
    
    try:
        while True:
            result = demo_main_menu()
            if result is None:
                break
                
            # 如果返回 False，表示繼續循環
            if result is False:
                continue
                
    except KeyboardInterrupt:
        print("\n\n演示已中斷。")
    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n演示結束。感謝體驗！")
    print("\n實際使用:")
    print("  運行設置嚮導: python scripts/setup.py")
    print("  或: python scripts/interactive/setup_wizard.py")


if __name__ == "__main__":
    main()