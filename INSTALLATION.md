# Project Memory Manager v5.0 安裝指南

## 概述

本指南介紹如何安裝和配置 Project Memory Manager v5.0。v5.0 是完全基於 OpenClaw 哲學的重構版本：「技能提供指引，Agent 執行操作」。

## 系統要求

### 必需條件
- **Python**: 3.8 或更高版本
- **OpenClaw**: 任何支持以下工具的版本：
  - `exec` (命令執行)
  - `sessions_history` (會話歷史)
  - `sessions_spawn` (子會話生成)
  - `memory_search` (記憶搜索)
  - `read`/`write` (文件讀寫)
- **Git**: 2.20 或更高版本（用於版本控制）

### 推薦條件
- **GitHub CLI (`gh`)**: 用於自動創建 GitHub 倉庫
- **OpenClaw 工作空間**: 已配置 `OPENCLAW_WORKSPACE` 環境變量

## 安裝步驟

### 步驟 1: 下載技能

#### 選項 A: 從 GitHub 克隆
```bash
# 克隆倉庫
git clone https://github.com/mismcinffh-svg/project-memory-manager.git

# 進入技能目錄
cd project-memory-manager

# 切換到 v5.0.0 版本
git checkout v5.0.0
```

#### 選項 B: 作為 OpenClaw 技能安裝
```bash
# 複製到 OpenClaw 技能目錄
cp -r project-memory-manager ~/.openclaw/workspace-[your-agent]/skills/

# 或使用符號鏈接（推薦，便於更新）
ln -s $(pwd)/project-memory-manager ~/.openclaw/workspace-[your-agent]/skills/
```

### 步驟 2: 安裝 Python 依賴

```bash
# 進入技能目錄
cd ~/.openclaw/workspace-[your-agent]/skills/project-memory-manager

# 安裝依賴（如果沒有 requirements.txt，v5.0 使用內置依賴）
python3 -m pip install --upgrade pip

# 檢查 Python 版本
python3 --version  # 需要 3.8+
```

### 步驟 3: 配置環境變量

#### 設置工作空間路徑
```bash
# 在 ~/.bashrc, ~/.zshrc 或 OpenClaw 配置中
export OPENCLAW_WORKSPACE="$HOME/.openclaw/workspace-[your-agent]"

# 驗證配置
echo $OPENCLAW_WORKSPACE
```

#### 可選: 配置 GitHub CLI
```bash
# 安裝 GitHub CLI
# macOS: brew install gh
# Ubuntu: sudo apt install gh
# 其他: https://cli.github.com/

# 登錄 GitHub
gh auth login

# 驗證登錄
gh auth status
```

### 步驟 4: 驗證安裝

#### 運行測試套件
```bash
cd ~/.openclaw/workspace-[your-agent]/skills/project-memory-manager
python3 test_v5_components.py
```

**預期輸出**:
```
SecurityValidator              ✅ 通過
GitToolWrapper                 ✅ 通過
OpenClawToolsWrapper           ✅ 通過
ProjectUpdateGuidance          ✅ 通過
ProjectUpdateIntegrationV5     ✅ 通過
Backward Compatibility         ✅ 通過
====================================
Total: 6 Passed, 0 Failed 🎉
```

#### 運行架構對比演示
```bash
python3 demo_v5_vs_v4.py
```

#### 測試基本功能
```bash
# 測試 v5.0 新架構
python3 -c "
from scripts.project_update_integration_v5 import ProjectUpdateIntegrationV5
integration = ProjectUpdateIntegrationV5(use_old_components=False)
print('v5.0 架構初始化: ✅')
"

# 測試 v4.x 兼容模式
python3 -c "
from scripts.project_update_integration_v5 import ProjectUpdateIntegrationV5
integration = ProjectUpdateIntegrationV5(use_old_components=True)
print('v4.x 兼容模式初始化: ✅')
"
```

## 配置詳解

### 核心配置文件

#### config.json (主要配置)
```json
{
  "openclaw": {
    "requires": {
      "python": true
    },
    "version": "5.0.0",
    "architecture": "guidance-based"
  },
  "security": {
    "path_whitelist": [
      "/projects",
      "/scripts",
      "/config"
    ],
    "command_blacklist": [
      "rm\\s+-rf",
      "wget\\s+.*\\|\\s*sh",
      "curl\\s+.*\\|\\s*bash",
      "chmod\\s+777"
    ]
  }
}
```

#### project.json (項目配置示例)
每個項目在 `projects/<project-name>/project.json` 有自己的配置：
```json
{
  "name": "項目名稱",
  "slug": "project-slug",
  "description": "項目描述",
  "version": "1.0.0",
  "github_url": "https://github.com/username/repo",
  "status": "active",
  "keywords": ["關鍵詞1", "關鍵詞2"]
}
```

### 環境變量配置

| 變量名 | 用途 | 示例值 |
|--------|------|--------|
| `OPENCLAW_WORKSPACE` | 工作空間根目錄 | `$HOME/.openclaw/workspace-secretary` |
| `PM_USE_V5_ARCHITECTURE` | 強制使用 v5.0 架構 | `true` 或 `false` |
| `PM_SECURITY_LEVEL` | 安全級別 | `strict` (默認), `moderate`, `permissive` |
| `PM_LOG_LEVEL` | 日誌級別 | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## 架構選擇

v5.0 支持兩種架構模式，可根據需要選擇：

### 模式 A: v5.0 指引架構 (推薦)
```python
# 使用 v5.0 新架構 - 技能提供指引，Agent執行操作
from scripts.project_update_integration_v5 import ProjectUpdateIntegrationV5

integration = ProjectUpdateIntegrationV5(use_old_components=False)

# 獲取工作流程指引
guidance = integration.get_full_workflow_guidance(
    project_slug="my-project",
    update_summary=True
)

# Agent 根據指引執行工具調用
```

**優點**:
- 符合 OpenClaw 哲學
- 最高安全性（所有命令都經過驗證）
- 真實數據源（非模擬數據）
- 清晰的責任分離

### 模式 B: v4.x 兼容模式
```python
# 使用兼容模式 - 類似 v4.x 的直接執行
from scripts.project_update_integration_v5 import ProjectUpdateIntegrationV5

integration = ProjectUpdateIntegrationV5(use_old_components=True)

# 直接執行工作流程（兼容 v4.x 腳本）
success, version, details = integration.run_compatible_workflow(
    "my-project",
    update_summary=True
)
```

**優點**:
- 完全向後兼容
- 無需修改現有代碼
- 遷移路徑平滑

### 模式 C: 混合模式 (漸進遷移)
```python
# 逐步遷移到 v5.0 架構
from scripts.project_update_integration_v5 import ProjectUpdateIntegrationV5

# 階段 1: 使用兼容模式
integration = ProjectUpdateIntegrationV5(use_old_components=True)

# 階段 2: 遷移部分組件
from scripts.git_tool_wrapper import GitToolWrapper
git_wrapper = GitToolWrapper(project_dir, use_openclaw_tools=True)

# 階段 3: 完全使用 v5.0
integration = ProjectUpdateIntegrationV5(use_old_components=False)
```

## 安全配置

### 安全級別

v5.0 提供三個安全級別：

#### 級別 1: Strict (嚴格)
- 所有路徑都必須在 whitelist 內
- 所有命令都經過 blacklist 過濾
- Git 命令必須來自 GitToolWrapper
- 默認級別，推薦用於生產環境

#### 級別 2: Moderate (中等)
- 允許工作空間內的所有路徑
- 只過濾高危命令 (rm -rf, wget | sh 等)
- 允許直接 exec，但有警告
- 推薦用於開發環境

#### 級別 3: Permissive (寬鬆)
- 只過濾極端危險命令
- 主要用於調試和遷移
- 不推薦用於生產

### 配置安全級別
```bash
# 通過環境變量
export PM_SECURITY_LEVEL="moderate"

# 通過代碼
from scripts.security import SecurityValidator
validator = SecurityValidator(security_level="moderate")
```

## 故障排除

### 常見問題

#### Q1: 導入錯誤 "No module named 'guidance_executor'"
**解決方案**:
```bash
# 確保在正確的目錄中
cd ~/.openclaw/workspace-[your-agent]/skills/project-memory-manager

# 檢查文件是否存在
ls -la scripts/guidance_executor.py

# 如果不存在，從 GitHub 重新下載
git checkout v5.0.0
```

#### Q2: 安全驗證失敗 "路徑不在workspace範圍內"
**解決方案**:
```bash
# 設置 OPENCLAW_WORKSPACE 環境變量
export OPENCLAW_WORKSPACE=$(pwd)

# 或使用兼容模式（臨時）
export PM_SECURITY_LEVEL="permissive"
```

#### Q3: v5.0 指引架構不理解如何使用
**解決方案**:
```python
# 使用 GuidanceExecutor 獲取執行指導
from scripts.openclaw_tools_wrapper import OpenClawToolsWrapper
from scripts.guidance_executor import GuidanceExecutor

tools = OpenClawToolsWrapper("project-name")
guidance = tools.get_conversation_history(limit=30)

# 獲取完整執行方案
executor = GuidanceExecutor()
scheme = executor.execute_guidance(guidance)

# 生成示例代碼
example = executor.generate_execution_script(guidance, "python")
print(example)
```

#### Q4: 測試失敗
**解決方案**:
```bash
# 運行詳細測試
python3 test_v5_components.py --verbose

# 檢查 Python 版本
python3 --version  # 需要 3.8+

# 檢查依賴
python3 -c "import json, re, pathlib, logging; print('基本依賴: ✅')"
```

### 獲取幫助

1. **查看文檔**:
   - `SKILL.md` - 主要技能文檔
   - `MIGRATION_GUIDE.md` - 遷移指南
   - `VERSION.md` - 版本信息

2. **運行演示**:
   ```bash
   python3 demo_v5_vs_v4.py
   ```

3. **檢查示例**:
   ```bash
   # 查看使用示例
   python3 scripts/openclaw_tools_wrapper.py --migrate
   ```

4. **GitHub 問題**:
   - 訪問 https://github.com/mismcinffh-svg/project-memory-manager/issues

## 升級指南

### 從 v4.x 升級到 v5.0

#### 自動遷移 (推薦)
```bash
cd project-memory-manager
python3 scripts/project_update_integration_v5.py --migrate-v4-to-v5
```

#### 手動遷移步驟
1. **備份現有數據**:
   ```bash
   cp -r projects/ projects_backup_v4/
   ```

2. **安裝 v5.0**:
   ```bash
   git fetch origin
   git checkout v5.0.0
   ```

3. **測試兼容性**:
   ```bash
   python3 test_v5_components.py --test compatibility
   ```

4. **漸進式遷移**:
   ```python
   # 先使用兼容模式
   integration = ProjectUpdateIntegrationV5(use_old_components=True)
   
   # 逐步遷移組件
   # 1. 先遷移 Git 操作 (GitToolWrapper)
   # 2. 再遷移工具調用 (OpenClawToolsWrapper)
   # 3. 最後遷移工作流程 (ProjectUpdateGuidance)
   ```

5. **完全切換**:
   ```python
   # 當所有組件都遷移後
   integration = ProjectUpdateIntegrationV5(use_old_components=False)
   ```

## 性能優化

### 增量處理 (v5.0.1+)
```python
# 只處理上次摘要後的對話
from scripts.openclaw_tools_wrapper import OpenClawToolsWrapper

tools = OpenClawToolsWrapper("project-name")
last_summary_time = "2026-01-01T00:00:00Z"

# 只獲取上次摘要後的對話
guidance = tools.get_conversation_history(
    limit=100,
    since_time=last_summary_time  # 新增參數
)
```

### 緩存機制
```python
# 使用內置緩存減少重複工具調用
from scripts.project_update_guidance import ProjectUpdateGuidance

guidance_gen = ProjectUpdateGuidance(enable_cache=True)

# 第一次生成指引（會調用工具）
guidance1 = guidance_gen.get_workflow_guidance("project-name", "update")

# 第二次生成指引（使用緩存）
guidance2 = guidance_gen.get_workflow_guidance("project-name", "update")
```

## 開發者指南

### 擴展 v5.0 架構

#### 添加新工具封裝
```python
# 1. 創建新的工具封裝類
class NewToolWrapper:
    def __init__(self, project_slug=None):
        self.project_slug = project_slug
    
    def get_tool_guidance(self, **params) -> Dict:
        return {
            "tool": "new_tool",
            "parameters": params,
            "description": "新工具的指引"
        }

# 2. 集成到 OpenClawToolsWrapper
# 在 openclaw_tools_wrapper.py 中添加方法
```

#### 添加新的安全規則
```python
# 在 security.py 中擴展
class EnhancedSecurityValidator(SecurityValidator):
    def __init__(self, workspace_dir=None, security_level="strict"):
        super().__init__(workspace_dir, security_level)
        
        # 添加新的危險模式
        self.dangerous_patterns.extend([
            r"sudo\s+",  # 禁止 sudo
            r"dd\s+",    # 禁止 dd 命令
        ])
```

## 版本信息

- **當前版本**: 5.0.0
- **發布日期**: 2026-03-16
- **架構**: Guidance-based (指引驅動)
- **兼容性**: 完全向後兼容 v4.x

詳見 `VERSION.md` 和 `CHANGELOG.md`。

---

**安裝完成！** 現在你可以開始使用 Project Memory Manager v5.0 了。

下一步建議:
1. 運行 `python3 demo_v5_vs_v4.py` 了解架構差異
2. 閱讀 `MIGRATION_GUIDE.md` 規劃遷移策略
3. 在測試項目上嘗試 v5.0 指引架構