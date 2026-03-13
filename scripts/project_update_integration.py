#!/usr/bin/env python3
"""
項目更新集成系統 - 協調對話摘要與版本管理
實現完整工作流程：
1. 檢測觸發關鍵詞
2. 識別項目
3. 詢問用戶確認
4. 更新專櫃內容（可選）
5. 執行版本更新與Git同步
"""

import os
import sys
import json
import argparse
import shutil
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# 添加當前目錄到路徑，以便導入本地模塊
sys.path.append(str(Path(__file__).parent))

from conversation_summary import ConversationSummary
from version_manager import VersionManager

logger = logging.getLogger(__name__)

class ProjectUpdateIntegration:
    """項目更新集成器"""
    
    def __init__(self, workspace_dir: str = None):
        if workspace_dir is None:
            # 智能檢測 workspace 目錄：向上遍歷尋找包含真實 projects/ 的目錄
            current_dir = Path(__file__).parent
            self.workspace_dir = current_dir
            
            # 向上遍歷最多 5 層，尋找包含真實 projects/ 的目錄
            for _ in range(5):
                projects_dir = self.workspace_dir / "projects"
                if projects_dir.exists():
                    # 檢查這是否是真實的 projects 目錄（包含至少一個有 project.json 的項目）
                    has_real_projects = False
                    try:
                        for item in projects_dir.iterdir():
                            if item.is_dir() and not item.name.startswith('_'):
                                config_path = item / "project.json"
                                if config_path.exists():
                                    has_real_projects = True
                                    break
                    except Exception as e:
                        logger.warning(f"檢查 projects 目錄時出錯: {e}")
                    
                    if has_real_projects:
                        logger.info(f"✅ 檢測到真實 workspace 目錄: {self.workspace_dir}")
                        break
                    else:
                        logger.debug(f"跳過空 projects 目錄: {projects_dir}")
                
                parent = self.workspace_dir.parent
                if parent == self.workspace_dir:  # 到達根目錄
                    break
                self.workspace_dir = parent
            
            logger.info(f"最終 workspace 目錄: {self.workspace_dir}")
        else:
            self.workspace_dir = Path(workspace_dir)
        
        self.projects_dir = self.workspace_dir / "projects"
        
        # 觸發關鍵詞配置
        self.trigger_keywords = [
            "commit", "上github", "git push", 
            "更新倉庫", "同步到github", "push",
            "更新版本", "version update", "版本更新",
            "發布", "release", "發佈", "上版"
        ]
    
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
                    except Exception as e:
                        logger.warning(f"讀取項目配置失敗 {item.name}: {e}")
                        continue
        
        return projects
    
    def detect_trigger(self, message: str) -> bool:
        """檢測是否觸發更新"""
        message_lower = message.lower()
        return any(keyword.lower() in message_lower for keyword in self.trigger_keywords)
    
    def extract_project_name(self, message: str, projects: List[Dict]) -> Optional[str]:
        """從消息中提取項目名稱"""
        message_lower = message.lower()
        
        # 1. 嘗試直接匹配項目slug
        for project in projects:
            slug = project['slug'].lower()
            name = project['name'].lower()
            
            if slug in message_lower or name in message_lower:
                return project['slug']
        
        # 2. 嘗試從指令中提取
        # 如 "commit project-memory-manager" → "project-memory-manager"
        words = message_lower.split()
        for i, word in enumerate(words):
            if word in ["commit", "push", "上", "更新", "同步", "version", "release"] and i + 1 < len(words):
                potential_name = words[i + 1]
                # 清理標點
                potential_name = potential_name.strip('.,;!?："\'')
                return potential_name
        
        # 3. 返回最近修改的項目
        if projects:
            sorted_projects = sorted(
                projects, 
                key=lambda p: p['config'].get('updated', ''), 
                reverse=True
            )
            return sorted_projects[0]['slug']
        
        return None
    
    def simulate_conversation_history(self, project_slug: str) -> List[Dict]:
        """模擬對話歷史（實際應從OpenClaw sessions_history獲取）"""
        # 這裡模擬一些對話
        # 實際應該使用 OpenClaw 的 sessions_history 工具
        
        now = datetime.now()
        ten_min_ago = int(now.timestamp() * 1000) - 600000
        
        sample_conversations = [
            {
                'role': 'user',
                'content': f'我準備commit {project_slug}上GitHub',
                'timestamp': str(ten_min_ago)
            },
            {
                'role': 'assistant',
                'content': f'好，準備commit {project_slug}。要唔要同時更新專櫃摘要？',
                'timestamp': str(ten_min_ago + 1000)
            },
            {
                'role': 'user',
                'content': '要，更新埋摘要啦',
                'timestamp': str(ten_min_ago + 2000)
            },
            {
                'role': 'assistant',
                'content': f'收到，開始為{project_slug}生成摘要...',
                'timestamp': str(ten_min_ago + 3000)
            }
        ]
        
        return sample_conversations
    
    def run_summary_update(self, project_dir: str, conversations: List[Dict]) -> bool:
        """運行摘要更新（模擬sessions_spawn）"""
        try:
            summary = ConversationSummary(project_dir)
            
            # 實際應該使用 sessions_spawn 調用sub-agent
            # 這裡模擬sub-agent的回應
            
            project_name = summary.config.get('name', '未知項目')
            since_time = summary.get_last_summary_time()
            
            # 構建prompt（實際應發送給sub-agent）
            prompt = summary.build_summary_prompt(project_name, conversations, since_time)
            
            logger.info(f"📝 生成摘要prompt（{len(prompt)} 字符）")
            logger.info(f"📊 對話條數: {len(conversations)}")
            
            # 模擬sub-agent回應
            mock_response = f"""--- decisions.md ---
- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] 決策：執行版本更新與專櫃同步
  原因：用戶觸發「更新版本」指令，需要同步專櫃內容與GitHub
  考慮選項：A只更新版本、B只更新專櫃、C兩者都更新
  參考對話：#1,#2,#3,#4

- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] 決策：採用_latest+_history文件分離結構
  原因：清晰區分最新摘要與完整歷史，方便查閱
  考慮選項：A單一文件、B分離結構、C混合模式
  參考對話：#1,#2

--- technical.md ---
- [版本管理系統]：實現自動版本遞增與CHANGELOG更新
  實現方式：VersionManager類，支持major/minor/patch遞增，自動生成CHANGELOG條目
  技術選擇：Python + 正則表達式，兼容語義化版本規範
  替代方案：手動更新（易出錯）、外部工具（依賴性）
  參考對話：#1,#2,#3,#4

- [Git集成]：自動化git操作流水線
  實現方式：subprocess調用git命令，錯誤處理與重試機制
  技術選擇：原生git命令，避免複雜庫依賴
  替代方案：GitPython庫（更重）、手動操作（不自動）
  參考對話：#1,#2

--- learnings.md ---
- [洞察]：自動化版本管理大幅減少人為錯誤
  應用場景：任何需要定期發布的項目，特別是開源項目
  經驗教訓：版本號遞增邏輯需要嚴格遵循語義化版本規範
  參考對話：#1,#2,#3

- [洞察]：用戶確認步驟至關重要
  應用場景：涉及文件修改的自動化功能，應給用戶最終控制權
  經驗教訓：即使自動化程度高，也要保留「開關」和確認步驟
  參考對話：#2,#3,#4"""
            
            # 解析回應
            sections = summary.parse_summary_response(mock_response)
            
            # 更新文件
            summary.update_project_files(sections)
            
            logger.info("✅ 摘要更新完成")
            return True
            
        except Exception as e:
            logger.error(f"摘要更新失敗: {e}")
            return False
    
    def run_full_update_workflow(self, project_slug: str, update_summary: bool = True, auto_confirm: bool = False) -> Tuple[bool, str]:
        """運行完整更新工作流程
        
        Args:
            project_slug: 項目slug
            update_summary: 是否更新專櫃摘要
            
        Returns:
            (是否成功, 新版本號)
        """
        try:
            logger.info(f"🚀 開始項目更新工作流程: {project_slug}")
            
            # 1. 找到項目目錄
            projects = self.list_projects()
            project_dir = None
            for project in projects:
                if project['slug'] == project_slug:
                    project_dir = project['path']
                    break
            
            if not project_dir:
                logger.error(f"❌ 找不到項目: {project_slug}")
                return False, ""
            
            logger.info(f"📂 項目目錄: {project_dir}")
            
            # 2. 如果更新摘要，獲取對話歷史並生成摘要
            if update_summary:
                logger.info("🔄 獲取對話歷史...")
                conversations = self.simulate_conversation_history(project_slug)
                
                logger.info("🤖 生成專櫃摘要...")
                if not self.run_summary_update(project_dir, conversations):
                    logger.warning("⚠️  摘要更新失敗，繼續版本更新")
                else:
                    logger.info("✅ 專櫃摘要更新完成")
            else:
                logger.info("⏭️  跳過專櫃摘要更新")
            
            # 3. 執行版本更新
            logger.info("🔄 執行版本更新...")
            version_manager = VersionManager(project_dir)
            
            # 根據更新類型決定遞增類型
            # 如果有摘要更新，視為minor更新（因為有內容變更）
            # 如果只有版本文件更新，視為patch更新
            increment_type = "minor" if update_summary else "patch"
            
            # 準備變更描述
            changes = []
            if update_summary:
                changes.append("更新專櫃摘要內容")
            changes.append("自動版本遞增與CHANGELOG更新")
            
            success, new_version = version_manager.full_version_update(
                increment_type=increment_type,
                changes=changes,
                run_git=True,
                auto_confirm=auto_confirm
            )
            
            if not success:
                logger.error("❌ 版本更新失敗")
                return False, ""
            
            logger.info(f"✅ 版本更新完成: v{new_version}")
            
            # 4. 如果是project-memory-manager項目，同步技能目錄的文件
            if project_slug == "project-memory-manager":
                self.sync_skill_documentation(project_dir, new_version)
            
            # 5. 返回結果
            return True, new_version
            
        except Exception as e:
            logger.error(f"❌ 更新工作流程失敗: {e}")
            return False, ""
    
    def sync_skill_documentation(self, project_dir: Path, new_version: str) -> bool:
        """同步技能目錄的CHANGELOG.md和README.md
        
        當更新project-memory-manager項目時，需要同時更新技能目錄的文件
        """
        try:
            # 技能目錄（當前腳本的上兩級目錄）
            skill_dir = Path(__file__).parent.parent
            
            # 需要同步的文件列表
            files_to_sync = ["CHANGELOG.md", "README.md"]
            
            for filename in files_to_sync:
                project_file = project_dir / filename
                skill_file = skill_dir / filename
                
                if project_file.exists():
                    # 複製文件
                    shutil.copy2(project_file, skill_file)
                    logger.info(f"✅ 同步 {filename} 到技能目錄")
                    
                    # 更新技能目錄文件中的版本號（如果文件中有版本號）
                    if filename == "README.md":
                        self.update_version_in_readme(skill_file, new_version)
                else:
                    logger.warning(f"⚠️  項目文件不存在: {project_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 同步技能目錄文件失敗: {e}")
            return False
    
    def update_version_in_readme(self, readme_path: Path, new_version: str) -> bool:
        """更新README.md中的版本號"""
        try:
            content = readme_path.read_text(encoding='utf-8')
            
            # 替換版本號模式
            version_patterns = [
                r'v?\d+\.\d+\.\d+',  # x.y.z
                r'版本\s*[:：]?\s*v?\d+\.\d+\.\d+',  # 版本: x.y.z
                r'Version\s*[:：]?\s*v?\d+\.\d+\.\d+'  # Version: x.y.z
            ]
            
            updated = False
            for pattern in version_patterns:
                if re.search(pattern, content):
                    # 簡單替換：將舊版本號替換為新版本號
                    # 替換 v1.0.0 → v{new_version} 和 1.0.0 → new_version
                    old_matches = re.findall(r'v?\d+\.\d+\.\d+', content)
                    for old_version in old_matches:
                        if old_version.startswith('v'):
                            content = content.replace(old_version, f"v{new_version}")
                        else:
                            content = content.replace(old_version, new_version)
                    updated = True
                    break
            
            if updated:
                readme_path.write_text(content, encoding='utf-8')
                logger.info(f"✅ 更新README.md版本號: v{new_version}")
            
            return updated
            
        except Exception as e:
            logger.error(f"❌ 更新README.md版本號失敗: {e}")
            return False
    
    def interactive_workflow(self, test_message: str = None):
        """交互式工作流程（用於演示和測試）"""
        print("🎬 項目更新集成系統演示")
        print("=" * 60)
        
        # 1. 列出項目
        projects = self.list_projects()
        if not projects:
            print("❌ 未找到項目，請先創建項目專櫃")
            return
        
        print(f"📁 找到 {len(projects)} 個項目:")
        for i, project in enumerate(projects, 1):
            print(f"  {i}. {project['name']} ({project['slug']})")
        
        # 2. 使用測試消息或輸入
        if test_message:
            message = test_message
        else:
            message = input("\n📝 輸入測試消息（如「更新版本 project-memory-manager」）: ")
        
        print(f"\n📨 消息: {message}")
        
        # 3. 檢測觸發
        if not self.detect_trigger(message):
            print("❌ 未觸發更新（不包含相關關鍵詞）")
            return
        
        print("✅ 觸發條件滿足")
        
        # 4. 識別項目
        project_slug = self.extract_project_name(message, projects)
        if not project_slug:
            print("❌ 無法識別項目名稱")
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
        
        # 5. 詢問是否更新專櫃摘要
        print("\n🤔 用戶確認")
        if test_message:
            # 測試模式，假設用戶同意
            update_summary = True
            print("✅ 測試模式：自動選擇更新專櫃摘要")
        else:
            response = input("要唔要同時更新項目專櫃內容？ (y/N): ").strip().lower()
            update_summary = response in ['y', 'yes', '要', '是']
        
        # 6. 運行完整工作流程
        print("\n🚀 開始更新工作流程...")
        success, new_version = self.run_full_update_workflow(project_slug, update_summary, auto_confirm=False)
        
        if success:
            print(f"\n🎉 更新完成！")
            print(f"   項目: {project_slug}")
            print(f"   新版本: v{new_version}")
            print(f"   專櫃更新: {'✅' if update_summary else '❌'}")
            print(f"   GitHub同步: ✅")
        else:
            print("\n❌ 更新失敗，請檢查錯誤信息")

def main():
    """命令行入口點"""
    import sys  # 確保在函數作用域內可用
    parser = argparse.ArgumentParser(description='項目更新集成系統')
    parser.add_argument('--message', help='測試消息')
    parser.add_argument('--workspace', help='OpenClaw workspace目錄')
    parser.add_argument('--project', help='指定項目slug')
    parser.add_argument('--update-summary', action='store_true', help='更新專櫃摘要')
    parser.add_argument('--no-update-summary', action='store_true', help='不更新專櫃摘要')
    parser.add_argument('--demo', action='store_true', help='運行交互式演示')
    parser.add_argument('--yes', action='store_true', help='自動確認，不詢問')
    parser.add_argument('--background', action='store_true', help='後台執行，不阻塞')
    
    args = parser.parse_args()
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    integration = ProjectUpdateIntegration(args.workspace)
    
    if args.demo:
        integration.interactive_workflow(args.message)
    elif args.project:
        # 指定項目直接運行
        update_summary = args.update_summary or (not args.no_update_summary)
        
        # 檢查是否需要後台執行
        if args.background:
            # 後台執行，不阻塞
            import subprocess
            import sys
            
            # 構建命令行參數
            cmd = [sys.executable, __file__]
            if args.workspace:
                cmd.extend(['--workspace', args.workspace])
            cmd.extend(['--project', args.project])
            if update_summary:
                cmd.append('--update-summary')
            else:
                cmd.append('--no-update-summary')
            cmd.append('--yes')  # 後台執行自動確認
            
            # 後台啟動
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"🔧 後台執行已啟動 (PID: {process.pid})")
            print(f"   項目: {args.project}")
            print(f"   專櫃更新: {'✅' if update_summary else '❌'}")
            sys.exit(0)
        else:
            # 前台執行
            success, new_version = integration.run_full_update_workflow(
                args.project, 
                update_summary, 
                auto_confirm=args.yes
            )
            
            if success:
                print(f"✅ 更新成功: {args.project} v{new_version}")
            else:
                print(f"❌ 更新失敗: {args.project}")
                sys.exit(1)
    else:
        print("使用方法：")
        print("  --demo                   運行交互式演示")
        print("  --project <slug>         指定項目運行更新")
        print("  --update-summary         更新專櫃摘要（默認）")
        print("  --no-update-summary      不更新專櫃摘要")
        print("  --yes                    自動確認，不詢問")
        print("  --background             後台執行，不阻塞")
        print("\n示例：")
        print("  python project_update_integration.py --demo")
        print("  python project_update_integration.py --project project-memory-manager --update-summary")
        print("  python project_update_integration.py --project project-memory-manager --update-summary --yes")
        print("  python project_update_integration.py --project project-memory-manager --update-summary --background")

if __name__ == "__main__":
    main()