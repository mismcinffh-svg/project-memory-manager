# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.1.0] - 2026-03-11

### Added
- **對話摘要系統**：自動檢測「更新版本」、「同步上GitHub」等關鍵詞，觸發專櫃內容更新
- **版本管理模塊**：自動版本號遞增（major/minor/patch）、CHANGELOG自動更新、Git操作集成
- **文件結構升級**：`_latest` + `_history` 分離結構（learnings_latest.md, learnings_history.md, technical_latest.md, technical_history.md）
- **完整更新工作流程**：專櫃摘要更新 + 版本遞增 + CHANGELOG更新 + GitHub同步一體化

### New Features
- **觸發檢測**：支持「commit」、「上github」、「git push」、「更新版本」、「version update」、「發布」等關鍵詞
- **項目識別**：自動從消息提取項目名，或從最近項目推斷
- **用戶確認**：詢問「要不要更新項目專櫃內容」，提供控制權
- **智能版本遞增**：根據更新類型自動選擇major/minor/patch遞增
- **Git自動化**：自動執行 git add/commit/tag/push 操作

### Technical Components
- **對話摘要引擎**：`conversation_summary.py` - 生成專櫃摘要內容
- **版本管理器**：`version_manager.py` - 處理版本遞增與CHANGELOG更新
- **集成協調器**：`project_update_integration.py` - 協調完整工作流程
- **文件結構升級**：更新create.py支持分離文件結構

### Workflow Integration
- **專櫃更新路徑**：用戶確認後 → sessions_spawn生成摘要 → 更新_latest/_history文件
- **版本更新路徑**：自動遞增版本號 → 更新CHANGELOG → 執行Git操作
- **GitHub同步**：自動推送代碼和標籤到GitHub倉庫
- **錯誤處理**：各步驟獨立錯誤處理，失敗時繼續其他操作

### Compatibility
- **向後兼容**：現有項目自動適配新文件結構
- **配置升級**：config.json自動更新文件列表
- **無破壞性更新**：現有項目數據完全保留
- **漸進式採用**：用戶可選擇是否啟用對話摘要功能

## [4.0.0] - 2026-03-10

### Added
- **交互式設置嚮導**：方向鍵選擇（↑↓←→）、簡單顏色、進度條百分比
- **智能環境檢測**：自動識別 Git、GitHub CLI、Telegram Bot 配置
- **雙模式界面**：curses 圖形界面 + 文本模式回退，100% 兼容
- **配置持久化**：JSON 格式保存到 `~/.openclaw/project-memory-config.json`
- **Git 自動化增強**：post-commit 鉤子實現零配置自動推送

### User Experience
- **模仿 openclaw config**：相同交互邏輯和視覺風格
- **快速設置流程**：5步完成 Git、GitHub、Telegram 配置
- **進度可視化**：實時百分比進度條和旋轉指示器
- **零技術門檻**：新手只需按箭頭和回車鍵

### Technical Features
- **選單引擎**：`menu_engine.py` 支持方向鍵導航和顏色顯示
- **進度條系統**：`progress_bar.py` 提供百分比進度和多步驟追蹤
- **設置嚮導核心**：`setup_wizard.py` 實現完整配置流程
- **環境檢測器**：自動檢測系統環境和第三方工具

### GitHub Integration
- **安全遷移策略**：單項目遷移 + 24小時觀察期避免風控
- **自動化推送**：每次提交後自動同步到 GitHub
- **Telegram 通知**：即時反饋所有 Git 操作
- **賬戶安全**：支持密碼修改和 2FA 啟用建議

## [3.0.0] - 2026-03-09

### Added
- **完整技能架構**：SKILL.md + 配置模板 + Python腳本
- **500 Tokens自動監測**：智能識別主題並自動創建項目歸檔
- **手動項目創建**：支持「開新項目 [名稱]」命令
- **高效索引系統**：INDEX.md一行一項目，關鍵詞優先
- **智能檢索優化**：跨項目memory_search()支持

### Technical Features
- **Python腳本**：create.py（項目創建）和 init.py（初始化）
- **配置模板**：config.json 用於通用配置
- **參考文檔**：best-practices.md 和 troubleshooting.md
- **兼容性**：完全通用設計，適用任何OpenClaw Agent

### Documentation
- **完整技能文檔**：SKILL.md 包含詳細使用指南
- **安裝指南**：支持標準技能安裝和手動安裝
- **最佳實踐**：參考文檔提供使用建議

## [2.0.0] - 2026-03-07 (內部版本)

### Added
- 初始項目概念和原型設計
- 基本項目創建功能
- 初步索引系統

## [1.0.0] - 2026-03-05 (概念版本)

### Added
- 項目記憶管理概念提出
- 初步架構設計
- 基礎文檔結構