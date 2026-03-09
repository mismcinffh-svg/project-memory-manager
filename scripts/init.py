#!/usr/bin/env python3
"""
Project Memory Manager - 初始化腳本
通用版本：在任何OpenClaw Agent的workspace中運行
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def setup_logging():
    """設置日誌系統"""
    log_dir = Path.cwd() / "projects" / "_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"init_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def create_directory_structure(workspace: Path, logger):
    """創建目錄結構"""
    projects_dir = workspace / "projects"
    
    directories = [
        projects_dir,
        projects_dir / "_templates",
        projects_dir / "_logs",
        projects_dir / "_backups",
        workspace / "memory"
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
        logger.info(f"創建目錄: {directory}")
    
    return projects_dir

def create_memory_file(workspace: Path, logger):
    """創建極簡MEMORY.md"""
    memory_file = workspace / "MEMORY.md"
    
    if memory_file.exists():
        logger.info(f"MEMORY.md 已存在: {memory_file}")
        return False
    
    content = """# MEMORY.md - 核心記憶

## 項目記憶系統
項目內容存放於 projects/ 目錄
使用 memory_search("關鍵詞") 檢索項目內容

## 核心身份
<!-- 在此添加SOUL.md/USER.md中的核心內容 -->

## 關鍵決策
<!-- 在此添加關鍵決策，保持簡潔 -->
"""
    
    memory_file.write_text(content, encoding='utf-8')
    logger.info(f"創建 MEMORY.md: {memory_file}")
    return True

def create_index_file(projects_dir: Path, logger):
    """創建項目索引"""
    index_file = projects_dir / "INDEX.md"
    
    content = """# 項目索引

| 項目 | 關鍵詞 | 位置 | 狀態 | 創建時間 |
|------|--------|------|------|----------|
| 示例項目 | 示例,測試 | example/ | active | 2026-03-05 |
"""
    
    index_file.write_text(content, encoding='utf-8')
    logger.info(f"創建 INDEX.md: {index_file}")

def create_project_templates(projects_dir: Path, logger):
    """創建項目模板"""
    templates_dir = projects_dir / "_templates"
    
    templates = {
        "README.md": """# {project_name}

## 概述
{description}

## 目標
- [ ] 目標1
- [ ] 目標2
- [ ] 目標3

## 時間線
- **開始日期**: {created_date}
- **預計完成**: 
- **實際完成**: 

## 負責人
- 主要: 
- 協助: 

## 相關鏈接
- 
""",
        "technical.md": """# 技術細節

## 技術棧
- 

## 架構設計
- 

## 實現步驟
1. 
2. 
3. 

## 技術挑戰
- 

## 解決方案
- 
""",
        "decisions.md": """# 關鍵決策

## 決策記錄
| 日期 | 決策內容 | 決策者 | 理由 | 影響 |
|------|----------|--------|------|------|
| {created_date} | 項目創建 | 系統 | 自動創建 | 開始項目 |
""",
        "learnings.md": """# 學習總結

## 學習要點
- 

## 成功經驗
- 

## 失敗教訓
- 

## 改進建議
- 
""",
        "project.json": """{
  "name": "{project_name}",
  "slug": "{project_slug}",
  "description": "{description}",
  "status": "active",
  "created": "{created_iso}",
  "updated": "{created_iso}",
  "keywords": {keywords},
  "token_count": 0,
  "files": ["README.md", "technical.md", "decisions.md", "learnings.md"]
}
"""
    }
    
    for filename, template in templates.items():
        template_file = templates_dir / filename
        template_file.write_text(template, encoding='utf-8')
        logger.info(f"創建模板: {template_file}")

def create_config_file(skill_dir: Path, logger):
    """創建配置文件"""
    config_file = skill_dir / "config.json"
    
    config = {
        "auto_monitor": {
            "enabled": True,
            "threshold_tokens": 500,
            "check_interval_hours": 24,
            "last_check": None
        },
        "index": {
            "max_tokens": 200,
            "keywords_per_project": 3,
            "status_options": ["active", "inactive", "completed", "archived"]
        },
        "projects": {
            "default_status": "active",
            "max_projects_per_day": 10,
            "blacklisted_keywords": ["測試", "示例", "temp", "test"]
        },
        "system": {
            "version": "3.0.0",
            "initialized": datetime.now().isoformat(),
            "workspace": str(Path.cwd())
        }
    }
    
    config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8')
    logger.info(f"創建配置文件: {config_file}")

def main():
    """主函數"""
    logger = setup_logging()
    
    try:
        workspace = Path.cwd()
        logger.info(f"🚀 Project Memory Manager v3.0.0 - 初始化")
        logger.info(f"📁 工作空間: {workspace}")
        
        # 檢查是否為OpenClaw workspace
        openclaw_indicators = ["AGENTS.md", "SOUL.md", "USER.md", "MEMORY.md", ".openclaw"]
        has_indicators = any((workspace / indicator).exists() for indicator in openclaw_indicators)
        
        if not has_indicators:
            logger.warning("⚠️  未檢測到OpenClaw標誌文件，可能不在正確的workspace中")
            logger.warning(f"   當前目錄: {workspace}")
            response = input("是否繼續初始化？(y/n): ")
            if response.lower() != 'y':
                logger.info("初始化取消")
                return
        
        # 創建目錄結構
        projects_dir = create_directory_structure(workspace, logger)
        
        # 創建核心文件
        created = create_memory_file(workspace, logger)
        if created:
            logger.info("✅ 創建新的MEMORY.md（極簡版）")
        
        create_index_file(projects_dir, logger)
        create_project_templates(projects_dir, logger)
        
        # 創建技能配置
        skill_dir = Path(__file__).parent.parent
        create_config_file(skill_dir, logger)
        
        # 完成
        logger.info("🎉 初始化完成！")
        logger.info(f"📁 項目目錄: {projects_dir}")
        logger.info("📝 使用「開新項目 [名稱]」創建第一個項目")
        logger.info("🔍 系統將自動監測MEMORY.md的500tokens規則")
        
        print("\n" + "="*60)
        print("✅ Project Memory Manager 初始化成功！")
        print(f"📁 工作空間: {workspace}")
        print(f"📁 項目目錄: {projects_dir}")
        print("📝 使用命令: python3 scripts/create.py manual \"項目名稱\"")
        print("="*60)
        
    except Exception as e:
        logger.error(f"❌ 初始化失敗: {e}", exc_info=True)
        print(f"❌ 錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()