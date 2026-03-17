---
name: project-memory-manager-v5
description: Manage project memory and archives using OpenClaw v5.0 architecture. Use when user says '歸檔', '記錄落去', '更新專櫃', 'commit', '上github', '更新版本', '同步到github', '版本更新', '發布', 'release', or when preparing to push to GitHub. Provides guidance instead of direct execution, following OpenClaw best practices.
metadata: {"openclaw": {"requires": {"python": true}, "user-invocable": true, "install": [{"id": "python-deps", "kind": "info", "label": "Python 3.8+ required", "note": "本技能使用Python腳本實現自動化功能"}], "version": "5.0.3", "architecture": "guidance-based"}}
---

# Project Memory Manager v5.0.3

## Overview

**Project Memory Manager v5.0.2** is a complete architectural redesign that follows OpenClaw's philosophy of "skills provide guidance, Agents execute." This version solves the security and architectural issues of v4.x while maintaining full backward compatibility.

### 🎯 v5.0 Key Improvements
| 問題 | v4.x | v5.0 解決方案 |
|------|------|---------------|
| **安全風險** | 直接 `subprocess` | `exec` 工具指引 + 安全驗證 |
| **數據不真實** | 模擬數據 (mock) | 真實 OpenClaw 工具調用 |
| **架構違規** | 技能直接執行操作 | 技能提供指引，Agent 執行 |
| **Token 估算不準** | `len(text) // 3` | 中英文混合精準算法 |
| **原子性問題** | 無事務支持 | 完整事務 + 自動回滾 |

## Core Architecture Principles

### 🔧 Skills as Toolboxes (Not Automation Machines)
v5.0 follows the OpenClaw philosophy:
- **Skills provide tools and guidance** - not direct execution
- **Agents decide when and how** - based on context and judgment
- **Clear separation of concerns** - guidance generation vs. execution

### 🛡️ Security-First Design
- **Zero `subprocess` calls** - all commands use `exec` tool guidance
- **Path whitelist validation** - prevents directory traversal attacks
- **Command sanitization** - dangerous command blacklist + Git command whitelist
- **Atomic operations** - file locks + automatic backup/rollback

### 🔄 Full Backward Compatibility
- **Dual architecture support** - choose v4.x compatible mode or v5.0 guidance mode
- **Automatic migration** - `use_old_components=True` for compatibility
- **Gradual adoption** - migrate components one by one

## When to Use This Skill

### Trigger Keywords
Use this skill when the user says:
- **歸檔**, **記錄落去**, **更新專櫃** - Archive or update project cabinet
- **commit**, **上github**, **同步到github** - Prepare for GitHub sync
- **更新版本**, **版本更新**, **發布**, **release** - Version update scenarios
- When preparing to push to GitHub

### Detection Methods
1. **Manual detection**: Check if user message contains any trigger keywords
2. **Automated detection**: Run `trigger_detector.py` to analyze the message
3. **Context-based**: If discussing project completion or GitHub operations

## Quick Start Guide (v5.0 Architecture)

### Step 1: Detect the Scenario
Check if the current context requires project memory management:
```bash
# Option A: Manual check
# Look for keywords: 歸檔, commit, 更新版本, etc.

# Option B: Automated detection (v5.0 recommended)
python3 {baseDir}/scripts/project_update_integration_v5.py \
  --project <project-name> \
  --detect-only
```

### Step 2: Find the Target Project
Locate the project in the `projects/` directory:
1. **Extract from message**: User may mention project name (e.g., "office365-skill")
2. **Check INDEX.md**: Read the index file to find recent or relevant projects
3. **Recent project**: If unspecified, use the most recently modified project

**INDEX.md format:**
```
| 項目 | 關鍵詞 | 位置 | 狀態 |
|------|--------|------|------|
| office365-skill | office365, email, calendar | projects/office365-skill | active |
| project-memory-manager | memory, archive, project | projects/project-memory-manager | active |
```

### Step 3: Choose Your Architecture (v5.0 Key Decision)

#### Option A: v5.0 Guidance Mode (Recommended)
**Philosophy**: Skills provide guidance, Agents execute operations
```python
# 使用 v5.0 新架構 - 獲取指引，Agent執行
from scripts.project_update_integration_v5 import ProjectUpdateIntegrationV5

# 1. 初始化（使用新架構）
integration = ProjectUpdateIntegrationV5(use_old_components=False)

# 2. 獲取完整工作流程指引
guidance = integration.get_full_workflow_guidance(
    project_slug="project-name",
    update_summary=True,
    auto_confirm=False
)

# 3. Agent根據指引執行操作
#    - 調用 sessions_history 獲取真實對話
#    - 調用 sessions_spawn 生成摘要
#    - 調用 exec 執行Git操作
#    - 所有操作都經過安全驗證

print("工作流程指引:", json.dumps(guidance, indent=2))
```

#### Option B: v5.0 with GuidanceExecutor (Enhanced)
**For Complex Workflows**: Use GuidanceExecutor to help execute guidance
```python
from scripts.openclaw_tools_wrapper import OpenClawToolsWrapper
from scripts.guidance_executor import GuidanceExecutor

# 1. 獲取工具指引
tools = OpenClawToolsWrapper("project-name")
history_guidance = tools.get_conversation_history(limit=30)

# 2. 獲取執行方案
executor = GuidanceExecutor()
execution_scheme = tools.get_execution_scheme(history_guidance)

# 3. 生成示例代碼
example_code = tools.generate_execution_example(history_guidance, "python")
print("示例代碼:\n", example_code)
```

#### Option C: v4.x Compatibility Mode
**For Migration or Legacy Support**: Use v5.0 with v4.x compatibility
```bash
# 命令行方式（兼容v4.x腳本）
python3 {baseDir}/scripts/project_update_integration_v5.py \
  --project <project-name> \
  --use-old-components \
  --update-summary \
  --yes

# Python方式
from scripts.project_update_integration_v5 import ProjectUpdateIntegrationV5
integration = ProjectUpdateIntegrationV5(use_old_components=True)
success, version, details = integration.run_compatible_workflow(
    "project-name", 
    update_summary=True,
    auto_confirm=False
)
```

### Common Scenarios (v5.0 Style)

#### Scenario A: Archive/Update with Guidance
```python
# 獲取歸檔工作流程指引
integration = ProjectUpdateIntegrationV5(use_old_components=False)
guidance = integration.get_archive_workflow_guidance("project-name")
# Agent根據guidance執行歸檔操作
```

#### Scenario B: Version Update with Safe Git Operations
```python
# 使用GitToolWrapper生成安全Git操作指引
from scripts.git_tool_wrapper import GitToolWrapper
git_wrapper = GitToolWrapper(project_dir, use_openclaw_tools=True)

# 安全Git操作指引
add_guidance = git_wrapper.git_add(".")
commit_guidance = git_wrapper.git_commit("更新版本")
push_guidance = git_wrapper.git_push()

# 所有指引都經過安全驗證，無subprocess風險
```

#### Scenario C: Real Data Processing
```python
# 使用真實OpenClaw工具數據
from scripts.openclaw_tools_wrapper import OpenClawToolsWrapper
tools = OpenClawToolsWrapper("project-name")

# 真實對話歷史指引（非模擬數據）
history_guidance = tools.get_conversation_history(limit=50)

# 真實摘要生成指引
summary_guidance = tools.spawn_summary_agent(
    project_name="Project Name",
    conversations=real_conversations,  # 從sessions_history獲取
    since_time="2026-01-01T00:00:00Z"
)
```

## Expected Output (v5.0 Architecture)

### v5.0 Guidance Mode Success Indicators
```
✅ 安全指引生成：所有操作都經過安全驗證
✅ 真實工具調用：使用 sessions_history 獲取真實對話
✅ 原子操作保證：文件鎖 + 事務支持防止損壞
✅ 零風險Git操作：所有Git命令都通過安全檢查
✅ 完整執行方案：GuidanceExecutor提供詳細執行步驟
✅ 向後兼容性：v4.x項目無需修改即可工作
```

### v4.x Compatibility Mode Success Indicators
```
✅ 專櫃內容已更新：projects/<project>/_latest/_history 文件
✅ 版本號已遞增（如果適用）
✅ CHANGELOG.md 已更新
✅ 專案準備好 GitHub 推送
```

### File Structure Changes (v5.0 Enhanced)
```
projects/<project>/
├── _latest/              # Latest summaries (v5.0原子寫入保證)
│   ├── decisions_latest.md
│   ├── learnings_latest.md
│   └── technical_latest.md
├── _history/             # Complete history (事務保護)
│   ├── decisions_history.md
│   ├── learnings_history.md
│   └── technical_history.md
├── decisions.md          # Decision records (原子追加)
├── CHANGELOG.md         # Version history (自動更新)
├── project.json         # Updated version number (JSON Schema驗證)
└── .locks/              # v5.0新增：文件鎖目錄（防止併發衝突）
```

### Guidance Output Examples

#### Example 1: Conversation History Guidance
```json
{
  "tool": "sessions_history",
  "action": "get_conversation_history",
  "parameters": {
    "sessionKey": "current",
    "limit": 30,
    "includeTools": false
  },
  "description": "獲取當前會話的對話歷史",
  "execution_scheme": {
    "tool_call_example": { ... },
    "execution_steps": [ ... ],
    "error_handling": { ... }
  }
}
```

#### Example 2: Git Operation Guidance
```json
{
  "tool": "exec",
  "source": "GitToolWrapper",
  "parameters": {
    "command": "git add .",
    "workdir": "/safe/path/inside/workspace",
    "timeout": 30
  },
  "security_checked": true,
  "dangerous_patterns_rejected": 0
}
```

#### Example 3: Complete Workflow Guidance
```json
{
  "type": "complete_workflow",
  "project": "project-name",
  "architecture": "v5.0_guidance",
  "steps": [
    {
      "step": 1,
      "name": "獲取真實對話歷史",
      "guidance": { ... },
      "estimated_tokens": 1500,
      "security_level": "high"
    },
    {
      "step": 2,
      "name": "生成AI摘要",
      "guidance": { ... },
      "estimated_tokens": 3000,
      "security_level": "medium"
    }
  ],
  "total_estimated_tokens": 7500,
  "security_score": 95
}
```

## Common Errors & Troubleshooting

### Error 1: "找不到項目" (Project not found)
**Symptoms:** `❌ 找不到項目: <name>`
**Solution:**
1. Check if `projects/INDEX.md` contains the project
2. Verify the project directory has `project.json`
3. Run repair command:
   ```bash
   python3 {baseDir}/scripts/create.py rebuild-index
   ```

### Error 2: Python Path Issues
**Symptoms:** `ModuleNotFoundError` or `python3: command not found`
**Solution:**
1. Confirm Python 3.8+ is installed: `python3 --version`
2. Install dependencies if missing: `pip install -r {baseDir}/requirements.txt`

### Error 3: Permission Denied
**Symptoms:** `Permission denied` or `Read-only file system`
**Solution:**
1. Check workspace directory permissions: `ls -la ~/.openclaw/workspace-*/`
2. Fix permissions if needed: `chmod -R 755 ~/.openclaw/`

### Error 4: INDEX.md Format Error
**Symptoms:** Cannot parse index file
**Solution:**
1. Manually fix INDEX.md (maintain Markdown table format)
2. Or rebuild index: `python3 {baseDir}/scripts/create.py rebuild-index`

### Error 5: GitHub Remote URL Not Found
**Symptoms:** `fatal: 'origin' does not appear to be a git repository`
**Solution:**
1. **First time setup**: Set the GitHub remote URL:
   ```bash
   cd projects/<project-name>
   git remote add origin https://github.com/your-username/repo-name.git
   ```
2. **After successful push**: The skill automatically records the URL in `project.json`
3. **Next session**: Read `github_url` from `project.json` to avoid asking again
4. **Manual check**: View recorded URL:
   ```bash
   cat projects/<project-name>/project.json | grep github_url
   ```

### Error 6: v5.0 Guidance Execution Issues
**Symptoms:** 
- `GuidanceExecutor not found` 或 `OpenClawToolsWrapper只生成指引，不知如何執行`
- `參數轉換錯誤` 或 `工具調用失敗`

**Solution (v5.0.1+):**
1. **安裝GuidanceExecutor**: 確保 `guidance_executor.py` 在 scripts/ 目錄中
2. **使用執行方案**: 通過 `get_execution_scheme()` 獲取完整執行指導
   ```python
   from scripts.openclaw_tools_wrapper import OpenClawToolsWrapper
   tools = OpenClawToolsWrapper("project-name")
   guidance = tools.get_conversation_history(limit=30)
   execution_scheme = tools.get_execution_scheme(guidance)
   ```
3. **生成示例代碼**: 使用 `generate_execution_example()` 獲取可直接使用的代碼
   ```python
   example_code = tools.generate_execution_example(guidance, "python")
   print(example_code)  # 顯示如何調用工具的示例代碼
   ```
4. **安全執行Git操作**: 始終使用 `GitToolWrapper` 而非直接 `exec`
   ```python
   # ❌ 危險：直接exec
   # exec(command="git add .")  # 可能包含危險命令
   
   # ✅ 安全：通過GitToolWrapper
   from scripts.git_tool_wrapper import GitToolWrapper
   wrapper = GitToolWrapper(project_dir, use_openclaw_tools=True)
   safe_guidance = wrapper.git_add(".")  # 經過安全檢查
   ```

### Error 7: v5.0 Security Validation Failures
**Symptoms:**
- `路徑不在workspace範圍內` 或 `命令包含危險模式`
- `SecurityValidator拒絕操作`

**Solution:**
1. **檢查工作空間路徑**: 確保所有操作都在 `OPENCLAW_WORKSPACE` 環境變量指定的目錄內
2. **使用安全命令**: 避免 `rm -rf`, `wget | sh`, `chmod 777` 等危險模式
3. **白名單路徑**: 只操作 `projects/`, `scripts/`, `config/` 等目錄
4. **降級到兼容模式** (臨時解決方案):
   ```python
   from scripts.project_update_integration_v5 import ProjectUpdateIntegrationV5
   integration = ProjectUpdateIntegrationV5(use_old_components=True)
   # 使用v4.x兼容模式（安全性較低）
   ```

### Error 8: Real Tool Call Failures (v5.0 vs Mock Data)
**Symptoms:**
- `sessions_history工具返回空數據` 或 `sessions_spawn失敗`
- `真實工具調用與模擬數據不一致`

**Solution:**
1. **檢查工具權限**: 確認 `tools.sessions.visibility=all` 設置正確
2. **使用模擬數據回退** (開發/測試):
   ```python
   # 在開發環境中使用模擬數據
   from scripts.conversation_summary import ConversationSummary
   summary = ConversationSummary(project_dir)
   simulated = summary.simulate_conversation_history("project-name")
   ```
3. **漸進式遷移**: 先使用兼容模式，逐步遷移到真實工具調用
4. **錯誤處理**: 實現優雅的錯誤降級機制

## 🗂️ 項目歸檔操作指南 (Archive Project Guide) - v5.0.3

**目標**: 30秒內完成項目歸檔，無需探索代碼或理解內部實現

### 快速歸檔 (3步完成)

#### 步驟1: 運行歸檔命令
```bash
# 基本歸檔
python3 scripts/archive_project.py --project project-name

# 帶詳細輸出
python3 scripts/archive_project.py --project project-name --verbose

# 生成可執行腳本
python3 scripts/archive_project.py --project project-name --generate-script
```

#### 步驟2: 查看歸檔結果
```bash
# 查看歸檔指引和執行方案
python3 scripts/archive_project.py --project project-name --output archive_result.json

# 查看生成的專櫃文件
ls projects/project-name/_latest/
```

#### 步驟3: 可選Git同步
```bash
# 如果需要同步到GitHub
python3 scripts/project_update_integration_v5.py --project project-name --update-summary
```

### 歸檔工具功能詳解

#### 1. 基本歸檔
```bash
# 歸檔指定項目
python3 scripts/archive_project.py --project project-memory-manager

# 指定workspace目錄
python3 scripts/archive_project.py --project office365-skill --workspace /path/to/workspace

# 控制對話歷史條數
python3 scripts/archive_project.py --project project-name --limit 50

# 只獲取指引，不生成摘要
python3 scripts/archive_project.py --project project-name --no-summary
```

#### 2. 生成快速腳本
```bash
# 生成可獨立運行的歸檔腳本
python3 scripts/archive_project.py --project project-name --generate-script

# 運行生成的腳本
python3 archive_project-name.py
```

#### 3. 獲取幫助
```bash
# 查看完整幫助
python3 scripts/archive_project.py --help

# 簡短幫助
python3 scripts/archive_project.py -h
```

### 歸檔流程詳解 (內部工作原理)

```
歸檔執行流程:
1. ✅ 安全驗證: 路徑白名單 + 命令黑名單檢查
2. ✅ 指引生成: 獲取歸檔工作流程指引
3. ✅ 對話歷史: 生成sessions_history工具調用指引
4. ✅ 摘要生成: 生成sessions_spawn摘要指引
5. ✅ 執行方案: 生成詳細執行步驟和示例代碼
6. ✅ 文件更新: 準備專櫃文件更新計劃
```

### 示例: 完整歸檔項目

```bash
# 示例1: 歸檔project-memory-manager項目
python3 scripts/archive_project.py --project project-memory-manager --verbose --output pm_archive.json

# 示例2: 生成並運行歸檔腳本
python3 scripts/archive_project.py --project office365-skill --generate-script
python3 archive_office365-skill.py

# 示例3: 批量歸檔多個項目
for project in project1 project2 project3; do
    python3 scripts/archive_project.py --project $project --no-summary
done
```

### 預期輸出

```
🚀 開始歸檔項目: project-name
📋 生成歸檔工作流程指引...
💬 獲取對話歷史指引...
📝 生成摘要指引...
🔧 生成執行方案...
📁 準備更新專櫃文件...
✅ 項目 'project-name' 歸檔準備完成
   項目: project-name
   時間: 2026-03-17T00:30:00.000000
   完成步驟: 5
   
📋 下一步:
   1. 根據指引執行對話歷史獲取
   2. 根據指引生成摘要
   3. 根據計劃更新專櫃文件
   4. 可選：同步到GitHub
   
💡 提示: 使用 --generate-script 生成可執行的歸檔腳本
```

### 常見問題 (FAQ)

#### Q1: 歸檔工具與v5.0哲學矛盾嗎？
**A**: 不矛盾。歸檔工具仍然遵循「技能提供指引」原則：
- 工具生成詳細的執行指引和示例代碼
- Agent仍然需要根據指引執行實際操作
- 工具提供「立即可用」的起點，而不是完全自動化

#### Q2: 如何處理真實工具調用失敗？
**A**: 工具包含錯誤處理和降級機制：
- 真實工具失敗時提供清晰的錯誤信息
- 可選使用模擬數據進行開發和測試
- 生成替代執行方案

#### Q3: 歸檔後文件在哪裡？
**A**: 歸檔內容保存在：
- `projects/<project-name>/_latest/` - 最新摘要
- `projects/<project-name>/_history/` - 完整歷史
- `projects/<project-name>/decisions.md` - 決策記錄
- `projects/<project-name>/learnings_latest.md` - 最新學習點

#### Q4: 可以自動同步到GitHub嗎？
**A**: 可以，但需要額外步驟：
```bash
# 先歸檔
python3 scripts/archive_project.py --project project-name

# 再同步到GitHub
python3 scripts/project_update_integration_v5.py --project project-name --update-summary
```

### 與舊版對比

| 功能 | v4.x | v5.0.3歸檔工具 |
|------|------|----------------|
| **執行時間** | 需要探索代碼 (~15分鐘) | 30秒內完成 |
| **命令行** | 無專用歸檔命令 | `archive_project.py --project xxx` |
| **文檔指引** | 需要理解哲學 | 具體操作步驟 |
| **錯誤處理** | 簡單 | 詳細錯誤信息和建議 |
| **輸出結果** | 分散 | 統一JSON輸出 |

### 開發者提示

對於需要自定義歸檔流程的開發者：

```python
# 直接使用歸檔工具類
from scripts.archive_project import ProjectArchiveTool

tool = ProjectArchiveTool()
result = tool.archive_project("project-name", limit=50)

# 生成自定義腳本
script = tool.generate_quick_archive_script("project-name")
with open("custom_archive.py", "w") as f:
    f.write(script)
```

## GitHub Auto-Creation Mechanism

### First-Time GitHub Sync (Automatic)
When you run a project update for the first time and no GitHub remote is configured:

1. **Detection**: The skill checks for `git remote` and `project.json["github_url"]`
2. **GitHub CLI Check**: Verifies `gh` CLI is installed and logged in
3. **Auto-Creation (with `--yes` flag)**: If `--yes` is used, automatically creates a private GitHub repository
4. **Repository Naming**: Uses project `slug` from `project.json` or directory name
5. **Remote Setup**: Configures `origin` remote and pushes all code
6. **URL Recording**: Updates `project.json["github_url"]` after successful push

### Requirements
- **GitHub CLI (gh)**: Must be installed and authenticated (`gh auth login`)
- **Project Slug**: Should be unique and valid for GitHub repository names
- **User Confirmation**: Without `--yes` flag, shows instructions instead of auto-creating

### Example Flow
```bash
# First time (no remote, with --yes to auto-create)
python3 {baseDir}/scripts/project_update_integration.py \
  --project office365-skill \
  --update-summary \
  --yes

# Output:
# ℹ️ 未檢測到Git remote，嘗試設置...
# ✅ GitHub倉庫創建成功: https://github.com/your-username/office365-skill.git
# ✅ Git remote 已設置
# ✅ 分支推送成功: main
# ✅ 已更新project.json github_url

# Subsequent runs (uses recorded URL)
python3 {baseDir}/scripts/project_update_integration.py \
  --project office365-skill \
  --update-summary \
  --yes
```

### Manual Setup Alternative
If you prefer manual setup or don't have GitHub CLI:
```bash
cd projects/<project-name>
git remote add origin https://github.com/your-username/repo-name.git
# The skill will record the URL after first successful push
```

## Advanced Features

### Manual Project Creation
```bash
python3 {baseDir}/scripts/create.py manual "項目名稱" "描述"
```

### System Status Check
```bash
python3 {baseDir}/scripts/create.py status
```

### Demo Mode
```bash
python3 {baseDir}/scripts/project_update_integration.py --demo
```

## Skill Structure

```
{baseDir}/
├── SKILL.md                 # This file
├── scripts/                 # Executable scripts
│   ├── trigger_detector.py  # Keyword detection
│   ├── project_update_integration.py # Main workflow
│   ├── conversation_summary.py # Conversation summarization
│   ├── version_manager.py   # Version management
│   ├── create.py           # Project creation tools
│   └── init.py             # System initialization
├── references/             # Detailed references (load as needed)
│   ├── best-practices.md   # Best practices guide
│   └── troubleshooting.md  # Detailed troubleshooting
└── integration_example.md  # Integration examples
```

## Progressive Disclosure

For detailed information, refer to these files when needed:

### `references/best-practices.md`
- Project structure design principles
- Version management strategies
- GitHub sync best practices

### `references/troubleshooting.md`
- Complete error code list
- System diagnostic commands
- Recovery procedures

### `integration_example.md`
- Integration with other skills examples
- Automated workflow designs
- Custom configuration options

## Emergency Recovery

If the system is completely broken:

1. **Backup existing data:**
   ```bash
   cp -r projects/ projects_backup_$(date +%Y%m%d)/
   ```

2. **Reinitialize:**
   ```bash
   python3 {baseDir}/scripts/init.py --force
   ```

3. **Rebuild index:**
   ```bash
   python3 {baseDir}/scripts/create.py rebuild-index
   ```

4. **Restore projects:**
   ```bash
   python3 {baseDir}/scripts/create.py manual "項目名" --from-backup
   ```

## Design Philosophy

### This skill is a **toolbox**, not an **automation machine**
- You (the Agent) are the toolbox user
- Choose the right tool based on the scenario
- The skill provides guidance, you provide judgment

### Teach fishing, don't give fish
- Don't assume fixed paths (like `~/workspace-secretary`)
- Teach how to detect workspace: traverse up to find `projects/`
- Teach how to read INDEX.md to find projects
- Provide tools, let the Agent decide when to use them

### Remember the fishing spot (GitHub URL memory)
- **Problem**: Skills forget GitHub remote URLs across sessions
- **Solution**: Auto-record remote URL after first successful sync
- **Mechanism**: When `git push` succeeds, update `github_url` in `project.json`
- **Next session**: Read `github_url` from `project.json`, don't ask again
- **Design principle**: Learn from successful operations, reduce repetitive questions