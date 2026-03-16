# Project Memory Manager v5.0 遷移指南

## 概述

v5.0 是基於 OpenClaw 哲學的完全重構版本，解決了 v4.x 中的安全問題和架構缺陷。

### 主要變化

| 方面 | v4.x | v5.0 | 影響 |
|------|------|------|------|
| **命令執行** | 直接使用 `subprocess` | 使用 `exec` 工具指引 | 🛡️ 安全性大幅提升 |
| **數據來源** | 模擬數據 (mock) | 真實 OpenClaw 工具調用 | ✅ 數據準確性 |
| **架構哲學** | 技能直接執行操作 | 技能提供指引，Agent 執行操作 | 🎯 符合 OpenClaw 設計 |
| **安全驗證** | 基本路徑檢查 | 完整路徑白名單 + 命令黑名單 | 🔒 防止目錄遍歷攻擊 |
| **Token 估算** | `len(text) // 3` | 中英文混合精準估算 | 📊 估算準確度提升 |
| **錯誤處理** | 基本異常捕獲 | 事務回滾 + 自動備份 | ♻️ 可靠性增強 |

## 遷移步驟

### 1. 環境準備

確保你的環境滿足 v5.0 要求：

```bash
# 檢查 Python 版本
python3 --version  # 需要 3.8+

# 檢查依賴
git --version
gh --version  # 可選，用於 GitHub 自動創建
```

### 2. 文件結構變化

```
project-memory-manager/
├── scripts/
│   ├── security.py              # 🆕 安全模塊
│   ├── git_tool_wrapper.py      # 🆕 Git 工具封裝
│   ├── openclaw_tools_wrapper.py # 🆕 OpenClaw 工具封裝
│   ├── project_update_guidance.py # 🆕 指引生成器
│   ├── project_update_integration_v5.py # 🆕 v5 集成器
│   ├── project_update_integration.py    # v4 集成器（保留）
│   ├── conversation_summary.py  # v4 組件（保留）
│   └── version_manager.py       # v4 組件（保留）
├── test_v5_components.py        # 🆕 測試套件
├── MIGRATION_GUIDE.md           # 🆕 本文件
└── SKILL.md                     # 需要更新
```

### 3. 代碼遷移示例

#### 舊代碼 (v4.x) - 需要遷移

```python
# ❌ 直接使用 subprocess（安全風險）
import subprocess
result = subprocess.run(["git", "add", "."], capture_output=True, text=True)

# ❌ 模擬對話歷史（不真實）
def simulate_conversation_history():
    return [{"role": "user", "content": "模擬數據"}]

# ❌ 技能直接執行操作
def run_workflow():
    # 直接執行各種操作
    pass
```

#### 新代碼 (v5.0) - 推薦寫法

```python
# ✅ 使用 GitToolWrapper 生成安全指引
from git_tool_wrapper import GitToolWrapper
wrapper = GitToolWrapper(project_dir, use_openclaw_tools=True)
guidance = wrapper.git_add(".")
# Agent 根據 guidance 調用 exec 工具

# ✅ 使用 OpenClawToolsWrapper 獲取真實數據
from openclaw_tools_wrapper import OpenClawToolsWrapper
tools = OpenClawToolsWrapper(project_slug)
history_guidance = tools.get_conversation_history(limit=30)
# Agent 根據 guidance 調用 sessions_history 工具

# ✅ 技能提供指引，不直接執行
from project_update_guidance import ProjectUpdateGuidance
guidance_gen = ProjectUpdateGuidance()
workflow = guidance_gen.get_version_update_workflow(project_slug)
# 返回指引給 Agent 執行
```

### 4. API 變化

#### 舊 API (兼容模式)

```python
from project_update_integration_v5 import ProjectUpdateIntegrationV5

# 使用 v4 兼容模式（不推薦長期使用）
integration = ProjectUpdateIntegrationV5(use_old_components=True)
success, version, details = integration.run_compatible_workflow(
    "project-name", update_summary=True, auto_confirm=False
)
```

#### 新 API (v5.0 架構)

```python
from project_update_integration_v5 import ProjectUpdateIntegrationV5

# 使用 v5.0 新架構（推薦）
integration = ProjectUpdateIntegrationV5(use_old_components=False)

# 方法 1: 獲取完整工作流程指引
guidance = integration.get_full_workflow_guidance(
    "project-name", update_summary=True
)

# 方法 2: 獲取特定組件指引
history_guidance = integration.get_conversation_history_guidance("project-name")
git_guidance = integration.get_git_operations_guidance("project-name", "commit")

# 方法 3: 兼容執行（內部自動選擇架構）
success, version, details = integration.run_compatible_workflow(
    "project-name", update_summary=True
)
```

### 5. 配置遷移

v5.0 簡化了配置管理：

#### 舊配置方式
- `config.json` + `project.json` + 環境變量
- 複雜的 workspace 檢測邏輯（向上遍歷 5 層）

#### 新配置方式
- 優先使用 `OPENCLAW_WORKSPACE` 環境變量
- 統一路徑驗證（SecurityValidator）
- 自動依賴檢查

### 6. 測試遷移

#### 舊測試方式
```bash
# 測試舊功能
python3 scripts/project_update_integration.py --demo
```

#### 新測試方式
```bash
# 測試 v5.0 組件
python3 test_v5_components.py  # 運行所有測試
python3 test_v5_components.py --demo  # 快速演示
python3 test_v5_components.py --test security  # 測試特定組件

# 測試兼容性
python3 scripts/project_update_integration_v5.py --demo
python3 scripts/project_update_integration_v5.py --project test --guidance-only
```

## 遷移時間表

### 階段 1: 評估和測試（1-2 天）
1. 運行測試套件確認兼容性
2. 在測試項目上驗證 v5.0 功能
3. 評估現有項目遷移需求

### 階段 2: 漸進遷移（3-5 天）
1. 先遷移安全性關鍵組件（SecurityValidator）
2. 再遷移 Git 操作（GitToolWrapper）
3. 最後遷移工作流程（ProjectUpdateGuidance）

### 階段 3: 完整切換（1-2 天）
1. 更新 SKILL.md 文檔
2. 培訓團隊使用新架構
3. 監控生產環境運行情況

## 常見問題

### Q1: 我的現有項目會受影響嗎？
**A:** 不會。v5.0 完全向後兼容。現有項目可以繼續使用 v4 兼容模式。

### Q2: 遷移後性能會下降嗎？
**A:** 不會。v5.0 優化了路徑檢測和 Token 估算，性能可能略有提升。

### Q3: 必須一次性遷移所有代碼嗎？
**A:** 不需要。支持漸進式遷移，可以逐個組件替換。

### Q4: 如果遇到問題如何回退？
**A:** 隨時可以設置 `use_old_components=True` 回退到 v4 兼容模式。

### Q5: 新架構需要學習成本嗎？
**A:** 有一定學習成本，但我們提供了完整的文檔和示例。核心概念是「技能提供指引，Agent 執行操作」。

## 技術細節

### 安全性改進詳解

#### 路徑驗證
```python
# 舊：簡單檢查
if ".." in path:  # 可能被繞過
    raise Error

# 新：完整驗證
validator = SecurityValidator(workspace_dir)
is_safe, error = validator.validate_path(path)
# 檢查：1) 在 workspace 內 2) 無目錄遍歷 3) 非敏感文件
```

#### 命令安全
```python
# 舊：直接執行
subprocess.run(command)  # 可能執行危險命令

# 新：命令清理
is_safe, sanitized, error = validator.sanitize_command(command)
# 檢查：1) 危險模式黑名單 2) Git 命令白名單 3) 路徑參數驗證
```

### 架構哲學轉變

#### v4.x: 技能作為「自動化機器」
- 技能直接執行所有操作
- 包含業務邏輯和執行邏輯
- 難以測試和維護

#### v5.0: 技能作為「工具箱」
- 技能提供工具和指引
- Agent 決定何時使用工具
- 清晰的責任分離
- 易於測試和擴展

## 遷移檢查清單

- [ ] 閱讀本遷移指南
- [ ] 運行測試套件 (`test_v5_components.py`)
- [ ] 在測試項目上驗證 v5.0 功能
- [ ] 更新配置（如有需要）
- [ ] 遷移關鍵代碼（逐步進行）
- [ ] 更新文檔（SKILL.md, README.md）
- [ ] 培訓團隊成員
- [ ] 監控生產環境

## 獲取幫助

如果在遷移過程中遇到問題：

1. **查閱文檔**：查看 `SKILL.md` 和本指南
2. **運行測試**：使用 `test_v5_components.py` 診斷問題
3. **檢查示例**：參考 `scripts/` 目錄中的示例代碼
4. **尋求支持**：聯繫開發團隊

---

*最後更新: 2026-03-16*
*版本: v5.0-migration-guide-1.0*