#!/usr/bin/env python3
"""
OpenClaw工具封裝 - 提供真實的工具調用指引

基於Sergio的安全審查要求：
1. 移除所有模擬數據（mock data）
2. 提供真實的OpenClaw工具調用指引
3. 技能提供指引，Agent執行工具

設計理念：
- 技能不直接操作，而是提供「如何操作」的指引
- 所有與OpenClaw系統的交互都通過工具調用
- 保持清晰的責任分離：技能指導，Agent執行
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import logging

logger = logging.getLogger(__name__)


class OpenClawToolsWrapper:
    """OpenClaw工具封裝器"""
    
    def __init__(self, project_slug: str = None):
        """
        初始化OpenClaw工具封裝器
        
        Args:
            project_slug: 項目slug（可選，用於上下文）
        """
        self.project_slug = project_slug
        
    def get_conversation_history(self, 
                                session_key: str = "current",
                                limit: int = 50,
                                include_tools: bool = False) -> Dict:
        """
        獲取對話歷史指引
        
        實際應該調用 sessions_history 工具：
        sessions_history(sessionKey=session_key, limit=limit, includeTools=include_tools)
        
        Args:
            session_key: 會話鍵，默認"current"（當前會話）
            limit: 獲取的條數
            include_tools: 是否包含工具調用
            
        Returns:
            工具調用指引字典
        """
        description = f"獲取會話歷史（{limit}條）"
        if self.project_slug:
            description += f" - 項目: {self.project_slug}"
        
        guidance = {
            "tool": "sessions_history",
            "action": "get_conversation_history",
            "parameters": {
                "sessionKey": session_key,
                "limit": limit,
                "includeTools": include_tools
            },
            "description": description,
            "expected_output": {
                "type": "list",
                "structure": "包含role, content, timestamp的消息列表",
                "usage": "用於對話摘要生成"
            },
            "processing_instructions": [
                "1. 調用sessions_history工具獲取真實對話歷史",
                "2. 過濾掉系統消息和無關對話",
                "3. 提取與項目相關的對話片段",
                "4. 保留時間戳和角色信息"
            ]
        }
        
        return guidance
    
    def spawn_summary_agent(self, 
                           project_name: str,
                           conversations: List[Dict],
                           since_time: Union[datetime, str]) -> Dict:
        """
        生成摘要Agent指引
        
        實際應該調用 sessions_spawn 工具啟動sub-agent生成摘要：
        sessions_spawn(task=prompt, label="summary-generation", model="deepseek-chat", ...)
        
        Args:
            project_name: 項目名稱
            conversations: 對話歷史（應從sessions_history獲取）
            since_time: 上次摘要時間
            
        Returns:
            工具調用指引字典
        """
        # 處理since_time參數（支持datetime對象或ISO格式字符串）
        if isinstance(since_time, str):
            try:
                since_time = datetime.fromisoformat(since_time.replace('Z', '+00:00'))
            except ValueError:
                # 如果解析失敗，使用默認時間
                since_time = datetime.fromisoformat("2026-01-01T00:00:00+00:00")
                logger.warning(f"無法解析since_time字符串: {since_time}, 使用默認時間")
        
        # 構建prompt（與原conversation_summary.py相同，但作為指引的一部分）
        conv_text = ""
        for i, conv in enumerate(conversations[:10], 1):  # 限制前10條以免過長
            role = conv.get('role', 'unknown')
            content = self._extract_text_content(conv.get('content', ''))
            timestamp = conv.get('timestamp', '')
            
            time_str = ""
            if timestamp:
                try:
                    ts = int(timestamp) / 1000
                    dt = datetime.fromtimestamp(ts)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            conv_text += f"{i}. [{role}] {time_str}\n"
            conv_text += f"   {content[:150]}{'...' if len(content) > 150 else ''}\n\n"
        
        prompt = f"""請根據以下對話，為項目「{project_name}」生成專櫃摘要。

## 項目信息
- 項目名稱：{project_name}
- 最後摘要更新：{since_time.strftime('%Y-%m-%d %H:%M')}
- 對話條數：{len(conversations)}

## 對話歷史（前10條）
{conv_text}

## 摘要要求
請生成三個部分的內容：

### 1. decisions.md 更新（決策記錄）
格式：
```
- [YYYY-MM-DD HH:MM] 決策：[具體決策內容]
  原因：[為什麼做出這個決策]
  考慮選項：[考慮了哪些選項，為什麼選擇這個]
  參考對話：[相關對話編號，如#1,#3]
```

### 2. technical.md 更新（技術要點）
格式：
```
- [技術模塊/功能]：[技術實現要點]
  實現方式：[具體實現方法]
  技術選擇：[為什麼選擇這個技術方案]
  替代方案：[考慮過的其他方案]
  參考對話：[相關對話編號]
```

### 3. learnings.md 更新（學習總結）
格式：
```
- [洞察/學習]：[學到了什麼]
  應用場景：[這個學習可以應用到什麼場景]
  經驗教訓：[從中得到的經驗教訓]
  參考對話：[相關對話編號]
```

## 輸出格式
請直接輸出三個部分的內容，用分隔線分開：
```
--- decisions.md ---
[decisions.md內容]

--- technical.md ---
[technical.md內容]

--- learnings.md ---
[learnings.md內容]
```

注意：內容要簡潔、有價值，便於未來查閱。"""
        
        guidance = {
            "tool": "sessions_spawn",
            "action": "generate_project_summary",
            "parameters": {
                "task": prompt,
                "label": f"summary-{project_name[:20]}",
                "runtime": "subagent",
                "agentId": "coder",  # 使用coder agent生成摘要
                "model": "deepseek/deepseek-chat",  # 成本控制
                "thinking": "off"
            },
            "description": f"生成項目摘要 - {project_name}",
            "prompt_preview": prompt[:500] + "..." if len(prompt) > 500 else prompt,
            "expected_output": {
                "type": "text",
                "format": "三個部分用分隔線分開",
                "sections": ["decisions.md", "technical.md", "learnings.md"]
            },
            "post_processing": {
                "parse_function": "conversation_summary.parse_summary_response",
                "update_function": "conversation_summary.update_project_files"
            }
        }
        
        return guidance
    
    def get_memory_search(self, query: str, max_results: int = 5) -> Dict:
        """
        獲取記憶搜索指引
        
        實際應該調用 memory_search 工具：
        memory_search(query=query, maxResults=max_results)
        """
        guidance = {
            "tool": "memory_search",
            "action": "search_project_memory",
            "parameters": {
                "query": query,
                "maxResults": max_results
            },
            "description": f"搜索項目記憶: {query[:50]}...",
            "expected_usage": "查找相關的決策、技術細節或學習記錄"
        }
        
        return guidance
    
    def get_memory_get(self, path: str, lines: int = 50) -> Dict:
        """
        獲取特定記憶文件內容指引
        
        實際應該調用 memory_get 工具：
        memory_get(path=path, lines=lines)
        """
        guidance = {
            "tool": "memory_get",
            "action": "read_memory_file",
            "parameters": {
                "path": path,
                "lines": lines
            },
            "description": f"讀取記憶文件: {Path(path).name}",
            "safety_check": "路徑應在workspace範圍內"
        }
        
        return guidance
    
    def execute_safe_command(self, command: str, workdir: str = None) -> Dict:
        """
        執行安全命令指引
        
        實際應該調用 exec 工具：
        exec(command=command, workdir=workdir)
        
        注意：應先使用security模塊驗證命令安全性
        """
        guidance = {
            "tool": "exec",
            "action": "run_safe_command",
            "parameters": {
                "command": command,
                "workdir": workdir or ".",
                "security": "驗證命令安全性後執行"
            },
            "description": f"執行命令: {command[:100]}...",
            "safety_requirements": [
                "使用security.sanitize_command驗證命令",
                "避免危險操作（rm -rf, 格式化等）",
                "路徑應在workspace範圍內"
            ]
        }
        
        return guidance
    
    def create_workflow_guidance(self, 
                                project_slug: str,
                                update_summary: bool = True) -> Dict:
        """
        創建完整工作流程指引
        
        將多個工具調用組合成一個工作流程
        """
        workflow = {
            "name": f"項目更新工作流程 - {project_slug}",
            "project": project_slug,
            "steps": [],
            "estimated_tokens": 0,
            "expected_duration": "5-10分鐘"
        }
        
        # 步驟1：獲取對話歷史
        step1 = {
            "step": 1,
            "name": "獲取對話歷史",
            "guidance": self.get_conversation_history(limit=30),
            "purpose": "收集最近的項目相關對話"
        }
        workflow["steps"].append(step1)
        
        if update_summary:
            # 步驟2：生成摘要（需要步驟1的結果）
            step2 = {
                "step": 2,
                "name": "生成項目摘要",
                "guidance": {
                    "note": "此步驟需要步驟1的結果（對話歷史）",
                    "implementation": "在獲取對話歷史後，調用spawn_summary_agent生成摘要"
                },
                "depends_on": 1,
                "purpose": "從對話中提取決策、技術要點和學習"
            }
            workflow["steps"].append(step2)
            
            # 步驟3：更新專櫃文件（需要步驟2的結果）
            step3 = {
                "step": 3,
                "name": "更新專櫃文件",
                "guidance": {
                    "tool": "custom",
                    "action": "update_cabinet_files",
                    "implementation": "使用conversation_summary.parse_summary_response和update_project_files",
                    "parameters": {
                        "summary_response": "來自步驟2的輸出",
                        "project_dir": f"projects/{project_slug}"
                    }
                },
                "depends_on": 2,
                "purpose": "將摘要保存到項目專櫃文件"
            }
            workflow["steps"].append(step3)
        
        # 步驟4：版本管理
        step4 = {
            "step": 4 if update_summary else 2,
            "name": "版本更新",
            "guidance": {
                "tool": "custom",
                "action": "version_management",
                "implementation": "使用version_manager進行版本遞增和CHANGELOG更新",
                "note": "此部分應使用GitToolWrapper進行安全的Git操作"
            },
            "purpose": "遞增版本號，更新CHANGELOG"
        }
        workflow["steps"].append(step4)
        
        # 步驟5：Git操作
        step5 = {
            "step": 5 if update_summary else 3,
            "name": "Git同步",
            "guidance": {
                "tool": "git",
                "action": "commit_and_push",
                "implementation": "使用GitToolWrapper進行安全的git add, commit, push操作",
                "commands": [
                    "git add .",
                    f"git commit -m 'chore: update {project_slug}'",
                    "git push origin main"
                ]
            },
            "depends_on": 4 if update_summary else 2,
            "purpose": "將更改同步到GitHub"
        }
        workflow["steps"].append(step5)
        
        return workflow
    
    def _extract_text_content(self, content) -> str:
        """從OpenClaw消息內容中提取文本（與conversation_summary.py保持一致）"""
        if isinstance(content, str):
            return content
        
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                    elif 'text' in item:
                        text_parts.append(item['text'])
                elif isinstance(item, str):
                    text_parts.append(item)
            return ' '.join(text_parts)
        
        return str(content)


def migrate_from_mock_data_example():
    """從模擬數據遷移示例"""
    print("=== 從模擬數據遷移示例 ===")
    
    # 舊代碼示例（使用模擬數據）
    old_code = '''
def simulate_conversation_history(self, project_slug: str) -> List[Dict]:
    """模擬對話歷史（實際應從OpenClaw sessions_history獲取）"""
    # 這裡模擬一些對話
    sample_conversations = [
        {
            'role': 'user',
            'content': f'我準備commit {project_slug}上GitHub',
            'timestamp': str(ten_min_ago)
        },
        # ... 更多模擬對話
    ]
    return sample_conversations
    
def run_summary_update(self, project_dir: str, conversations: List[Dict]) -> bool:
    """運行摘要更新（模擬sessions_spawn）"""
    # 模擬sub-agent的回應
    mock_response = \"\"\"--- decisions.md ---
    ... 模擬內容 ...
    \"\"\"
    # 解析模擬回應
    sections = summary.parse_summary_response(mock_response)
    '''
    
    print("舊代碼（使用模擬數據）:")
    print(old_code[:500] + "...")
    print()
    
    # 新代碼示例（使用OpenClawToolsWrapper）
    print("新代碼（使用OpenClawToolsWrapper）：")
    print('''
# 初始化工具封裝器
tools = OpenClawToolsWrapper(project_slug="project-memory-manager")

# 1. 獲取真實對話歷史指引
history_guidance = tools.get_conversation_history(limit=30)
print("對話歷史指引:", json.dumps(history_guidance, indent=2))

# 2. 生成摘要指引（假設已獲取真實對話）
# 注意：實際應先執行步驟1，獲取真實對話後再執行步驟2
summary_guidance = tools.spawn_summary_agent(
    project_name="Project Memory Manager",
    conversations=real_conversations,  # 從sessions_history獲取的真實數據
    since_time=last_summary_time
)
print("摘要生成指引:", json.dumps(summary_guidance, indent=2))

# 3. 完整工作流程指引
workflow = tools.create_workflow_guidance(
    project_slug="project-memory-manager",
    update_summary=True
)
print("完整工作流程:", json.dumps(workflow, indent=2))
''')
    
    print("=== 遷移關鍵點 ===")
    print("1. 移除所有 simulate_* 函數")
    print("2. 將 mock data 替換為工具調用指引")
    print("3. 技能不再直接操作，而是提供操作指引")
    print("4. Agent負責執行指引中的工具調用")


if __name__ == "__main__":
    # 測試OpenClawToolsWrapper
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--migrate":
        migrate_from_mock_data_example()
        sys.exit(0)
    
    print("=== OpenClawToolsWrapper 測試 ===")
    
    tools = OpenClawToolsWrapper("test-project")
    
    print("1. 對話歷史指引:")
    guidance = tools.get_conversation_history(limit=20)
    print(json.dumps(guidance, indent=2, ensure_ascii=False))
    print()
    
    print("2. 記憶搜索指引:")
    guidance = tools.get_memory_search("項目記憶管理", max_results=3)
    print(json.dumps(guidance, indent=2, ensure_ascii=False))
    print()
    
    print("3. 完整工作流程指引:")
    workflow = tools.create_workflow_guidance(
        project_slug="project-memory-manager",
        update_summary=True
    )
    print(json.dumps(workflow, indent=2, ensure_ascii=False))
    
    print("\n=== 測試完成 ===")
    print("\n使用方法:")
    print("  python openclaw_tools_wrapper.py              # 運行測試")
    print("  python openclaw_tools_wrapper.py --migrate    # 查看遷移示例")