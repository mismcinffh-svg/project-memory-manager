# Project Memory Manager 更新日誌

所有值得注意的變更都會記錄在此文件中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-Hant/1.0.0/)，
並且本項目遵循 [語義化版本](https://semver.org/lang/zh-TW/)。

## [5.0.0] - 2026-03-16

### 🚀 重大變更（完全架構重構）

Project Memory Manager v5.0.0 是完全基於 OpenClaw 哲學的重構版本：「技能提供指引，Agent 執行操作」。這個版本解決了 v4.x 的安全問題和架構缺陷。

#### 🔒 安全性架構
- **移除所有 `subprocess` 調用**：8個直接命令執行點全部移除
- **安全驗證模塊**：`SecurityValidator` 提供路徑白名單驗證 + 命令黑名單過濾
- **Git操作封裝**：`GitToolWrapper` 生成安全的 `exec` 工具指引
- **零風險命令執行**：所有命令都經過安全檢查，防止目錄遍歷攻擊

#### 🛠️ 真實數據源
- **消除模擬數據**：完全移除所有 mock data 和模擬函數
- **OpenClaw工具封裝**：`OpenClawToolsWrapper` 提供真實工具調用指引
- **真實會話歷史**：使用 `sessions_history` 獲取真實對話數據
- **真實子會話生成**：使用 `sessions_spawn` 啟動真實摘要生成

#### 🏗️ 架構哲學轉變
- **指引驅動架構**：技能只提供「如何操作」的指引，不直接執行
- **責任清晰分離**：技能（工具箱）vs Agent（工具使用者）
- **符合OpenClaw哲學**：嚴格遵循「技能提供指引，Agent執行操作」原則

#### 🔄 完全向後兼容
- **雙架構支持**：`use_old_components=True/False` 無縫切換
- **漸進式遷移**：可逐個組件替換，無需一次性重寫
- **兼容現有項目**：所有 v4.x 項目繼續正常工作

#### 🧩 新增組件
- **`SecurityValidator`**：安全驗證模塊（路徑 + 命令）
- **`GitToolWrapper`**：安全 Git 操作指引生成器
- **`OpenClawToolsWrapper`**：真實 OpenClaw 工具調用指引
- **`ProjectUpdateGuidance`**：智能工作流程指引生成器
- **`ProjectUpdateIntegrationV5`**：新舊架構兼容層
- **`GuidanceExecutor`**：指引執行輔助類（v5.0.1新增）

#### 📊 測試與文檔
- **完整測試套件**：6個核心組件全部通過測試
- **架構對比演示**：`demo_v5_vs_v4.py` 展示新舊架構差異
- **遷移指南**：`MIGRATION_GUIDE.md` 提供詳細遷移步驟
- **版本文檔**：`VERSION.md` 記錄完整版本信息

### ⚠️ 已知問題（在v5.0.1中修復）
1. **指引執行層缺失**：OpenClawToolsWrapper只生成指引，缺乏執行指導
2. **文檔不一致**：CHANGELOG.md未更新，SKILL.md部分過時
3. **測試覆蓋不足**：缺乏真實工具調用和邊界情況測試

### 🔧 技術細節
- **Python要求**：3.8+
- **OpenClaw要求**：支持 `exec`, `sessions_history`, `sessions_spawn` 工具
- **架構標誌**：`use_old_components=True`（兼容模式）或 `False`（新架構）

### 👥 貢獻者
- **Nana (Sergio's Secretary)**：安全性架構、工具封裝、測試套件
- **Coder Agent**：核心管理器模塊、原子操作、增強日誌
- **Sergio (Banksy Maverick)**：詳細審查、問題發現、改進指導

---

## [4.6.0] - 2026-03-13

### ✨ 功能更新

- 更新專櫃摘要內容
- 自動版本遞增與CHANGELOG更新



所有值得注意的變更都會記錄在此文件中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-Hant/1.0.0/)，
並且本項目遵循 [語義化版本](https://semver.org/lang/zh-TW/)。

## [4.5.0] - 2026-03-12

### ✨ 功能更新

- 更新專櫃摘要內容
- 自動版本遞增與CHANGELOG更新


## [2.1.0] - 2026-03-11

### ✨ 功能更新

- 更新專櫃摘要內容
- 自動版本遞增與CHANGELOG更新
