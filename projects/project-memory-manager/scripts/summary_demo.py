#!/usr/bin/env python3
"""
對話摘要系統 - 完整演示
展示從觸發到更新的完整流程
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加conversation_summary模塊路徑
sys.path.append(str(Path(__file__).parent))
from conversation_summary import ConversationSummary

class SummarySystemDemo:
    def __init__(self, workspace_dir: str = None):
        if workspace_dir is None:
            # 默認使用當前目錄的父目錄（projects/）
            self.workspace_dir = Path(__file__).parent.parent.parent
        else:
            self.workspace_dir = Path(workspace_dir)
        
        self.projects_dir = self.workspace_dir / "projects"
        
    def list_projects(self) -> List[Dict]:
        """列出所有項目"""
        projects = []
        
        if not self.projects_dir.exists():
            return projects
        
        for item in self.projects_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                config_path = item / "project.json"
                if config_path.exists():
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        projects.append({
                            'name': config.get('name', item.name),
                            'slug': config.get('slug', item.name),
                            'path': str(item),
                            'config': config
                        })
                    except:
                        continue
        
        return projects
    
    def detect_trigger(self, message: str) -> bool:
        """檢測是否觸發摘要更新"""
        trigger_keywords = [
            "commit", "上github", "git push", 
            "更新倉庫", "同步到github", "push"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in trigger_keywords)
    
    def extract_project_name(self, message: str, projects: List[Dict]) -> str:
        """從消息中提取項目名稱"""
        message_lower = message.lower()
        
        # 1. 嘗試直接匹配項目slug
        for project in projects:
            slug = project['slug'].lower()
            name = project['name'].lower()
            
            if slug in message_lower or name in message_lower:
                return project['slug']
        
        # 2. 嘗試從commit指令中提取
        # 如 "commit project-memory-manager" → "project-memory-manager"
        words = message_lower.split()
        for i, word in enumerate(words):
            if word in ["commit", "push", "上"] and i + 1 < len(words):
                potential_name = words[i + 1]
                # 清理可能的標點
                potential_name = potential_name.strip('.,;!?')
                return potential_name
        
        # 3. 返回最近修改的項目
        if projects:
            # 按更新時間排序
            sorted_projects = sorted(
                projects, 
                key=lambda p: p['config'].get('updated', ''), 
                reverse=True
            )
            return sorted_projects[0]['slug']
        
        return None
    
    def simulate_conversation_history(self, project_slug: str) -> List[Dict]:
        """模擬對話歷史（實際應從sessions_history獲取）"""
        # 這裡模擬一些對話
        # 實際應該使用 OpenClaw 的 sessions_history 工具
        
        sample_conversations = [
            {
                'role': 'user',
                'content': f'我準備commit {project_slug}上GitHub',
                'timestamp': str(int(datetime.now().timestamp() * 1000) - 600000)  # 10分鐘前
            },
            {
                'role': 'assistant',
                'content': f'好，準備commit {project_slug}。要唔要同時更新專櫃摘要？',
                'timestamp': str(int(datetime.now().timestamp() * 1000) - 599000)
            },
            {
                'role': 'user',
                'content': '要，更新埋摘要啦',
                'timestamp': str(int(datetime.now().timestamp() * 1000) - 598000)
            },
            {
                'role': 'assistant',
                'content': '收到，開始生成摘要...',
                'timestamp': str(int(datetime.now().timestamp() * 1000) - 597000)
            }
        ]
        
        return sample_conversations
    
    def generate_summary_with_subagent(self, project_dir: str, conversations: List[Dict]) -> Dict[str, str]:
        """使用sub-agent生成摘要（模擬）"""
        # 實際應該使用 sessions_spawn 工具
        # 這裡模擬sub-agent的回應
        
        summary = ConversationSummary(project_dir)
        project_name = summary.config.get('name', '未知項目')
        since_time = summary.get_last_summary_time()
        
        # 構建prompt
        prompt = summary.build_summary_prompt(project_name, conversations, since_time)
        
        print("=== 模擬sub-agent處理 ===")
        print(f"項目: {project_name}")
        print(f"對話條數: {len(conversations)}")
        print(f"Prompt長度: {len(prompt)} 字符")
        print()
        
        # 模擬sub-agent回應（實際應從sessions_spawn獲取）
        mock_response = f"""--- decisions.md ---
- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] 決策：實現對話摘要系統
  原因：解決專櫃與GitHub脫節問題，提供決策追溯
  考慮選項：A從commit倒推（不準確）、B從對話直接記錄（準確但需集成）、C混合方案
  參考對話：#1,#2,#3,#4

- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] 決策：採用「先問後做」觸發機制
  原因：平衡自動化與用戶控制，避免過度打擾
  考慮選項：A全自動（可能太煩）、B全手動（太麻煩）、C先問後做（平衡）
  參考對話：#2,#3

--- technical.md ---
- [對話摘要系統]：OpenClaw集成設計
  實現方式：關鍵詞觸發 → 項目識別 → 對話獲取 → sessions_spawn生成摘要 → 文件更新
  技術選擇：Python + OpenClaw工具（sessions_history, sessions_spawn）
  替代方案：獨立服務（更複雜）、GitHub Action（需API暴露）
  參考對話：#1,#2,#3,#4

- [觸發檢測]：智能關鍵詞匹配
  實現方式：正則表達式匹配commit相關詞彙
  技術選擇：簡單字符串匹配，避免複雜NLP
  替代方案：ML模型（過度設計）
  參考對話：#1,#2

--- learnings.md ---
- [洞察]：用戶更在意可控性而非全自動
  應用場景：AI功能設計時應提供開關和確認步驟
  經驗教訓：即使犧牲一點便利，也要給用戶控制權
  參考對話：#1,#2,#3

- [洞察]：從對話源頭記錄比從結果倒推更準確
  應用場景：決策記錄應在決策發生時進行，而非事後分析
  經驗教訓：捕捉意圖比分析結果更重要
  參考對話：#3,#4"""
        
        # 解析回應
        sections = summary.parse_summary_response(mock_response)
        
        print("✅ 模擬摘要生成完成")
        print(f"  decisions: {len(sections['decisions'])} 字符")
        print(f"  technical: {len(sections['technical'])} 字符")
        print(f"  learnings: {len(sections['learnings'])} 字符")
        
        return sections
    
    def run_demo(self, test_message: str = None):
        """運行完整演示"""
        print("🎬 對話摘要系統演示")
        print("=" * 50)
        
        # 1. 列出項目
        projects = self.list_projects()
        print(f"📁 找到 {len(projects)} 個項目:")
        for project in projects:
            print(f"  - {project['name']} ({project['slug']})")
        
        if not projects:
            print("❌ 未找到項目，請先創建項目專櫃")
            return
        
        # 2. 使用測試消息或輸入
        if test_message:
            message = test_message
        else:
            message = input("\n📝 輸入測試消息（如「commit project-memory-manager」）: ")
        
        print(f"\n📨 消息: {message}")
        
        # 3. 檢測觸發
        if not self.detect_trigger(message):
            print("❌ 未觸發摘要更新（不包含commit相關關鍵詞）")
            return
        
        print("✅ 觸發條件滿足（包含commit相關關鍵詞）")
        
        # 4. 識別項目
        project_slug = self.extract_project_name(message, projects)
        if not project_slug:
            print("❌ 無法識別項目名稱")
            # 顯示項目列表讓用戶選擇
            print("\n可選項目:")
            for i, project in enumerate(projects, 1):
                print(f"  {i}. {project['name']}")
            
            try:
                choice = int(input("請選擇項目編號: ")) - 1
                if 0 <= choice < len(projects):
                    project_slug = projects[choice]['slug']
                else:
                    print("❌ 選擇無效")
                    return
            except:
                print("❌ 輸入無效")
                return
        
        print(f"✅ 識別項目: {project_slug}")
        
        # 5. 找到項目目錄
        project_dir = None
        for project in projects:
            if project['slug'] == project_slug:
                project_dir = project['path']
                break
        
        if not project_dir:
            print(f"❌ 找不到項目目錄: {project_slug}")
            return
        
        print(f"📂 項目目錄: {project_dir}")
        
        # 6. 模擬對話歷史（實際應從sessions_history獲取）
        print("\n🔄 獲取對話歷史...")
        conversations = self.simulate_conversation_history(project_slug)
        print(f"✅ 獲取到 {len(conversations)} 條對話")
        
        # 7. 生成摘要（模擬sub-agent）
        print("\n🤖 生成摘要...")
        sections = self.generate_summary_with_subagent(project_dir, conversations)
        
        # 8. 更新文件
        print("\n📝 更新專櫃文件...")
        summary = ConversationSummary(project_dir)
        summary.update_project_files(sections)
        
        print("\n🎉 演示完成！")
        print("\n📊 總結:")
        print(f"  1. 觸發檢測: ✅")
        print(f"  2. 項目識別: ✅ ({project_slug})")
        print(f"  3. 對話獲取: ✅ ({len(conversations)}條)")
        print(f"  4. 摘要生成: ✅ (模擬)")
        print(f"  5. 文件更新: ✅")
        
        print("\n💡 實際集成需要:")
        print("  - 在OpenClaw Agent中實現觸發檢測")
        print("  - 使用 sessions_history 獲取真實對話")
        print("  - 使用 sessions_spawn 調用真實sub-agent")
        print("  - 與git操作集成")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='對話摘要系統演示')
    parser.add_argument('--message', help='測試消息')
    parser.add_argument('--workspace', help='OpenClaw workspace目錄')
    
    args = parser.parse_args()
    
    demo = SummarySystemDemo(args.workspace)
    demo.run_demo(args.message)

if __name__ == "__main__":
    # 默認測試
    demo = SummarySystemDemo()
    demo.run_demo("commit project-memory-manager 上GitHub")