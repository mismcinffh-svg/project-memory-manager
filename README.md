# Project Memory Manager

**通用項目記憶管理系統：智能監測MEMORY.md，自動創建項目歸檔，高效索引管理**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 概述

**問題**：OpenClaw Agent的MEMORY.md文件會隨時間增長，導致上下文過載、響應變慢、記憶混亂。

**解決方案**：本技能實施「項目專櫃」架構：
1. **500 Tokens自動規則**：監測MEMORY.md，同一主題>500t自動創建項目歸檔
2. **高效索引系統**：INDEX.md一行一項目，關鍵詞優先，狀態標記
3. **用戶手動控制**：隨時說「開新項目 [名稱]」立即創建
4. **智能檢索**：使用 `memory_search("關鍵詞")` 跨項目查找

**兼容性**：完全通用設計，無硬編碼路徑，適用任何OpenClaw Agent（workspace-secretary, workspace-pm, workspace-coder等）。

## 核心功能

### 🚨 500 Tokens自動監測（已實現）
- **實時監測**：每次更新MEMORY.md時自動檢查
- **智能識別**：按主題分組內容，計算tokens總量
- **自動遷移**：>500t的主題自動創建項目+遷移內容
- **索引更新**：自動更新INDEX.md，保持同步

### 🎯 手動項目創建
- **簡單命令**：「開新項目 [項目名稱]」
- **完整結構**：自動創建4個標準文件（README.md, technical.md, decisions.md, learnings.md）
- **關鍵詞提取**：從項目名自動生成檢索關鍵詞
- **狀態管理**：active/inactive/completed狀態標記

### 📊 高效索引系統
- **極簡設計**：INDEX.md <200 tokens，一行一項目
- **關鍵詞優先**：方便 `memory_search()` 檢索
- **狀態可視化**：清晰標記項目進度
- **位置指引**：快速定位項目文件夾

### 🔍 智能檢索優化
- **跨項目搜索**：`memory_search("關鍵詞")` 檢索所有項目
- **類型過濾**：`memory_search("項目名 技術")` 查找技術細節
- **決策追溯**：`memory_search("項目名 決策")` 查找決策記錄

### 🎮 交互式設置嚮導 (v4.0.0 新增)
- **方向鍵導航**：使用 ↑↓←→ 鍵選擇，模仿 `openclaw config` 體驗
- **簡單顏色**：青/綠/黃/藍色顯示，增強視覺效果
- **進度條百分比**：實時顯示設置進度，清晰直觀
- **自動環境檢測**：智能識別 Git、GitHub CLI、Telegram 配置
- **雙模式支持**：curses 圖形界面失敗時自動回退到文本模式
- **配置持久化**：JSON 格式保存到 `~/.openclaw/project-memory-config.json`
- **安全設計**：不存儲敏感信息，支持環境變量和安全提示

## 🚀 快速開始

### 全新交互式設置嚮導 (v4.0.0+)

**無需命令行知識，零配置上手！**

```bash
# 1. 運行設置嚮導（推薦）
cd project-memory-manager
python scripts/setup.py
```

設置嚮導提供：
- **方向鍵選擇**：使用 ↑↓←→ 鍵導航，無需打字
- **進度條顯示**：實時百分比進度，清晰直觀
- **自動檢測**：Git、GitHub CLI、Telegram 自動配置
- **雙模式支持**：圖形界面失敗時自動回退到文本模式

**界面預覽**：
```
┌─────────────────────────────────────┐
│    Project Memory Manager 設置嚮導    │
├─────────────────────────────────────┤
│  請選擇設置模式：                    │
│                                      │
│    > 快速設置（推薦） <              │
│      自動檢測並配置最常用選項        │
│                                      │
│      高級設置                        │
│      自定義每個配置選項              │
│                                      │
│      檢查當前配置                    │
│      查看和驗證現有配置              │
└─────────────────────────────────────┘
方向鍵: 選擇 | 回車: 確認 | ESC: 返回
```

### 傳統安裝方法
cp project-memory-manager.skill ~/.openclaw/workspace-[your-agent]/

# 2. 讓Agent閱讀技能文件
read({ path: "project-memory-manager.skill" })

# 3. 系統自動初始化
# 4. 確認安裝完成
```

#### 方法二：手動安裝（適用於調試）
```bash
# 1. 創建技能目錄
mkdir -p ~/.openclaw/workspace-[your-agent]/skills/project-memory-manager/{scripts,references}

# 2. 複製所有文件
cp -r skills/project-memory-manager/* ~/.openclaw/workspace-[your-agent]/skills/project-memory-manager/

# 3. 閱讀技能文檔
read({ path: "~/.openclaw/workspace-[your-agent]/skills/project-memory-manager/SKILL.md" })
```

### 基本使用

```bash
# 手動創建新項目
開新項目 AI賺錢研究

# 查看項目索引
read({ path: "projects/INDEX.md" })

# 搜索項目內容
memory_search("AI賺錢 技術")
```

## 項目結構

```
project-memory-manager/
├── SKILL.md              # 核心技能文檔
├── config.json           # 配置模板
├── scripts/              # Python腳本
│   ├── create.py        # 項目創建腳本
│   ├── init.py          # 初始化腳本
│   ├── setup.py         # 設置嚮導入口點
│   ├── demo_menu.py     # 演示腳本
│   └── interactive/     # 交互式模塊
│       ├── menu_engine.py    # 選單引擎
│       ├── progress_bar.py   # 進度條系統
│       └── setup_wizard.py   # 設置嚮導核心
├── references/           # 參考文檔
│   ├── best-practices.md # 最佳實踐
│   └── troubleshooting.md # 故障排除
├── .gitignore           # Git忽略規則
├── LICENSE              # MIT許可證
└── README.md            # 本文件
```

## 版本歷史

詳見 [CHANGELOG.md](CHANGELOG.md)

## 貢獻指南

歡迎提交問題報告和功能請求。請在提交PR前閱讀 [CONTRIBUTING.md](CONTRIBUTING.md)（即將添加）。

## 許可證

本項目採用 MIT 許可證 - 詳見 [LICENSE](LICENSE) 文件。
<!-- Last test commit: 2026-03-10 13:20:42 -->

<!-- Telegram notification test: 2026-03-10 13:40:33 -->

<!-- 遷移測試成功: 2026-03-10 14:41:16 -->
