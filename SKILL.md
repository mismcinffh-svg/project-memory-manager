---
name: project-memory-manager-v5
description: Manage project memory and archives using OpenClaw v5.0 architecture. Use when user says '歸檔', '記錄落去', '更新專櫃', 'commit', '上github', '更新版本', '同步到github', '版本更新', '發布', 'release', or when preparing to push to GitHub. Provides guidance instead of direct execution, following OpenClaw best practices.
metadata: {"openclaw": {"requires": {"python": true}, "user-invocable": true, "install": [{"id": "python-deps", "kind": "info", "label": "Python 3.8+ required", "note": "本技能使用Python腳本實現自動化功能"}], "version": "5.0.0", "architecture": "guidance-based"}}
---

# Project Memory Manager v5.0

## Overview

**Project Memory Manager v5.0** is a complete architectural redesign that follows OpenClaw's philosophy of "skills provide guidance, Agents execute." This version solves the security and architectural issues of v4.x while maintaining full backward compatibility.

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

## Quick Start Guide (3 Steps)

### Step 1: Detect the Scenario
Check if the current context requires project memory management:
```bash
# Option A: Manual check
# Look for keywords: 歸檔, commit, 更新版本, etc.

# Option B: Automated detection
python3 {baseDir}/scripts/trigger_detector.py --message "用戶消息內容"
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

### Step 3: Execute the Update Workflow
Choose the appropriate command based on the scenario:

**Scenario A: Archive/Update Cabinet Content**
```bash
python3 {baseDir}/scripts/project_update_integration.py \
  --project <project-name> \
  --update-summary \
  --yes
```

**Scenario B: Version Update/Release**
```bash
python3 {baseDir}/scripts/project_update_integration.py \
  --project <project-name> \
  --no-update-summary \
  --yes
```

**Scenario C: GitHub Sync Preparation**
```bash
# First update cabinet content, then push
python3 {baseDir}/scripts/project_update_integration.py \
  --project <project-name> \
  --update-summary \
  --yes
# Then manually git push (or let the skill handle it)
```

## Expected Output

### Success Indicators
```
✅ 專櫃內容已更新：projects/<project>/_latest/_history 文件
✅ 版本號已遞增（如果適用）
✅ CHANGELOG.md 已更新
✅ 專案準備好 GitHub 推送
```

### File Structure Changes
```
projects/<project>/
├── _latest/              # Latest summaries
│   ├── decisions_latest.md
│   ├── learnings_latest.md
│   └── technical_latest.md
├── _history/             # Complete history
│   ├── decisions_history.md
│   ├── learnings_history.md
│   └── technical_history.md
├── decisions.md          # Decision records (appended)
├── CHANGELOG.md         # Version history
└── project.json         # Updated version number
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