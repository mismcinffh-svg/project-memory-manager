#!/usr/bin/env python3
"""
指引執行器 - 幫助Agent執行OpenClaw工具調用指引

基於Sergio的審查反饋：
1. OpenClawToolsWrapper只生成指引，缺乏執行層
2. Agent需要幫助將指引轉換為實際工具調用
3. 需要標準化的執行流程和錯誤處理

設計理念：
- 不直接執行工具（技能不應該直接操作）
- 提供「如何執行」的模板和示例
- 標準化的參數轉換和錯誤處理
- 支持所有OpenClaw常用工具
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging

logger = logging.getLogger(__name__)


class GuidanceExecutor:
    """
    指引執行器 - 幫助Agent安全、正確地執行工具指引
    
    這個類不直接調用OpenClaw工具，而是：
    1. 解析指引結構
    2. 生成工具調用示例代碼
    3. 提供執行步驟和注意事項
    4. 處理常見錯誤模式
    """
    
    def __init__(self, workspace_dir: Optional[Path] = None):
        """
        初始化指引執行器
        
        Args:
            workspace_dir: 工作空間目錄（用於路徑驗證）
        """
        self.workspace_dir = workspace_dir
        
    def execute_guidance(self, guidance: Dict) -> Dict:
        """
        執行指引 - 生成完整的工具調用方案
        
        Args:
            guidance: 從OpenClawToolsWrapper獲取的指引
            
        Returns:
            執行方案字典，包含：
            - tool_call: 工具調用示例
            - steps: 執行步驟
            - error_handling: 錯誤處理指南
            - validation: 參數驗證規則
        """
        if not guidance or "tool" not in guidance:
            return self._create_error_scheme("無效的指引格式：缺少'tool'字段")
        
        tool_name = guidance["tool"]
        
        # 根據工具類型生成不同的執行方案
        if tool_name == "sessions_history":
            return self._execute_sessions_history(guidance)
        elif tool_name == "sessions_spawn":
            return self._execute_sessions_spawn(guidance)
        elif tool_name == "exec":
            return self._execute_exec(guidance)
        elif tool_name == "memory_search":
            return self._execute_memory_search(guidance)
        elif tool_name == "memory_get":
            return self._execute_memory_get(guidance)
        elif tool_name == "read":
            return self._execute_read(guidance)
        elif tool_name == "write":
            return self._execute_write(guidance)
        else:
            return self._execute_generic_tool(guidance)
    
    def _execute_sessions_history(self, guidance: Dict) -> Dict:
        """執行sessions_history指引"""
        params = guidance.get("parameters", {})
        
        # 生成工具調用示例
        tool_call = {
            "tool": "sessions_history",
            "sessionKey": params.get("sessionKey", "current"),
            "limit": params.get("limit", 50),
            "includeTools": params.get("includeTools", False)
        }
        
        # 執行步驟
        steps = [
            "1. 驗證會話鍵（sessionKey）是否有效",
            "2. 檢查limit參數（建議1-100之間）",
            "3. 調用sessions_history工具",
            "4. 解析返回的對話歷史",
            "5. 過濾無關消息（系統消息、空內容）",
            "6. 按時間戳排序（如果需要）"
        ]
        
        # 錯誤處理指南
        error_handling = {
            "common_errors": [
                {
                    "error": "Session history visibility is restricted",
                    "cause": "tools.sessions.visibility配置不正確",
                    "solution": "設置tools.sessions.visibility=all"
                },
                {
                    "error": "Session not found",
                    "cause": "sessionKey不存在或已過期",
                    "solution": "使用'current'或有效的sessionKey"
                }
            ],
            "fallback_strategy": "如果無法獲取歷史，使用最近10條對話作為替代"
        }
        
        # 參數驗證規則
        validation = {
            "sessionKey": {
                "type": "string",
                "required": True,
                "default": "current",
                "allowed_values": ["current", "agent:sc:main", "agent:coder:subagent:*"]
            },
            "limit": {
                "type": "integer",
                "required": False,
                "default": 50,
                "min": 1,
                "max": 1000
            },
            "includeTools": {
                "type": "boolean",
                "required": False,
                "default": False
            }
        }
        
        return {
            "tool": "sessions_history",
            "tool_call_example": tool_call,
            "description": guidance.get("description", "獲取對話歷史"),
            "execution_steps": steps,
            "error_handling": error_handling,
            "parameter_validation": validation,
            "expected_output_structure": {
                "type": "list",
                "items": {
                    "role": "user|assistant|system",
                    "content": "string",
                    "timestamp": "ISO timestamp"
                }
            }
        }
    
    def _execute_sessions_spawn(self, guidance: Dict) -> Dict:
        """執行sessions_spawn指引"""
        params = guidance.get("parameters", {})
        
        # 生成工具調用示例
        tool_call = {
            "tool": "sessions_spawn",
            "task": params.get("task", ""),
            "label": params.get("label", "summary-generation"),
            "model": params.get("model", "deepseek/deepseek-chat"),
            "runtime": params.get("runtime", "subagent"),
            "timeoutSeconds": params.get("timeoutSeconds", 300)
        }
        
        # 清理task參數（避免過長）
        task = tool_call["task"]
        if len(task) > 1000:
            task = task[:997] + "..."
            tool_call["task"] = task
        
        # 執行步驟
        steps = [
            "1. 準備任務提示（task），確保清晰明確",
            "2. 設置合適的標籤（label）用於追蹤",
            "3. 選擇性價比高的模型（如deepseek-chat）",
            "4. 設置合理的超時時間（timeoutSeconds）",
            "5. 調用sessions_spawn工具",
            "6. 監聽子會話完成事件",
            "7. 解析子會話的輸出結果"
        ]
        
        # 錯誤處理指南
        error_handling = {
            "common_errors": [
                {
                    "error": "Task too long",
                    "cause": "task參數超過令牌限制",
                    "solution": "簡化任務描述，限制在1000字符內"
                },
                {
                    "error": "Model not available",
                    "cause": "指定的模型不可用",
                    "solution": "使用默認模型或檢查模型配置"
                }
            ],
            "fallback_strategy": "如果spawn失敗，直接生成簡要摘要"
        }
        
        # 參數驗證規則
        validation = {
            "task": {
                "type": "string",
                "required": True,
                "max_length": 2000,
                "min_length": 10
            },
            "label": {
                "type": "string",
                "required": False,
                "default": "summary-generation",
                "pattern": r"^[a-zA-Z0-9_-]+$"
            },
            "model": {
                "type": "string",
                "required": False,
                "default": "deepseek/deepseek-chat",
                "allowed_values": ["deepseek/deepseek-chat", "deepseek/deepseek-reasoner", "bigmodel/GLM-5"]
            },
            "timeoutSeconds": {
                "type": "integer",
                "required": False,
                "default": 300,
                "min": 30,
                "max": 3600
            }
        }
        
        return {
            "tool": "sessions_spawn",
            "tool_call_example": tool_call,
            "description": guidance.get("description", "啟動子會話生成摘要"),
            "execution_steps": steps,
            "error_handling": error_handling,
            "parameter_validation": validation,
            "expected_output_structure": {
                "type": "object",
                "properties": {
                    "status": "accepted|completed|error",
                    "childSessionKey": "string",
                    "runId": "string"
                }
            }
        }
    
    def _execute_exec(self, guidance: Dict) -> Dict:
        """執行exec指引（特別注意安全性）"""
        params = guidance.get("parameters", {})
        
        # 安全檢查：確保來自GitToolWrapper的指引
        source = guidance.get("source", "")
        if source != "GitToolWrapper":
            logger.warning("exec指引未標記來源，需要額外安全檢查")
        
        # 生成工具調用示例
        tool_call = {
            "tool": "exec",
            "command": params.get("command", ""),
            "workdir": params.get("workdir", str(self.workspace_dir) if self.workspace_dir else None),
            "timeout": params.get("timeout", 30)
        }
        
        # 執行步驟（特別強調安全性）
        steps = [
            "1. ⚠️ 安全檢查：驗證命令是否來自可信來源（GitToolWrapper）",
            "2. ⚠️ 路徑檢查：確保workdir在workspace範圍內",
            "3. ⚠️ 命令檢查：避免危險命令（rm -rf, wget | sh等）",
            "4. 設置合適的超時時間（避免長時間阻塞）",
            "5. 調用exec工具",
            "6. 檢查返回碼（returncode != 0表示失敗）",
            "7. 解析stdout和stderr輸出"
        ]
        
        # 錯誤處理指南
        error_handling = {
            "common_errors": [
                {
                    "error": "Command execution failed",
                    "cause": "命令不存在或權限不足",
                    "solution": "檢查命令拼寫和執行權限"
                },
                {
                    "error": "Timeout expired",
                    "cause": "命令執行時間過長",
                    "solution": "增加timeout或優化命令"
                },
                {
                    "error": "Permission denied",
                    "cause": "沒有文件系統訪問權限",
                    "solution": "檢查路徑權限或使用沙盒模式"
                }
            ],
            "fallback_strategy": "如果exec失敗，記錄錯誤並跳過該步驟"
        }
        
        # 參數驗證規則（嚴格）
        validation = {
            "command": {
                "type": "string",
                "required": True,
                "security_rules": [
                    "不允許包含'rm -rf'",
                    "不允許包含'wget | sh'或'curl | bash'",
                    "不允許包含'chmod 777'",
                    "只允許已知安全的Git命令"
                ]
            },
            "workdir": {
                "type": "string",
                "required": False,
                "path_validation": "必須在workspace範圍內"
            },
            "timeout": {
                "type": "integer",
                "required": False,
                "default": 30,
                "min": 1,
                "max": 300
            }
        }
        
        return {
            "tool": "exec",
            "tool_call_example": tool_call,
            "description": guidance.get("description", "執行系統命令"),
            "execution_steps": steps,
            "error_handling": error_handling,
            "parameter_validation": validation,
            "security_warning": "⚠️ 這是高風險操作，必須進行嚴格的安全檢查",
            "expected_output_structure": {
                "type": "object",
                "properties": {
                    "returncode": "integer (0=成功)",
                    "stdout": "string",
                    "stderr": "string"
                }
            }
        }
    
    def _execute_memory_search(self, guidance: Dict) -> Dict:
        """執行memory_search指引"""
        params = guidance.get("parameters", {})
        
        tool_call = {
            "tool": "memory_search",
            "query": params.get("query", ""),
            "maxResults": params.get("maxResults", 10),
            "minScore": params.get("minScore", 0.3)
        }
        
        steps = [
            "1. 準備搜索查詢（query），使用具體關鍵詞",
            "2. 設置合理的結果數量（maxResults）",
            "3. 設置最小匹配分數（minScore）過濾低質量結果",
            "4. 調用memory_search工具",
            "5. 解析返回的記憶片段",
            "6. 按相關性排序結果"
        ]
        
        return {
            "tool": "memory_search",
            "tool_call_example": tool_call,
            "description": guidance.get("description", "搜索記憶"),
            "execution_steps": steps,
            "expected_output_structure": {
                "type": "list",
                "items": {
                    "path": "文件路徑",
                    "lines": "相關行號",
                    "content": "匹配內容",
                    "score": "匹配分數"
                }
            }
        }
    
    def _execute_memory_get(self, guidance: Dict) -> Dict:
        """執行memory_get指引"""
        params = guidance.get("parameters", {})
        
        tool_call = {
            "tool": "memory_get",
            "path": params.get("path", ""),
            "from": params.get("from", 1),
            "lines": params.get("lines", 50)
        }
        
        steps = [
            "1. 驗證路徑（path）是否在允許範圍內",
            "2. 設置起始行號（from），1-based索引",
            "3. 設置要讀取的行數（lines）",
            "4. 調用memory_get工具",
            "5. 處理返回的文本內容"
        ]
        
        return {
            "tool": "memory_get",
            "tool_call_example": tool_call,
            "description": guidance.get("description", "讀取記憶文件"),
            "execution_steps": steps,
            "expected_output_structure": {
                "type": "string",
                "note": "文件內容，可能被截斷"
            }
        }
    
    def _execute_read(self, guidance: Dict) -> Dict:
        """執行read指引"""
        params = guidance.get("parameters", {})
        
        tool_call = {
            "tool": "read",
            "path": params.get("path", ""),
            "offset": params.get("offset"),
            "limit": params.get("limit")
        }
        
        steps = [
            "1. 驗證文件路徑是否安全",
            "2. 設置偏移量（offset，可選）",
            "3. 設置行數限制（limit，可選）",
            "4. 調用read工具",
            "5. 處理返回的內容（可能是文本或圖像）"
        ]
        
        return {
            "tool": "read",
            "tool_call_example": tool_call,
            "description": guidance.get("description", "讀取文件"),
            "execution_steps": steps,
            "expected_output_structure": {
                "type": "string|object",
                "note": "文件內容或圖像數據"
            }
        }
    
    def _execute_write(self, guidance: Dict) -> Dict:
        """執行write指引"""
        params = guidance.get("parameters", {})
        
        tool_call = {
            "tool": "write",
            "path": params.get("path", ""),
            "content": params.get("content", "")
        }
        
        steps = [
            "1. ⚠️ 安全檢查：驗證路徑是否在workspace範圍內",
            "2. 準備要寫入的內容（content）",
            "3. 確保目錄存在（自動創建父目錄）",
            "4. 調用write工具",
            "5. 驗證寫入是否成功"
        ]
        
        return {
            "tool": "write",
            "tool_call_example": tool_call,
            "description": guidance.get("description", "寫入文件"),
            "execution_steps": steps,
            "security_warning": "⚠️ 寫入操作可能覆蓋現有文件",
            "expected_output_structure": {
                "type": "boolean",
                "note": "成功返回true，失敗返回false"
            }
        }
    
    def _execute_generic_tool(self, guidance: Dict) -> Dict:
        """執行通用工具指引"""
        tool_name = guidance["tool"]
        params = guidance.get("parameters", {})
        
        tool_call = {"tool": tool_name, **params}
        
        steps = [
            f"1. 驗證{tool_name}工具是否可用",
            "2. 檢查所有必要參數",
            "3. 調用工具",
            "4. 處理工具返回值"
        ]
        
        return {
            "tool": tool_name,
            "tool_call_example": tool_call,
            "description": guidance.get("description", f"執行{tool_name}工具"),
            "execution_steps": steps,
            "note": "這是通用執行方案，可能需要根據具體工具調整"
        }
    
    def _create_error_scheme(self, error_msg: str) -> Dict:
        """創建錯誤執行方案"""
        return {
            "error": True,
            "error_message": error_msg,
            "execution_steps": [
                "1. 檢查指引格式是否符合規範",
                "2. 確保包含'tool'字段",
                "3. 重新生成有效的指引"
            ],
            "fallback_strategy": "跳過當前指引，繼續執行其他步驟"
        }
    
    def generate_execution_script(self, guidance: Dict, language: str = "python") -> str:
        """
        生成執行腳本（示例代碼）
        
        Args:
            guidance: 指引字典
            language: 輸出語言（python, javascript, json）
            
        Returns:
            示例代碼字符串
        """
        if language == "python":
            return self._generate_python_script(guidance)
        elif language == "json":
            return self._generate_json_script(guidance)
        else:
            return self._generate_generic_script(guidance)
    
    def _generate_python_script(self, guidance: Dict) -> str:
        """生成Python示例代碼"""
        scheme = self.execute_guidance(guidance)
        
        if scheme.get("error"):
            return f"# 錯誤: {scheme['error_message']}"
        
        tool_call = scheme["tool_call_example"]
        tool_name = tool_call["tool"]
        
        code = f'''# 執行指引：{scheme.get('description', '')}
# 工具：{tool_name}

# 1. 準備參數
params = {json.dumps(tool_call, indent=2, ensure_ascii=False)}

# 2. 調用工具（在OpenClaw Agent中）
# 注意：實際調用方式取決於Agent的實現
# 示例（假設有call_tool函數）：
try:
    result = call_tool("{tool_name}", **params)
    
    # 3. 處理結果
    if "{tool_name}" == "sessions_history":
        conversations = result  # 應該是對話列表
        print(f"獲取到{{len(conversations)}}條對話")
        
    elif "{tool_name}" == "exec":
        if result.get("returncode") == 0:
            print(f"執行成功: {{result.get('stdout', '')}}")
        else:
            print(f"執行失敗: {{result.get('stderr', '')}}")
            
    # ... 其他工具處理邏輯
    
except Exception as e:
    print(f"工具調用失敗: {{e}}")
    # 執行降級策略
    
# 4. 後續處理
# 根據指引中的processing_instructions進行後續操作
'''
        
        return code
    
    def _generate_json_script(self, guidance: Dict) -> str:
        """生成JSON示例"""
        scheme = self.execute_guidance(guidance)
        return json.dumps(scheme, indent=2, ensure_ascii=False)
    
    def _generate_generic_script(self, guidance: Dict) -> str:
        """生成通用示例"""
        scheme = self.execute_guidance(guidance)
        
        output = f"工具: {scheme.get('tool', 'unknown')}\n"
        output += f"描述: {scheme.get('description', '')}\n\n"
        output += "執行步驟:\n"
        
        for i, step in enumerate(scheme.get('execution_steps', []), 1):
            output += f"  {i}. {step}\n"
        
        return output


def test_guidance_executor():
    """測試指引執行器"""
    print("=== 測試GuidanceExecutor ===")
    
    executor = GuidanceExecutor()
    
    # 測試sessions_history指引
    history_guidance = {
        "tool": "sessions_history",
        "parameters": {
            "sessionKey": "current",
            "limit": 20,
            "includeTools": False
        },
        "description": "獲取當前會話的對話歷史"
    }
    
    scheme = executor.execute_guidance(history_guidance)
    print(f"1. sessions_history執行方案: ✅")
    print(f"   工具: {scheme.get('tool')}")
    print(f"   步驟數: {len(scheme.get('execution_steps', []))}")
    
    # 測試exec指引
    exec_guidance = {
        "tool": "exec",
        "source": "GitToolWrapper",
        "parameters": {
            "command": "git status",
            "workdir": "/tmp",
            "timeout": 10
        },
        "description": "檢查Git狀態"
    }
    
    scheme = executor.execute_guidance(exec_guidance)
    print(f"\n2. exec執行方案: ✅")
    print(f"   安全警告: {'有' if 'security_warning' in scheme else '無'}")
    
    # 測試生成Python代碼
    python_code = executor.generate_execution_script(history_guidance, "python")
    print(f"\n3. Python示例代碼生成: ✅")
    print(f"   代碼行數: {len(python_code.split(chr(10)))}")
    
    print("\n🎯 GuidanceExecutor測試完成")


if __name__ == "__main__":
    test_guidance_executor()