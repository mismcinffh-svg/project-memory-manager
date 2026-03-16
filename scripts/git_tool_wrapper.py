#!/usr/bin/env python3
"""
Git工具封裝 - 提供安全的Git操作接口

基於Sergio的安全審查要求：
1. 移除所有直接subprocess調用
2. 提供OpenClaw exec工具調用指引
3. 確保路徑和命令安全

設計理念：
- 不直接執行命令，而是生成Agent可執行的指引
- 技能提供「工具箱」，Agent執行工具
- 向後兼容現有代碼結構
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class GitToolWrapper:
    """Git工具封裝器"""
    
    def __init__(self, project_dir: Path, use_openclaw_tools: bool = True):
        """
        初始化Git工具封裝器
        
        Args:
            project_dir: 項目目錄
            use_openclaw_tools: 是否生成OpenClaw工具調用指引（True）或直接執行（False）
        """
        self.project_dir = Path(project_dir).resolve()
        self.use_openclaw_tools = use_openclaw_tools
        
        # 安全驗證器
        try:
            from security import SecurityValidator
            self.validator = SecurityValidator(self.project_dir)
            self.security_enabled = True
        except ImportError:
            self.validator = None
            self.security_enabled = False
            logger.warning("安全模塊未找到，使用基本驗證")
    
    def _validate_command(self, command: List[str]) -> Tuple[bool, str]:
        """驗證Git命令安全性"""
        if not command or command[0] != "git":
            return False, "命令必須以git開頭"
        
        # 危險Git命令黑名單
        dangerous_git_commands = [
            r'git\s+clean\s+-fdx',
            r'git\s+reset\s+--hard',
            r'git\s+push\s+--force',
            r'git\s+push\s+-f',
            r'git\s+filter-branch',
            r'git\s+update-ref\s+-d',
        ]
        
        cmd_str = ' '.join(command)
        for pattern in dangerous_git_commands:
            if re.search(pattern, cmd_str, re.IGNORECASE):
                return False, f"危險的Git命令: {pattern}"
        
        # 路徑驗證：確保操作在項目目錄內
        for arg in command[1:]:
            if arg.startswith('/') or '..' in arg:
                # 可能是路徑參數，需要驗證
                if self.security_enabled and self.validator:
                    test_path = (self.project_dir / arg).resolve()
                    is_safe, error = self.validator.validate_path(test_path)
                    if not is_safe:
                        return False, f"不安全的路徑參數: {error}"
        
        return True, ""
    
    def _generate_openclaw_guidance(self, command: List[str], description: str = "") -> Dict:
        """生成OpenClaw exec工具調用指引
        
        返回結構化指引，Agent可根據此指引調用exec工具
        """
        cmd_str = ' '.join(command)
        
        guidance = {
            "tool": "exec",
            "action": "run_git_command",
            "parameters": {
                "command": cmd_str,
                "workdir": str(self.project_dir),
                "description": description or f"執行Git命令: {cmd_str}"
            },
            "safety_check": {
                "validated": True,
                "checks_passed": True,
                "notes": "已通過Git命令安全性驗證"
            },
            "fallback_instructions": f"如果exec工具不可用，請手動執行: cd {self.project_dir} && {cmd_str}"
        }
        
        return guidance
    
    def _run_direct(self, command: List[str]) -> Tuple[bool, str, Optional[str]]:
        """直接執行命令（向後兼容模式）"""
        try:
            import subprocess
            
            # 安全性驗證
            is_valid, error = self._validate_command(command)
            if not is_valid:
                return False, "", f"命令驗證失敗: {error}"
            
            # 執行命令
            result = subprocess.run(
                command,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                return True, result.stdout, None
            else:
                return False, result.stderr, f"命令失敗 (code: {result.returncode})"
                
        except Exception as e:
            logger.error(f"執行命令失敗: {e}")
            return False, "", str(e)
    
    def execute(self, command: List[str], description: str = "") -> Union[Dict, Tuple[bool, str, Optional[str]]]:
        """執行Git命令
        
        Args:
            command: Git命令列表，如 ["git", "add", "."]
            description: 命令描述
            
        Returns:
            如果use_openclaw_tools=True: 返回指引字典
            如果use_openclaw_tools=False: 返回(是否成功, 輸出, 錯誤信息)
        """
        # 驗證命令
        is_valid, error = self._validate_command(command)
        if not is_valid:
            if self.use_openclaw_tools:
                return {
                    "tool": "error",
                    "error": f"命令驗證失敗: {error}",
                    "recommendation": "請檢查命令安全性"
                }
            else:
                return False, "", f"命令驗證失敗: {error}"
        
        if self.use_openclaw_tools:
            # 生成OpenClaw工具調用指引
            return self._generate_openclaw_guidance(command, description)
        else:
            # 直接執行（向後兼容）
            return self._run_direct(command)
    
    # 常用Git操作的便捷方法
    
    def git_add(self, files: str = ".") -> Union[Dict, Tuple[bool, str, Optional[str]]]:
        """git add操作"""
        if files == ".":
            description = "添加所有更改的文件到暫存區"
        else:
            description = f"添加文件到暫存區: {files}"
        
        return self.execute(["git", "add", files], description)
    
    def git_commit(self, message: str) -> Union[Dict, Tuple[bool, str, Optional[str]]]:
        """git commit操作"""
        # 清理提交訊息（移除潛在危險字符）
        safe_message = re.sub(r'[`$|;&]', '', message[:200])
        
        return self.execute(
            ["git", "commit", "-m", safe_message],
            f"提交更改: {safe_message}"
        )
    
    def git_status(self) -> Union[Dict, Tuple[bool, str, Optional[str]]]:
        """git status操作"""
        return self.execute(["git", "status"], "檢查Git狀態")
    
    def git_push(self, remote: str = "origin", branch: str = "main") -> Union[Dict, Tuple[bool, str, Optional[str]]]:
        """git push操作"""
        return self.execute(
            ["git", "push", remote, branch],
            f"推送分支到遠端: {remote}/{branch}"
        )
    
    def git_tag(self, tag_name: str, message: str = "") -> Union[Dict, Tuple[bool, str, Optional[str]]]:
        """git tag操作"""
        if message:
            return self.execute(
                ["git", "tag", "-a", tag_name, "-m", message],
                f"創建帶註釋的標籤: {tag_name}"
            )
        else:
            return self.execute(
                ["git", "tag", tag_name],
                f"創建輕量標籤: {tag_name}"
            )
    
    def git_log(self, count: int = 5) -> Union[Dict, Tuple[bool, str, Optional[str]]]:
        """git log操作"""
        return self.execute(
            ["git", "log", f"--oneline", "-n", str(count)],
            f"查看最近{count}條提交記錄"
        )
    
    def get_remote_url(self) -> Optional[str]:
        """獲取遠端倉庫URL"""
        if self.use_openclaw_tools:
            # 生成指引
            guidance = self.execute(["git", "remote", "get-url", "origin"], "獲取遠端倉庫URL")
            return guidance  # Agent需要執行此指引
        else:
            # 直接執行
            success, output, error = self._run_direct(["git", "remote", "get-url", "origin"])
            if success:
                return output.strip()
            return None
    
    def check_remote_exists(self) -> bool:
        """檢查是否已設置遠端倉庫"""
        if self.use_openclaw_tools:
            # 生成檢查指引
            guidance = self.execute(["git", "remote"], "檢查遠端倉庫")
            return guidance  # Agent需要執行並解析結果
        else:
            # 直接執行
            success, output, error = self._run_direct(["git", "remote"])
            if success:
                return "origin" in output
            return False
    
    def batch_execute(self, commands: List[List[str]], 
                     descriptions: List[str] = None) -> List[Union[Dict, Tuple[bool, str, Optional[str]]]]:
        """批量執行多個命令"""
        results = []
        
        for i, cmd in enumerate(commands):
            desc = descriptions[i] if descriptions and i < len(descriptions) else ""
            result = self.execute(cmd, desc)
            results.append(result)
            
            # 如果不是OpenClaw模式且命令失敗，可選停止
            if not self.use_openclaw_tools and not result[0]:
                logger.warning(f"命令失敗，停止批量執行: {cmd}")
                break
        
        return results


def migrate_old_code_example():
    """舊代碼遷移示例"""
    print("=== 舊代碼遷移示例 ===")
    
    # 舊代碼示例（使用subprocess）
    old_code = '''
import subprocess
result = subprocess.run(["git", "add", "."], cwd=project_dir, capture_output=True, text=True)
if result.returncode == 0:
    print("添加成功")
    '''
    
    print("舊代碼（直接subprocess）:")
    print(old_code)
    print()
    
    # 新代碼示例（使用GitToolWrapper）
    print("新代碼（使用GitToolWrapper）:")
    print("方案A：生成OpenClaw指引（推薦）")
    print('''
wrapper = GitToolWrapper(project_dir, use_openclaw_tools=True)
guidance = wrapper.git_add(".")
print("生成的指引:", json.dumps(guidance, indent=2))
# Agent根據指引調用exec工具
''')
    
    print("方案B：直接執行（向後兼容）")
    print('''
wrapper = GitToolWrapper(project_dir, use_openclaw_tools=False)
success, output, error = wrapper.git_add(".")
if success:
    print(f"添加成功: {output}")
else:
    print(f"添加失敗: {error}")
''')
    
    print("=== 遷移完成 ===")


if __name__ == "__main__":
    # 測試GitToolWrapper
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--migrate":
        migrate_old_code_example()
        sys.exit(0)
    
    print("=== GitToolWrapper 測試 ===")
    
    # 創建測試目錄
    test_dir = Path("/tmp/test_git_wrapper")
    test_dir.mkdir(exist_ok=True)
    
    # 初始化Git工具
    wrapper = GitToolWrapper(test_dir, use_openclaw_tools=True)
    
    print(f"測試目錄: {test_dir}")
    print(f"使用OpenClaw工具: {wrapper.use_openclaw_tools}")
    print()
    
    # 測試生成指引
    print("1. 生成git status指引:")
    guidance = wrapper.git_status()
    print(json.dumps(guidance, indent=2, ensure_ascii=False))
    print()
    
    print("2. 生成git add指引:")
    guidance = wrapper.git_add(".")
    print(json.dumps(guidance, indent=2, ensure_ascii=False))
    print()
    
    print("3. 測試危險命令驗證:")
    dangerous_guidance = wrapper.execute(["git", "push", "--force", "origin", "main"])
    print(json.dumps(dangerous_guidance, indent=2, ensure_ascii=False))
    print()
    
    # 測試直接執行模式
    print("4. 切換到直接執行模式:")
    wrapper_direct = GitToolWrapper(test_dir, use_openclaw_tools=False)
    success, output, error = wrapper_direct.git_status()
    print(f"成功: {success}")
    print(f"輸出: {output[:100] if output else '無'}")
    print(f"錯誤: {error or '無'}")
    
    print("\n=== 測試完成 ===")
    print("\n使用方法:")
    print("  python git_tool_wrapper.py                    # 運行測試")
    print("  python git_tool_wrapper.py --migrate         # 查看遷移示例")