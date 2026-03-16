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

### ⚠️ 已知問題（已在v5.0.1中修復 ✅）
1. **指引執行層缺失**：OpenClawToolsWrapper只生成指引，缺乏執行指導 → ✅ 已修復：添加GuidanceExecutor
2. **文檔不一致**：CHANGELOG.md未更新，SKILL.md部分過時 → ✅ 已修復：更新所有文檔，添加INSTALLATION.md
3. **測試覆蓋不足**：缺乏真實工具調用和邊界情況測試 → ✅ 已修復：添加GuidanceExecutor測試和邊界情況測試

---

## [5.0.1] - 2026-03-16

### 🐛 錯誤修復與改進

#### 🔧 指引執行層 (核心修復)
- **新增 GuidanceExecutor**: 完整的工具執行輔助類，解決「指引 vs 實際執行」的差距
- **執行方案生成**: `OpenClawToolsWrapper.get_execution_scheme()` 提供完整執行指導
- **示例代碼生成**: `generate_execution_example()` 生成 Python/JSON 示例代碼
- **參數轉換幫助**: 標準化的工具參數轉換和錯誤處理指南

#### 📚 文檔完善
- **SKILL.md 全面更新**: 反映 v5.0 架構，添加 v5.0 使用指南
- **CHANGELOG.md 更新**: 添加 v5.0.0 和 v5.0.1 完整記錄
- **新增 INSTALLATION.md**: 完整的安裝和配置指南
- **架構對比文檔**: 明確區分 v5.0 指引模式和 v4.x 兼容模式

#### 🧪 測試強化
- **新增 GuidanceExecutor 測試**: 驗證指引執行層功能
- **新增邊界情況測試**: 測試極長路徑、危險命令變體、Git命令白名單
- **測試數量增加**: 從 6 個測試增加到 8 個測試，全部通過
- **集成測試改進**: 驗證 OpenClawToolsWrapper 與 GuidanceExecutor 的集成

#### 🛠️ 技術改進
- **Token 估算算法完善**: 完全實現中英文混合精準估算算法
- **安全驗證增強**: 改進 Git 命令白名單和危險命令檢測
- **錯誤處理優化**: 更好的錯誤消息和恢復策略
- **向後兼容性驗證**: 確保 v4.x 兼容模式完全可用

#### 🎯 解決的審查問題 (Sergio 指出)
1. ✅ **OpenClaw 工具整合未完成** → 新增 GuidanceExecutor 提供完整執行方案
2. ✅ **Token 估算算法簡單** → 實現中英文混合精準算法
3. ✅ **文檔不一致** → 更新所有文檔，保持一致性
4. ✅ **測試覆蓋不足** → 新增 2 個測試類別，覆蓋率提升
5. ✅ **錯誤處理和恢復薄弱** → 增強事務支持和錯誤降級
6. ✅ **配置管理混亂** → 添加 INSTALLATION.md 提供清晰配置指南

#### 📊 測試狀態
```
SecurityValidator              ✅ 通過
GitToolWrapper                 ✅ 通過  
OpenClawToolsWrapper           ✅ 通過
ProjectUpdateGuidance          ✅ 通過
ProjectUpdateIntegrationV5     ✅ 通過
向後兼容性                          ✅ 通過
GuidanceExecutor               ✅ 通過 (新增)
邊界情況測試                         ✅ 通過 (新增)
====================================
總計: 8 通過, 0 失敗 🎉
```

#### 🔄 遷移建議
- **新項目**: 直接使用 v5.0.1 指引架構 (`use_old_components=False`)
- **現有項目**: 使用兼容模式 (`use_old_components=True`) 無縫遷移
- **漸進式遷移**: 使用 GuidanceExecutor 逐步替換舊代碼

#### 👥 貢獻者
- **Nana (Sergio's Secretary)**: 指引執行層實現、文檔更新、測試強化
- **Sergio (Banksy Maverick)**: 詳細技術審查、問題識別、改進指導

---

## [5.0.0] - 2026-03-16

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
