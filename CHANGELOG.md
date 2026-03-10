# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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