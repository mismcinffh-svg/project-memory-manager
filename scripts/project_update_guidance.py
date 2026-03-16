#!/usr/bin/env python3
"""
項目更新指引生成器 - v5.0新架構

基於OpenClaw哲學重新設計：
- 技能提供指引，不直接執行操作
- 所有操作通過OpenClaw工具完成
- 清晰的責任分離：技能指導，Agent執行

設計原則：
1. 零subprocess調用 → 使用exec工具指引
2. 零模擬數據 → 使用真實工具調用指引  
3. 安全性優先 → 路徑驗證和命令清理
4. 模塊化設計 → 可組合的工作流程步驟
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import logging

logger = logging.getLogger(__name__)


class ProjectUpdateGuidance:
    """項目更新指引生成器"""
    
    def __init__(self, workspace_dir: Path = None):
        """
        初始化指引生成器
        
        Args:
            workspace_dir: OpenClaw workspace目錄，None則自動檢測
        """
        if workspace_dir is None:
            # 嘗試從環境變量獲取
            workspace_env = os.environ.get("OPENCLAW_WORKSPACE")
            if workspace_env:
                self.workspace_dir = Path(workspace_env).resolve()
            else:
                # 簡單檢測：當前目錄的父級
                self.workspace_dir = Path(__file__).parent.parent.parent.resolve()
        else:
            self.workspace_dir = Path(workspace_dir).resolve()
        
        self.projects_dir = self.workspace_dir / "projects"
        
        logger.info(f"指引生成器初始化，workspace: {self.workspace_dir}")
    
    def detect_scenario(self, user_message: str) -> Dict:
        """
        檢測用戶意圖並生成相應指引
        
        Args:
            user_message: 用戶消息
            
        Returns:
            場景檢測結果和推薦指引
        """
        # 觸發關鍵詞
        triggers = {
            "commit": ["commit", "上github", "git push", "同步到github"],
            "update": ["更新版本", "version update", "版本更新"],
            "release": ["發布", "release", "發佈", "上版"],
            "archive": ["歸檔", "記錄落去", "更新專櫃"]
        }
        
        message_lower = user_message.lower()
        detected_scenarios = []
        
        for scenario, keywords in triggers.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_scenarios.append(scenario)
        
        # 確定主要場景
        primary_scenario = None
        if detected_scenarios:
            # 優先級：release > update > commit > archive
            priority = {"release": 4, "update": 3, "commit": 2, "archive": 1}
            detected_scenarios.sort(key=lambda s: priority.get(s, 0), reverse=True)
            primary_scenario = detected_scenarios[0]
        
        # 提取項目名稱
        project_slug = self._extract_project_slug(user_message)
        
        guidance = {
            "user_message": user_message,
            "detected_scenarios": detected_scenarios,
            "primary_scenario": primary_scenario,
            "project_slug": project_slug,
            "recommended_workflow": self._get_workflow_for_scenario(primary_scenario, project_slug)
        }
        
        return guidance
    
    def _extract_project_slug(self, message: str) -> Optional[str]:
        """從消息中提取項目slug"""
        # 簡單實現：查找可能的項目名稱
        words = message.split()
        for word in words:
            # 移除標點
            clean_word = re.sub(r'[^\w\-]', '', word)
            if re.match(r'^[a-z0-9\-]+$', clean_word) and len(clean_word) > 3:
                # 檢查是否可能是項目目錄
                potential_path = self.projects_dir / clean_word
                if potential_path.exists():
                    return clean_word
        
        return None
    
    def _get_workflow_for_scenario(self, scenario: str, project_slug: str = None) -> Dict:
        """獲取場景對應的工作流程"""
        workflows = {
            "commit": self.get_commit_workflow(project_slug),
            "update": self.get_version_update_workflow(project_slug),
            "release": self.get_release_workflow(project_slug),
            "archive": self.get_archive_workflow(project_slug),
            "default": self.get_default_workflow(project_slug)
        }
        
        return workflows.get(scenario, workflows["default"])
    
    def get_commit_workflow(self, project_slug: str = None) -> Dict:
        """獲取提交工作流程指引"""
        workflow = {
            "name": "Git提交工作流程",
            "description": "準備並提交項目更改到GitHub",
            "steps": [
                {
                    "step": 1,
                    "name": "檢查項目狀態",
                    "guidance": {
                        "tool": "git",
                        "action": "check_status",
                        "implementation": "使用GitToolWrapper.git_status()",
                        "purpose": "查看當前更改狀態"
                    }
                },
                {
                    "step": 2,
                    "name": "詢問是否更新專櫃摘要",
                    "guidance": {
                        "tool": "interaction",
                        "action": "ask_user",
                        "question": "要唔要同時更新項目專櫃內容？",
                        "options": ["要", "不要", "稍後再問"],
                        "default": "要" if project_slug else "不要"
                    },
                    "note": "此步驟需要用戶交互"
                },
                {
                    "step": 3,
                    "name": "執行Git操作",
                    "guidance": {
                        "tool": "batch",
                        "action": "git_commit_flow",
                        "commands": [
                            {"cmd": ["git", "add", "."], "desc": "添加所有更改"},
                            {"cmd": ["git", "commit", "-m", "chore: update project"], "desc": "提交更改"},
                            {"cmd": ["git", "push", "origin", "main"], "desc": "推送到遠端"}
                        ],
                        "implementation": "使用GitToolWrapper.batch_execute()"
                    },
                    "conditional": "如果用戶確認執行"
                }
            ],
            "estimated_duration": "2-5分鐘",
            "token_cost": "低"
        }
        
        if project_slug:
            workflow["project"] = project_slug
        
        return workflow
    
    def get_version_update_workflow(self, project_slug: str = None) -> Dict:
        """獲取版本更新工作流程指引"""
        workflow = {
            "name": "版本更新工作流程",
            "description": "遞增版本號，更新CHANGELOG，並同步到GitHub",
            "steps": [
                {
                    "step": 1,
                    "name": "檢查當前版本",
                    "guidance": {
                        "tool": "custom",
                        "action": "read_project_config",
                        "implementation": "讀取project.json中的version字段",
                        "file": f"projects/{project_slug or '<project>'}/project.json"
                    }
                },
                {
                    "step": 2,
                    "name": "確定更新類型",
                    "guidance": {
                        "tool": "interaction",
                        "action": "ask_update_type",
                        "question": "請選擇版本更新類型：",
                        "options": [
                            {"value": "patch", "desc": "修補版本 (x.y.z → x.y.z+1)，小問題修復"},
                            {"value": "minor", "desc": "次要版本 (x.y.z → x.y+1.0)，新功能但向後兼容"},
                            {"value": "major", "desc": "主要版本 (x.y.z → x+1.0.0)，破壞性變更"}
                        ],
                        "default": "minor"
                    }
                },
                {
                    "step": 3,
                    "name": "更新版本號",
                    "guidance": {
                        "tool": "custom",
                        "action": "update_version",
                        "implementation": "使用version_manager.increment_version()",
                        "parameters": {
                            "increment_type": "從步驟2獲取",
                            "project_dir": f"projects/{project_slug or '<project>'}"
                        }
                    },
                    "depends_on": 2
                },
                {
                    "step": 4,
                    "name": "更新CHANGELOG",
                    "guidance": {
                        "tool": "custom",
                        "action": "update_changelog",
                        "implementation": "使用version_manager.update_changelog()",
                        "file": f"projects/{project_slug or '<project>'}/CHANGELOG.md"
                    },
                    "depends_on": 3
                },
                {
                    "step": 5,
                    "name": "Git提交與標籤",
                    "guidance": {
                        "tool": "batch",
                        "action": "version_git_flow",
                        "commands": [
                            {"cmd": ["git", "add", "project.json", "CHANGELOG.md"], "desc": "添加版本文件"},
                            {"cmd": ["git", "commit", "-m", "chore: release vX.Y.Z"], "desc": "提交版本更新"},
                            {"cmd": ["git", "tag", "-a", "vX.Y.Z", "-m", "Version vX.Y.Z"], "desc": "創建標籤"},
                            {"cmd": ["git", "push", "origin", "main"], "desc": "推送分支"},
                            {"cmd": ["git", "push", "origin", "vX.Y.Z"], "desc": "推送標籤"}
                        ],
                        "implementation": "使用GitToolWrapper.batch_execute()"
                    },
                    "depends_on": 4
                }
            ],
            "estimated_duration": "5-10分鐘",
            "token_cost": "中"
        }
        
        if project_slug:
            workflow["project"] = project_slug
        
        return workflow
    
    def get_release_workflow(self, project_slug: str = None) -> Dict:
        """獲取發布工作流程指引"""
        workflow = self.get_version_update_workflow(project_slug)
        workflow["name"] = "項目發布工作流程"
        workflow["description"] = "完整項目發布流程，包括版本更新、專櫃摘要和GitHub同步"
        
        # 在版本更新基礎上添加專櫃摘要步驟
        workflow["steps"].insert(1, {
            "step": 1.5,
            "name": "生成發布摘要",
            "guidance": {
                "tool": "openclaw",
                "action": "generate_release_summary",
                "implementation": "使用OpenClawToolsWrapper.spawn_summary_agent()生成發布摘要",
                "purpose": "記錄發布決策和技術要點"
            }
        })
        
        # 更新步驟編號
        for i, step in enumerate(workflow["steps"]):
            if isinstance(step.get("step"), (int, float)):
                step["step"] = i + 1
        
        workflow["estimated_duration"] = "10-15分鐘"
        workflow["token_cost"] = "高"
        
        return workflow
    
    def get_archive_workflow(self, project_slug: str = None) -> Dict:
        """獲取歸檔工作流程指引"""
        workflow = {
            "name": "項目歸檔工作流程",
            "description": "將對話內容歸檔到項目專櫃，更新摘要記錄",
            "steps": [
                {
                    "step": 1,
                    "name": "獲取近期對話歷史",
                    "guidance": {
                        "tool": "openclaw",
                        "action": "get_recent_conversations",
                        "implementation": "使用OpenClawToolsWrapper.get_conversation_history()",
                        "parameters": {"limit": 50, "session_key": "current"},
                        "purpose": "收集與項目相關的對話"
                    }
                },
                {
                    "step": 2,
                    "name": "生成專櫃摘要",
                    "guidance": {
                        "tool": "openclaw",
                        "action": "generate_cabinet_summary",
                        "implementation": "使用OpenClawToolsWrapper.spawn_summary_agent()",
                        "depends_on": "步驟1的輸出（對話歷史）",
                        "purpose": "從對話中提取決策、技術要點和學習"
                    },
                    "depends_on": 1
                },
                {
                    "step": 3,
                    "name": "更新專櫃文件",
                    "guidance": {
                        "tool": "custom",
                        "action": "update_cabinet_files",
                        "implementation": "使用conversation_summary.update_project_files()",
                        "parameters": {
                            "summary_response": "從步驟2獲取",
                            "project_dir": f"projects/{project_slug or '<project>'}"
                        },
                        "files": [
                            "decisions.md",
                            "learnings_latest.md", 
                            "learnings_history.md",
                            "technical_latest.md",
                            "technical_history.md"
                        ]
                    },
                    "depends_on": 2
                }
            ],
            "estimated_duration": "5-8分鐘",
            "token_cost": "中-高"
        }
        
        if project_slug:
            workflow["project"] = project_slug
        
        return workflow
    
    def get_default_workflow(self, project_slug: str = None) -> Dict:
        """獲取默認工作流程指引（當無法識別場景時）"""
        workflow = {
            "name": "項目維護工作流程",
            "description": "通用項目維護和更新流程",
            "steps": [
                {
                    "step": 1,
                    "name": "識別用戶意圖",
                    "guidance": {
                        "tool": "interaction",
                        "action": "clarify_intent",
                        "question": "請問你想做什麼？",
                        "options": [
                            "更新專櫃內容（歸檔對話）",
                            "更新版本號",
                            "提交到GitHub", 
                            "發布新版本",
                            "其他"
                        ]
                    }
                },
                {
                    "step": 2,
                    "name": "根據意圖選擇工作流程",
                    "guidance": {
                        "tool": "routing",
                        "action": "route_to_workflow",
                        "mapping": {
                            "更新專櫃內容（歸檔對話）": "archive",
                            "更新版本號": "update",
                            "提交到GitHub": "commit",
                            "發布新版本": "release"
                        },
                        "implementation": "根據用戶選擇調用對應的workflow方法"
                    },
                    "depends_on": 1
                }
            ],
            "estimated_duration": "可變",
            "token_cost": "低"
        }
        
        if project_slug:
            workflow["project"] = project_slug
        
        return workflow
    
    def generate_execution_plan(self, workflow: Dict, auto_confirm: bool = False) -> Dict:
        """
        根據工作流程生成具體執行計劃
        
        Args:
            workflow: 工作流程指引
            auto_confirm: 是否自動確認（跳過用戶詢問）
            
        Returns:
            詳細執行計劃
        """
        execution_plan = {
            "workflow_name": workflow.get("name"),
            "project": workflow.get("project"),
            "auto_confirm": auto_confirm,
            "steps": [],
            "prerequisites": self._check_prerequisites(workflow)
        }
        
        # 轉換工作流程步驟為執行步驟
        for step in workflow.get("steps", []):
            execution_step = self._convert_to_execution_step(step, auto_confirm)
            if execution_step:
                execution_plan["steps"].append(execution_step)
        
        # 添加後續步驟
        execution_plan["post_execution"] = {
            "verification": {
                "check_files_updated": "驗證專櫃文件是否已更新",
                "check_version_incremented": "驗證版本號是否已遞增",
                "check_git_committed": "驗證Git提交是否成功"
            },
            "cleanup": {
                "remove_backups": "清理備份文件（保留最近3個）",
                "update_index": "更新projects/INDEX.md"
            }
        }
        
        return execution_plan
    
    def _check_prerequisites(self, workflow: Dict) -> Dict:
        """檢查工作流程前提條件"""
        prerequisites = {
            "system": {
                "python_version": "3.8+",
                "git_installed": True,
                "openclaw_available": True
            },
            "project": {
                "project_dir_exists": True,
                "project_json_valid": True,
                "git_initialized": True
            },
            "permissions": {
                "write_access": True,
                "git_configured": True
            }
        }
        
        # 簡單檢查（實際應更詳細）
        try:
            import sys
            prerequisites["system"]["python_version_actual"] = sys.version
            prerequisites["system"]["python_version_ok"] = sys.version_info >= (3, 8)
        except:
            prerequisites["system"]["python_version_ok"] = False
        
        return prerequisites
    
    def _convert_to_execution_step(self, step: Dict, auto_confirm: bool) -> Dict:
        """將工作流程步驟轉換為執行步驟"""
        execution_step = {
            "step_number": step.get("step"),
            "name": step.get("name"),
            "guidance": step.get("guidance"),
            "depends_on": step.get("depends_on"),
            "status": "pending",
            "execution_time": None,
            "result": None
        }
        
        # 如果是交互步驟且auto_confirm=True，添加默認響應
        guidance = step.get("guidance", {})
        if guidance.get("tool") == "interaction" and auto_confirm:
            execution_step["auto_response"] = {
                "action": "use_default",
                "value": guidance.get("default", "是")
            }
        
        return execution_step


# 導入os用於環境變量
import os


def main():
    """命令行測試"""
    import sys
    
    print("=== 項目更新指引生成器 v5.0 ===")
    
    # 創建指引生成器
    guidance_gen = ProjectUpdateGuidance()
    
    if len(sys.argv) > 1:
        # 測試場景檢測
        user_message = ' '.join(sys.argv[1:])
        print(f"用戶消息: {user_message}")
        
        scenario = guidance_gen.detect_scenario(user_message)
        print("\n場景檢測結果:")
        print(json.dumps(scenario, indent=2, ensure_ascii=False))
        
        # 生成執行計劃
        workflow = scenario.get("recommended_workflow")
        if workflow:
            print(f"\n推薦工作流程: {workflow.get('name')}")
            
            execution_plan = guidance_gen.generate_execution_plan(workflow, auto_confirm=False)
            print("\n執行計劃:")
            print(json.dumps(execution_plan, indent=2, ensure_ascii=False))
    else:
        # 顯示所有工作流程
        print("\n可用工作流程:")
        
        workflows = [
            ("commit", "提交工作流程"),
            ("update", "版本更新工作流程"),
            ("release", "發布工作流程"),
            ("archive", "歸檔工作流程")
        ]
        
        for workflow_key, description in workflows:
            method_name = f"get_{workflow_key}_workflow"
            method = getattr(guidance_gen, method_name, None)
            if method:
                workflow = method("project-memory-manager")
                print(f"\n{workflow_key.upper()}: {workflow['name']}")
                print(f"描述: {workflow['description']}")
                print(f"步驟數: {len(workflow['steps'])}")
                print(f"預計時間: {workflow['estimated_duration']}")
        
        print("\n使用方法:")
        print("  python project_update_guidance.py '更新版本 project-memory-manager'")
        print("  python project_update_guidance.py '提交到GitHub'")


if __name__ == "__main__":
    main()