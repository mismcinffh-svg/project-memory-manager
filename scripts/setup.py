#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Memory Manager 設置嚮導入口點
簡單封裝，方便用戶調用
"""

import sys
import os

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """主入口點"""
    print("正在啟動 Project Memory Manager 設置嚮導...")
    print("="*60)
    
    try:
        from interactive.setup_wizard import SetupWizard
        
        wizard = SetupWizard()
        success = wizard.run()
        
        if success:
            print("\n" + "="*60)
            print("✅ 設置嚮導完成！")
            print("="*60)
            print("\n現在你可以開始使用 Project Memory Manager:")
            print("\n基本命令:")
            print("  創建新項目: python scripts/create.py <項目名>")
            print("  查看所有項目: python scripts/list.py")
            print("  管理項目記憶: python scripts/monitor.py")
            print("\n幫助:")
            print("  重新運行設置: python scripts/setup.py")
            print("  查看版本: python scripts/version.py")
        else:
            print("\n設置已取消。")
            
    except ImportError as e:
        print(f"❌ 導入模塊失敗: {e}")
        print("請確保所有依賴文件都存在:")
        print("  scripts/interactive/menu_engine.py")
        print("  scripts/interactive/progress_bar.py")
        print("  scripts/interactive/setup_wizard.py")
        return 1
    except KeyboardInterrupt:
        print("\n\n設置已中斷。")
        return 1
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())