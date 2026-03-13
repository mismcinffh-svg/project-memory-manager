#!/usr/bin/env python3
"""
項目記憶管理器 - 觸發檢測器
實現兩個核心場景：
1. 口語化歸檔：檢測「歸檔」等關鍵詞，確認後更新專櫃
2. GitHub同步必做：檢測commit/push等，自動更新專櫃
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ProjectMemoryTrigger:
    """項目記憶觸發器"""
    
    def __init__(self, workspace_dir: str = None):
        if workspace_dir is None:
            # 嘗試自動檢測workspace
            current_dir = Path.cwd()
            for parent in [current_dir] + list(current_dir.parents):
                if (parent / "MEMORY.md").exists():
                    self.workspace_dir = parent
                    break
            else:
                self.workspace_dir = current_dir
        else:
            self.workspace_dir = Path(workspace_dir)
        
        self.skill_dir = self.workspace_dir / "skills" / "project-memory-manager"
        self.projects_dir = self.workspace_dir / "projects"
        
        # 場景1：口語化歸檔關鍵詞
        self.archive_keywords = [
            "歸檔", "記錄落去", "記錄返", "update落去",
            "更新落去", "整理落去", "整理記錄", "放入專櫃",
            "存檔", "保存記錄", "寫入專櫃", "更新專櫃",
            "內容歸檔", "對話歸檔", "傾過嘅歸檔", "更新項目"
        ]
        
        # 場景2：GitHub同步關鍵詞（必須觸發）
        self.github_sync_keywords = [
            "commit", "上github", "git push", "push",
            "同步上github", "同步到github", "上傳github",
            "更新倉庫", "同步倉庫", "上傳代碼", "提交代碼"
        ]
        
        # 項目名稱模式 - 匹配項目slug（字母、數字、連字符、下劃線）
        self.project_pattern = r'(?:項目|project)[:：\s]*([a-zA-Z0-9_-]+)'
        
        logger.info(f"觸發器初始化完成 - Workspace: {self.workspace_dir}")
    
    def detect_scenario(self, message: str) -> Tuple[str, Optional[str]]:
        """
        檢測觸發場景
        返回: (場景類型, 項目名稱)
        場景類型: "archive" | "github_sync" | "none"
        """
        message_lower = message.lower()
        
        # 場景1：口語化歸檔
        for keyword in self.archive_keywords:
            if keyword in message:
                logger.info(f"檢測到歸檔關鍵詞: {keyword}")
                project_name = self.extract_project_name(message)
                return "archive", project_name
        
        # 場景2：GitHub同步
        for keyword in self.github_sync_keywords:
            if keyword in message_lower:
                logger.info(f"檢測到GitHub同步關鍵詞: {keyword}")
                project_name = self.extract_project_name(message)
                return "github_sync", project_name
        
        return "none", None
    
    def extract_project_name(self, message: str) -> Optional[str]:
        """從消息中提取項目名稱"""
        # 獲取所有已知項目
        known_projects = self.get_all_projects()
        
        # 方法1：檢查消息中是否包含已知項目slug
        for project in known_projects:
            project_slug = project['slug']
            project_name = project['name']
            
            # 檢查消息是否包含項目slug或名稱
            if project_slug in message or project_name in message:
                logger.info(f"從消息找到已知項目: {project_slug} ({project_name})")
                return project_slug
        
        # 方法2：使用正則匹配「項目: xxx」或「project xxx」模式
        match = re.search(self.project_pattern, message, re.IGNORECASE)
        if match:
            project_name = match.group(1).strip()
            logger.info(f"從正則提取項目名: {project_name}")
            return project_name
        
        # 方法3：查找最近項目
        recent_project = self.get_recent_project()
        if recent_project:
            logger.info(f"使用最近項目: {recent_project}")
            return recent_project
        
        # 方法4：從上下文推斷（需要外部提供）
        return None
    
    def get_all_projects(self) -> List[Dict]:
        """獲取所有項目列表"""
        projects = []
        if not self.projects_dir.exists():
            return projects
        
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('_'):
                config_file = project_dir / "project.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            projects.append({
                                'slug': project_dir.name,
                                'name': config.get('name', project_dir.name),
                                'config': config
                            })
                    except:
                        pass
        
        return projects
    
    def get_recent_project(self) -> Optional[str]:
        """獲取最近活躍的項目"""
        if not self.projects_dir.exists():
            return None
        
        # 查找有project.json的項目
        projects = []
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('_'):
                config_file = project_dir / "project.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            # 檢查最後更新時間
                            last_update = config.get('last_summary_update')
                            if last_update:
                                projects.append({
                                    'name': project_dir.name,
                                    'last_update': last_update,
                                    'config': config
                                })
                    except:
                        pass
        
        if not projects:
            return None
        
        # 按最後更新時間排序
        projects.sort(key=lambda x: x['last_update'], reverse=True)
        return projects[0]['name']
    
    def get_archive_confirmation_message(self, project_name: str) -> str:
        """生成歸檔確認消息（根據用戶要求格式）"""
        if project_name:
            return f"好的，而家準備更新「{project_name}」項目專櫃內嘅內容，請問是否確認？"
        else:
            return f"好的，而家準備更新項目專櫃內嘅內容，請問是否確認？"
    
    def execute_archive_scenario(self, project_name: str, user_confirmed: bool = True) -> Dict:
        """執行口語化歸檔場景"""
        if not user_confirmed:
            return {
                "success": False,
                "message": "用戶取消歸檔操作",
                "action": "none"
            }
        
        if not project_name:
            return {
                "success": False,
                "message": "無法識別項目名稱，請明確指定項目",
                "action": "ask_project"
            }
        
        # 構建執行命令
        script_path = self.skill_dir / "scripts" / "project_update_integration.py"
        if not script_path.exists():
            return {
                "success": False,
                "message": f"找不到執行腳本: {script_path}",
                "action": "error"
            }
        
        # 執行專櫃更新
        import subprocess
        try:
            cmd = [
                "python3", str(script_path),
                "--project", project_name,
                "--update-summary",
                "--yes"  # 用戶已確認，自動執行
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5分鐘超時
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"✅ 項目「{project_name}」專櫃內容更新完成",
                    "action": "archive_completed",
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "message": f"❌ 專櫃更新失敗: {result.stderr[:200]}",
                    "action": "error",
                    "output": result.stdout,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "❌ 操作超時（5分鐘）",
                "action": "timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ 執行錯誤: {str(e)}",
                "action": "error"
            }
    
    def execute_github_sync_scenario(self, project_name: str) -> Dict:
        """執行GitHub同步場景（自動執行，無需用戶確認）"""
        if not project_name:
            # 嘗試獲取最近項目
            project_name = self.get_recent_project()
            if not project_name:
                return {
                    "success": False,
                    "message": "無法識別項目名稱，跳過專櫃更新",
                    "action": "skip"
                }
        
        logger.info(f"GitHub同步場景 - 自動更新專櫃: {project_name}")
        
        # 使用session_spawn分身更新專櫃（JSON格式溝通）
        # 這裡需要OpenClaw的sessions_spawn工具支持
        # 先回退到直接執行
        
        script_path = self.skill_dir / "scripts" / "project_update_integration.py"
        if not script_path.exists():
            return {
                "success": False,
                "message": f"找不到執行腳本: {script_path}",
                "action": "error"
            }
        
        # 執行專櫃更新（後台自動執行）
        import subprocess
        try:
            cmd = [
                "python3", str(script_path),
                "--project", project_name,
                "--update-summary",
                "--yes",  # 自動確認
                "--background"  # 後台執行，不阻塞
            ]
            
            # 後台執行
            process = subprocess.Popen(
                cmd,
                cwd=self.workspace_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            return {
                "success": True,
                "message": f"🔧 已啟動專櫃內容更新（項目: {project_name}）",
                "action": "github_sync_started",
                "pid": process.pid
            }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ GitHub同步場景執行錯誤: {str(e)}",
                "action": "error"
            }
    
    def process_message(self, message: str, user_id: str = None) -> Dict:
        """
        處理消息，返回觸發結果
        用於OpenClaw Agent集成
        """
        scenario, project_name = self.detect_scenario(message)
        
        if scenario == "none":
            return {
                "triggered": False,
                "scenario": "none",
                "message": "未觸發任何場景"
            }
        
        result = {
            "triggered": True,
            "scenario": scenario,
            "project_name": project_name,
            "timestamp": datetime.now().isoformat()
        }
        
        if scenario == "archive":
            # 口語化歸檔需要用戶確認
            result["needs_confirmation"] = True
            result["confirmation_message"] = self.get_archive_confirmation_message(project_name)
            result["action"] = "await_confirmation"
            
        elif scenario == "github_sync":
            # GitHub同步自動執行
            result["needs_confirmation"] = False
            result["action"] = "execute_immediately"
            
            # 立即執行
            exec_result = self.execute_github_sync_scenario(project_name)
            result.update(exec_result)
        
        return result


def main():
    """命令行測試"""
    import argparse
    
    parser = argparse.ArgumentParser(description='項目記憶觸發器測試')
    parser.add_argument('message', help='測試消息')
    parser.add_argument('--workspace', help='workspace目錄')
    parser.add_argument('--execute', action='store_true', help='直接執行')
    
    args = parser.parse_args()
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    trigger = ProjectMemoryTrigger(args.workspace)
    
    if args.execute:
        # 直接執行
        scenario, project_name = trigger.detect_scenario(args.message)
        print(f"場景: {scenario}, 項目: {project_name}")
        
        if scenario == "archive":
            print("口語化歸檔場景")
            print(f"確認消息: {trigger.get_archive_confirmation_message(project_name)}")
            
            # 模擬用戶確認
            result = trigger.execute_archive_scenario(project_name, user_confirmed=True)
            print(f"執行結果: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
        elif scenario == "github_sync":
            print("GitHub同步場景（自動執行）")
            result = trigger.execute_github_sync_scenario(project_name)
            print(f"執行結果: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
        else:
            print("未觸發任何場景")
            
    else:
        # 僅檢測
        result = trigger.process_message(args.message)
        print(f"檢測結果: {json.dumps(result, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    from datetime import datetime
    main()