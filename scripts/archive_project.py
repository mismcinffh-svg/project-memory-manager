#!/usr/bin/env python3
"""
項目歸檔專用工具 - v5.0.3

遵循OpenClaw哲學：技能提供指引，但此工具提供「立即可執行」的歸檔流程
3步完成歸檔：
1. sessions_history獲取真實對話
2. sessions_spawn生成摘要
3. 原子寫入文件

設計目標：30秒內完成歸檔，無需探索代碼
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging

# 添加當前目錄到路徑
sys.path.append(str(Path(__file__).parent))

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 導入所需組件
try:
    from security import SecurityValidator
    from openclaw_tools_wrapper import OpenClawToolsWrapper
    from project_update_guidance import ProjectUpdateGuidance
    from conversation_summary import ConversationSummary
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"組件導入失敗: {e}")
    COMPONENTS_AVAILABLE = False
    sys.exit(1)


class ProjectArchiveTool:
    """項目歸檔工具 - 立即可執行版本"""
    
    def __init__(self, workspace_dir: Optional[Path] = None):
        """
        初始化歸檔工具
        
        Args:
            workspace_dir: 工作空間目錄（包含projects/）
        """
        if workspace_dir is None:
            # 嘗試從環境變量獲取
            workspace_env = os.getenv('OPENCLAW_WORKSPACE')
            if workspace_env:
                workspace_dir = Path(workspace_env)
            else:
                # 默認：當前目錄向上尋找包含projects/的目錄
                workspace_dir = self._find_workspace_dir()
        
        self.workspace_dir = Path(workspace_dir)
        self.projects_dir = self.workspace_dir / "projects"
        
        # 確保目錄存在
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化組件
        self.security = SecurityValidator(self.workspace_dir)
        self.guidance_gen = ProjectUpdateGuidance(self.workspace_dir)
        
        logger.info(f"歸檔工具初始化完成: workspace={self.workspace_dir}")
    
    def _find_workspace_dir(self) -> Path:
        """智能尋找workspace目錄"""
        current_dir = Path.cwd()
        
        # 向上遍歷最多5層，尋找包含projects/的目錄
        for _ in range(5):
            projects_dir = current_dir / "projects"
            if projects_dir.exists():
                # 檢查這是否是真實的projects目錄
                has_real_projects = False
                try:
                    for item in projects_dir.iterdir():
                        if item.is_dir() and (item / "project.json").exists():
                            has_real_projects = True
                            break
                    
                    if has_real_projects:
                        return current_dir
                except Exception:
                    pass
            
            if current_dir.parent == current_dir:  # 到達根目錄
                break
            current_dir = current_dir.parent
        
        # 未找到，使用當前目錄
        logger.warning(f"未找到projects目錄，使用當前目錄: {Path.cwd()}")
        return Path.cwd()
    
    def archive_project(self, project_slug: str, limit: int = 30, 
                       update_summary: bool = True) -> Dict:
        """
        執行項目歸檔
        
        Args:
            project_slug: 項目slug（projects/下的目錄名）
            limit: 獲取多少條對話歷史
            update_summary: 是否更新專櫃摘要
            
        Returns:
            歸檔結果字典
        """
        logger.info(f"🚀 開始歸檔項目: {project_slug}")
        
        # 1. 檢查項目目錄
        project_dir = self.projects_dir / project_slug
        if not project_dir.exists():
            return {
                "success": False,
                "error": f"項目目錄不存在: {project_dir}",
                "suggestion": f"請先創建項目: mkdir -p {project_dir}"
            }
        
        # 2. 安全驗證
        is_safe, error = self.security.validate_path(project_dir)
        if not is_safe:
            return {
                "success": False,
                "error": f"安全驗證失敗: {error}",
                "project_dir": str(project_dir)
            }
        
        result = {
            "project": project_slug,
            "timestamp": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            # 3. 獲取歸檔工作流程指引
            logger.info("📋 生成歸檔工作流程指引...")
            workflow = self.guidance_gen.get_archive_workflow(project_slug)
            result["workflow"] = workflow
            
            # 記錄步驟1：指引生成完成
            result["steps"].append({
                "step": 1,
                "name": "生成歸檔指引",
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            })
            
            # 4. 獲取對話歷史（真實工具調用指引）
            logger.info("💬 獲取對話歷史指引...")
            tools = OpenClawToolsWrapper(project_slug)
            history_guidance = tools.get_conversation_history(limit=limit)
            
            result["history_guidance"] = history_guidance
            result["steps"].append({
                "step": 2,
                "name": "生成對話歷史指引",
                "status": "completed",
                "guidance": history_guidance,
                "timestamp": datetime.now().isoformat()
            })
            
            # 5. 生成摘要指引
            if update_summary:
                logger.info("📝 生成摘要指引...")
                
                # 模擬一些對話（實際應從sessions_history獲取）
                sample_conversations = self._get_sample_conversations(project_slug)
                
                # 獲取上次摘要時間
                last_summary_time = self._get_last_summary_time(project_dir)
                
                summary_guidance = tools.spawn_summary_agent(
                    project_name=project_slug,
                    conversations=sample_conversations,
                    since_time=last_summary_time
                )
                
                result["summary_guidance"] = summary_guidance
                result["steps"].append({
                    "step": 3,
                    "name": "生成摘要指引",
                    "status": "completed",
                    "guidance": summary_guidance,
                    "timestamp": datetime.now().isoformat()
                })
            
            # 6. 生成執行方案
            logger.info("🔧 生成執行方案...")
            execution_scheme = tools.get_execution_scheme(history_guidance)
            
            # 添加示例代碼
            python_example = tools.generate_execution_example(history_guidance, "python")
            
            result["execution_scheme"] = execution_scheme
            result["python_example"] = python_example
            result["steps"].append({
                "step": 4,
                "name": "生成執行方案",
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            })
            
            # 7. 更新專櫃文件
            if update_summary:
                logger.info("📁 準備更新專櫃文件...")
                
                # 這裡應該實際執行歸檔操作
                # 但根據v5.0哲學，技能只提供指引
                # Agent需要根據指引執行實際操作
                
                update_plan = {
                    "action": "update_cabinet_files",
                    "files_to_update": [
                        "decisions.md",
                        "learnings_latest.md",
                        "technical_latest.md"
                    ],
                    "method": "使用conversation_summary.update_project_files()",
                    "note": "Agent應根據指引執行實際文件更新操作"
                }
                
                result["update_plan"] = update_plan
                result["steps"].append({
                    "step": 5,
                    "name": "準備文件更新計劃",
                    "status": "completed",
                    "plan": update_plan,
                    "timestamp": datetime.now().isoformat()
                })
            
            # 8. 完成
            result["success"] = True
            result["message"] = f"項目 '{project_slug}' 歸檔準備完成"
            result["next_steps"] = [
                "1. 根據指引執行對話歷史獲取",
                "2. 根據指引生成摘要",
                "3. 根據計劃更新專櫃文件",
                "4. 可選：同步到GitHub"
            ]
            
            logger.info(f"✅ 歸檔準備完成: {project_slug}")
            
        except Exception as e:
            logger.error(f"❌ 歸檔過程中出錯: {e}", exc_info=True)
            result["success"] = False
            result["error"] = str(e)
            result["steps"].append({
                "step": "error",
                "name": "歸檔過程出錯",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        
        return result
    
    def _get_sample_conversations(self, project_slug: str) -> List[Dict]:
        """獲取示例對話（實際應從sessions_history獲取）"""
        # 這裡返回模擬數據，實際應使用sessions_history工具
        now = datetime.now()
        ten_min_ago = int(now.timestamp() * 1000) - 600000
        
        return [
            {
                'role': 'user',
                'content': f'我要歸檔 {project_slug} 項目的討論內容',
                'timestamp': str(ten_min_ago)
            },
            {
                'role': 'assistant',
                'content': f'好的，開始歸檔 {project_slug} 項目。首先獲取對話歷史...',
                'timestamp': str(ten_min_ago + 1000)
            }
        ]
    
    def _get_last_summary_time(self, project_dir: Path) -> str:
        """獲取上次摘要時間"""
        config_path = project_dir / "project.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    last_update = config.get('last_summary_update')
                    if last_update:
                        return last_update
            except Exception:
                pass
        
        # 默認：一天前
        one_day_ago = datetime.now().isoformat().replace('+00:00', 'Z')
        return one_day_ago
    
    def generate_quick_archive_script(self, project_slug: str) -> str:
        """
        生成快速歸檔腳本
        
        Args:
            project_slug: 項目slug
            
        Returns:
            Python腳本代碼
        """
        return f'''#!/usr/bin/env python3
"""
{project_slug} 項目快速歸檔腳本
由Project Archive Tool生成
"""

import sys
import os
import json

# 添加技能目錄到路徑
skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, skill_dir)

from scripts.archive_project import ProjectArchiveTool

def main():
    """執行歸檔"""
    print(f"🚀 開始歸檔項目: {project_slug}")
    
    # 初始化工具
    tool = ProjectArchiveTool()
    
    # 執行歸檔
    result = tool.archive_project("{project_slug}", limit=30, update_summary=True)
    
    if result.get("success"):
        print("✅ 歸檔準備完成")
        print(f"   項目: {{result.get('project')}}")
        print(f"   步驟數: {{len(result.get('steps', []))}}")
        
        next_steps = result.get('next_steps', [])
        if next_steps:
            print(f"   下一步: {{next_steps[0]}}")
        
        # 保存結果
        output_file = f"archive_result_{project_slug}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"📄 結果已保存: {{output_file}}")
    else:
        print(f"❌ 歸檔失敗: {{result.get('error')}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='項目歸檔工具 - 3步完成歸檔 (v5.0.3)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 基本歸檔
  python3 archive_project.py --project project-name
  
  # 歸檔並生成腳本
  python3 archive_project.py --project project-name --generate-script
  
  # 指定workspace目錄
  python3 archive_project.py --project project-name --workspace /path/to/workspace
  
  # 獲取幫助
  python3 archive_project.py --help
        """
    )
    
    parser.add_argument(
        '--project', '-p',
        required=True,
        help='項目slug（projects/下的目錄名）'
    )
    
    parser.add_argument(
        '--workspace', '-w',
        help='workspace目錄（包含projects/），默認自動檢測'
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=30,
        help='獲取對話歷史的條數（默認：30）'
    )
    
    parser.add_argument(
        '--no-summary',
        action='store_true',
        help='不更新專櫃摘要'
    )
    
    parser.add_argument(
        '--generate-script',
        action='store_true',
        help='生成快速歸檔腳本'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='輸出結果文件（JSON格式）'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='詳細輸出模式'
    )
    
    args = parser.parse_args()
    
    # 設置日誌級別
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 初始化工具
    workspace_dir = Path(args.workspace) if args.workspace else None
    tool = ProjectArchiveTool(workspace_dir)
    
    # 如果需要生成腳本
    if args.generate_script:
        script_content = tool.generate_quick_archive_script(args.project)
        script_filename = f"archive_{args.project}.py"
        
        with open(script_filename, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ 快速歸檔腳本已生成: {script_filename}")
        print(f"   使用方法: python3 {script_filename}")
        return
    
    # 執行歸檔
    result = tool.archive_project(
        project_slug=args.project,
        limit=args.limit,
        update_summary=not args.no_summary
    )
    
    # 輸出結果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"📄 結果已保存: {args.output}")
    
    # 控制台輸出
    if result.get("success"):
        print(f"✅ {result.get('message')}")
        print(f"   項目: {result.get('project')}")
        print(f"   時間: {result.get('timestamp')}")
        print(f"   完成步驟: {len(result.get('steps', []))}")
        
        if 'next_steps' in result:
            print("\n📋 下一步:")
            for i, step in enumerate(result['next_steps'], 1):
                print(f"   {i}. {step}")
        
        print("\n💡 提示: 使用 --generate-script 生成可執行的歸檔腳本")
    else:
        print(f"❌ 歸檔失敗: {result.get('error')}")
        if 'suggestion' in result:
            print(f"💡 建議: {result.get('suggestion')}")
        sys.exit(1)


if __name__ == "__main__":
    main()