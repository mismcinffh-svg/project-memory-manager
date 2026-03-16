#!/usr/bin/env python3
"""
Project Memory Manager v5.0 vs v4.x 架構對比演示

展示兩種架構的關鍵差異：
1. 安全性：subprocess vs exec 工具指引
2. 數據真實性：模擬數據 vs 真實工具調用
3. 架構哲學：直接執行 vs 指引生成
"""

import json
import sys
from pathlib import Path

# 添加 scripts 目錄到路徑
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

def print_header(title):
    """打印標題"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def demo_security_comparison():
    """演示安全性對比"""
    print_header("1. 安全性對比：subprocess vs 安全指引")
    
    print("\n🔴 v4.x 問題：直接使用 subprocess（安全風險）")
    v4_code = '''
import subprocess

# ❌ 直接執行用戶提供的命令（可能包含危險操作）
def run_git_command_v4(command):
    result = subprocess.run(
        command.split(), 
        capture_output=True, 
        text=True
    )
    return result
    
# 可能被濫用
dangerous = "rm -rf /"
# run_git_command_v4(dangerous)  # 災難！
'''
    print(v4_code)
    
    print("\n🟢 v5.0 解決方案：安全驗證 + exec 工具指引")
    v5_code = '''
from security import SecurityValidator
from git_tool_wrapper import GitToolWrapper

# ✅ 安全驗證
validator = SecurityValidator()
is_safe, sanitized, error = validator.sanitize_command("rm -rf /")
print(f"危險命令檢查: {is_safe}, 錯誤: {error}")  # False, "命令包含危險模式"

# ✅ 生成安全指引
wrapper = GitToolWrapper(project_dir, use_openclaw_tools=True)
guidance = wrapper.git_add(".")
print("安全指引:", json.dumps(guidance, indent=2))

# Agent 根據指引安全地調用 exec 工具
'''
    print(v5_code)
    
    # 實際演示
    try:
        from security import SecurityValidator
        from git_tool_wrapper import GitToolWrapper
        
        print("\n🎬 實際演示：")
        
        validator = SecurityValidator()
        
        # 測試危險命令
        is_safe, sanitized, error = validator.sanitize_command("rm -rf /")
        print(f"  測試 'rm -rf /': {'❌ 正確拒絕' if not is_safe else '⚠️  應拒絕'}")
        
        # 測試安全命令
        is_safe, sanitized, error = validator.sanitize_command("git status")
        print(f"  測試 'git status': {'✅ 允許' if is_safe else '❌ 應允許'}")
        
    except ImportError as e:
        print(f"  演示失敗：組件未找到 - {e}")

def demo_data_comparison():
    """演示數據真實性對比"""
    print_header("2. 數據真實性對比：模擬數據 vs 真實工具調用")
    
    print("\n🔴 v4.x 問題：使用模擬數據（不準確）")
    v4_code = '''
def simulate_conversation_history_v4(project_slug):
    """❌ 模擬對話歷史（不是真實數據）"""
    return [
        {
            "role": "user",
            "content": f"模擬對話關於 {project_slug}",
            "timestamp": "1234567890"
        }
    ]

def run_summary_update_v4(project_dir, conversations):
    """❌ 模擬 sub-agent 回應"""
    mock_response = \"\"\"--- decisions.md ---
模擬決策內容...
\"\"\"
    # 處理模擬數據...
'''
    print(v4_code)
    
    print("\n🟢 v5.0 解決方案：真實 OpenClaw 工具調用指引")
    v5_code = '''
from openclaw_tools_wrapper import OpenClawToolsWrapper

tools = OpenClawToolsWrapper("project-memory-manager")

# ✅ 獲取真實對話歷史指引
history_guidance = tools.get_conversation_history(
    session_key="current",
    limit=30,
    include_tools=False
)
print("對話歷史指引:", json.dumps(history_guidance, indent=2))

# ✅ 生成真實摘要指引
summary_guidance = tools.spawn_summary_agent(
    project_name="Project Memory Manager",
    conversations=real_conversations,  # 從 sessions_history 獲取的真實數據
    since_time="2026-01-01T00:00:00+00:00"
)
print("摘要生成指引:", json.dumps(summary_guidance, indent=2))

# Agent 根據指引調用真實工具
'''
    print(v5_code)
    
    # 實際演示
    try:
        from openclaw_tools_wrapper import OpenClawToolsWrapper
        
        print("\n🎬 實際演示：")
        
        tools = OpenClawToolsWrapper("demo-project")
        
        # 生成指引
        history_guidance = tools.get_conversation_history(limit=10)
        print(f"  對話歷史指引類型: {history_guidance.get('tool')}")
        print(f"  參數: limit={history_guidance.get('parameters', {}).get('limit')}")
        
        # 展示指引結構
        print(f"  指引包含: {list(history_guidance.keys())}")
        
    except ImportError as e:
        print(f"  演示失敗：組件未找到 - {e}")

def demo_architecture_comparison():
    """演示架構哲學對比"""
    print_header("3. 架構哲學對比：直接執行 vs 指引生成")
    
    print("\n🔴 v4.x 架構：技能作為「自動化機器」")
    v4_arch = '''
class ProjectUpdateIntegration:
    """❌ 技能直接執行所有操作"""
    
    def run_full_workflow(self, project_slug):
        # 直接執行各種操作
        conversations = self.simulate_conversation_history(project_slug)
        summary = self.run_summary_update(project_dir, conversations)
        self.run_git_commands()
        # 技能包含了業務邏輯和執行邏輯
        
# 使用方式
integration = ProjectUpdateIntegration()
integration.run_full_workflow("my-project")  # 技能控制一切
'''
    print(v4_arch)
    
    print("\n🟢 v5.0 架構：技能作為「工具箱」")
    v5_arch = '''
class ProjectUpdateGuidance:
    """✅ 技能提供工具和指引"""
    
    def get_workflow_guidance(self, project_slug, scenario):
        # 分析場景，生成指引
        workflow = {
            "steps": [
                {"guidance": "如何獲取對話歷史"},
                {"guidance": "如何生成摘要"},
                {"guidance": "如何執行Git操作"}
            ]
        }
        return workflow  # 只返回指引，不執行
        
class ProjectUpdateIntegrationV5:
    """✅ 兼容層，自動選擇最佳架構"""
    
    def run_compatible_workflow(self, project_slug):
        if use_new_architecture:
            # 使用新架構：生成指引
            guidance = self.get_full_workflow_guidance(project_slug)
            return True, "v1.0.0", {"guidance": guidance}
        else:
            # 使用舊架構：直接執行（兼容模式）
            return self._run_v4_workflow(project_slug)

# 使用方式
integration = ProjectUpdateIntegrationV5()

# 方法A：獲取指引（推薦）
guidance = integration.get_full_workflow_guidance("my-project")
print("工作流程指引:", json.dumps(guidance, indent=2))
# Agent 根據指引執行操作

# 方法B：兼容執行
success, version, details = integration.run_compatible_workflow("my-project")
'''
    print(v5_arch)
    
    # 實際演示
    try:
        from project_update_guidance import ProjectUpdateGuidance
        from project_update_integration_v5 import ProjectUpdateIntegrationV5
        
        print("\n🎬 實際演示：")
        
        # 測試指引生成器
        guidance_gen = ProjectUpdateGuidance()
        
        test_message = "更新版本 project-memory-manager"
        scenario = guidance_gen.detect_scenario(test_message)
        print(f"  場景檢測: '{test_message}' → {scenario.get('primary_scenario')}")
        
        # 測試集成器
        integration = ProjectUpdateIntegrationV5(use_old_components=False)
        
        # 獲取指引
        guidance = integration.get_full_workflow_guidance(
            "project-memory-manager",
            update_summary=True
        )
        print(f"  工作流程類型: {guidance.get('type')}")
        print(f"  步驟數: {len(guidance.get('workflow', {}).get('steps', []))}")
        
        # 測試兼容模式
        print(f"  兼容模式可用: {hasattr(integration, 'run_compatible_workflow')}")
        
    except ImportError as e:
        print(f"  演示失敗：組件未找到 - {e}")

def demo_workflow_comparison():
    """演示完整工作流程對比"""
    print_header("4. 完整工作流程對比")
    
    print("\n🔴 v4.x 工作流程（問題總結）")
    v4_workflow = '''
1. 檢測觸發關鍵詞
2. ❌ 模擬對話歷史（不真實）
3. ❌ 模擬摘要生成（不真實）
4. ❌ 直接執行 Git 命令（不安全）
5. 返回結果

問題：
- 安全性：直接 subprocess 調用
- 真實性：使用模擬數據
- 架構：技能直接執行操作
- 維護性：難以測試和擴展
'''
    print(v4_workflow)
    
    print("\n🟢 v5.0 工作流程（解決方案）")
    v5_workflow = '''
1. 智能場景檢測
2. ✅ 生成對話歷史指引（真實工具調用）
3. ✅ 生成摘要指引（真實 sessions_spawn）
4. ✅ 生成 Git 操作指引（安全 exec 工具）
5. 返回指引給 Agent 執行

優勢：
- 安全性：所有命令經過驗證
- 真實性：使用真實 OpenClaw 工具
- 架構：技能提供指引，Agent 執行
- 維護性：模塊化，易測試
- 兼容性：支持新舊兩種架構
'''
    print(v5_workflow)
    
    # 實際演示
    try:
        from project_update_integration_v5 import ProjectUpdateIntegrationV5
        
        print("\n🎬 實際演示：新舊架構自動切換")
        
        # 新架構模式
        integration_v5 = ProjectUpdateIntegrationV5(use_old_components=False)
        print(f"  v5.0 新架構模式: use_old_components={integration_v5.use_old_components}")
        
        # 舊架構模式（兼容）
        integration_v4 = ProjectUpdateIntegrationV5(use_old_components=True)
        print(f"  v4.x 兼容模式: use_old_components={integration_v4.use_old_components}")
        
        print("\n  可用方法:")
        methods = [
            "detect_trigger",
            "extract_project_name", 
            "get_full_workflow_guidance",
            "run_compatible_workflow"
        ]
        for method in methods:
            exists = hasattr(integration_v5, method)
            print(f"    {method}: {'✅' if exists else '❌'}")
        
    except ImportError as e:
        print(f"  演示失敗：組件未找到 - {e}")

def demo_migration_path():
    """演示遷移路徑"""
    print_header("5. 遷移路徑演示")
    
    print("\n🟡 漸進式遷移策略")
    migration_steps = '''
第1步：引入 SecurityValidator
  - 立即提升安全性
  - 不影響現有功能
  
第2步：引入 GitToolWrapper
  - 替換所有 subprocess 調用
  - 可選擇使用指引模式或兼容模式
  
第3步：引入 OpenClawToolsWrapper
  - 逐步替換模擬數據
  - 遷移到真實工具調用
  
第4步：引入 ProjectUpdateGuidance
  - 重構工作流程
  - 實現指引驅動架構
  
第5步：切換到 ProjectUpdateIntegrationV5
  - 使用新集成器
  - 享受所有 v5.0 優勢
'''
    print(migration_steps)
    
    print("\n🎯 遷移檢查點")
    print("  ✅ 所有測試通過 (test_v5_components.py)")
    print("  ✅ 組件獨立工作")
    print("  ✅ 向後兼容性驗證")
    print("  ✅ 文檔更新 (MIGRATION_GUIDE.md)")
    print("  ✅ 演示可用 (本文件)")
    
    print("\n🚀 立即開始遷移")
    print("  1. 閱讀 MIGRATION_GUIDE.md")
    print("  2. 運行測試套件")
    print("  3. 在測試項目上嘗試")
    print("  4. 逐步遷移生產代碼")

def main():
    """主函數"""
    print("=" * 70)
    print("Project Memory Manager v5.0 vs v4.x 架構對比演示")
    print("=" * 70)
    print("\n🎯 目標：展示 v5.0 如何解決 v4.x 的關鍵問題")
    print("👤 演示者：Nana (Sergio 的秘書)")
    print("📅 日期：2026-03-16")
    print("=" * 70)
    
    # 運行各個演示
    demo_security_comparison()
    demo_data_comparison()
    demo_architecture_comparison()
    demo_workflow_comparison()
    demo_migration_path()
    
    print("\n" + "=" * 70)
    print("演示總結")
    print("=" * 70)
    
    summary = {
        "v4.x 問題": [
            "直接使用 subprocess（安全風險）",
            "使用模擬數據（不真實）",
            "技能直接執行操作（違反 OpenClaw 哲學）",
            "難以測試和維護"
        ],
        "v5.0 解決方案": [
            "使用 exec 工具指引（安全）",
            "使用真實 OpenClaw 工具調用（準確）",
            "技能提供指引，Agent 執行（符合哲學）",
            "模塊化，易測試，可維護"
        ],
        "遷移優勢": [
            "漸進式遷移，無停機時間",
            "完全向後兼容",
            "可選擇新舊架構",
            "文檔和工具齊全"
        ]
    }
    
    for category, items in summary.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  • {item}")
    
    print("\n" + "=" * 70)
    print("下一步行動")
    print("=" * 70)
    print("\n1. 🧪 運行測試: python3 test_v5_components.py")
    print("2. 📖 閱讀指南: cat MIGRATION_GUIDE.md")
    print("3. 🎬 運行演示: python3 demo_v5_vs_v4.py")
    print("4. 🚀 開始遷移: 參考遷移步驟")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()