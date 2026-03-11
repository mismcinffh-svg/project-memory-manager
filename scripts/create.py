#!/usr/bin/env python3
"""
Project Memory Manager - 項目創建與管理工具
支持手動創建、自動監測、狀態管理等功能
"""

import os
import sys
import re
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any

# 設置日誌
def setup_logger(name: str = "project-memory-manager") -> logging.Logger:
    """設置日誌記錄器"""
    log_dir = Path.cwd() / "projects" / "_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 避免重複添加handler
    if not logger.handlers:
        # 文件handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()

class ProjectManager:
    """項目管理器"""
    
    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or Path.cwd()
        self.projects_dir = self.workspace / "projects"
        self.memory_file = self.workspace / "MEMORY.md"
        self.index_file = self.projects_dir / "INDEX.md"
        
        # 加載配置
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """加載配置文件"""
        config_file = Path(__file__).parent.parent / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加載配置失敗: {e}")
        
        # 默認配置
        return {
            "auto_monitor": {
                "enabled": True,
                "threshold_tokens": 500,
                "check_interval_hours": 24
            },
            "index": {
                "max_tokens": 200,
                "keywords_per_project": 3
            },
            "projects": {
                "default_status": "active",
                "blacklisted_keywords": ["測試", "示例", "temp", "test"]
            }
        }
    
    def save_config(self):
        """保存配置"""
        config_file = Path(__file__).parent.parent / "config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存配置失敗: {e}")
    
    def slugify(self, name: str) -> str:
        """生成文件夾友好的名稱"""
        slug = name.lower().strip()
        # 移除特殊字符
        slug = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', slug)
        # 替換空格為連字符
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def estimate_tokens(self, text: str) -> int:
        """簡單估算tokens（字符數 ÷ 3）"""
        return len(text) // 3
    
    def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """從文本中提取關鍵詞"""
        # 中文詞語正則
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,}', text.lower())
        # 英文單詞正則
        english_words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        
        keywords = chinese_words + english_words
        
        # 過濾黑名單
        blacklist = self.config["projects"].get("blacklisted_keywords", [])
        keywords = [k for k in keywords if k not in blacklist and len(k) > 1]
        
        # 去重並按頻率排序
        from collections import Counter
        keyword_counts = Counter(keywords)
        sorted_keywords = [k for k, _ in keyword_counts.most_common(max_keywords)]
        
        return sorted_keywords
    
    def manual_create(self, project_name: str, description: str = "") -> Path:
        """手動創建項目"""
        logger.info(f"手動創建項目: {project_name}")
        
        # 生成slug
        project_slug = self.slugify(project_name)
        project_path = self.projects_dir / project_slug
        
        # 檢查是否已存在
        if project_path.exists():
            logger.warning(f"項目已存在: {project_path}")
            return project_path
        
        # 創建項目目錄
        project_path.mkdir(parents=True, exist_ok=True)
        
        # 提取關鍵詞
        keywords = self.extract_keywords(f"{project_name} {description}")
        
        # 項目配置
        project_config = {
            "name": project_name,
            "slug": project_slug,
            "description": description,
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "status": self.config["projects"]["default_status"],
            "keywords": keywords,
            "token_count": 0,
            "files": ["README.md", "technical.md", "decisions.md", "learnings.md"]
        }
        
        # 保存配置
        config_file = project_path / "project.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(project_config, f, indent=2, ensure_ascii=False)
        
        # 創建項目文件
        self.create_project_files(project_path, project_name, description)
        
        # 更新索引
        self.update_index(project_config)
        
        logger.info(f"✅ 項目創建成功: {project_name}")
        logger.info(f"📁 位置: {project_path}")
        
        return project_path
    
    def create_project_files(self, project_path: Path, project_name: str, description: str):
        """創建項目文件 (_latest + _history 分離結構)"""
        templates_dir = self.projects_dir / "_templates"
        
        # 如果模板目錄不存在，創建默認模板
        if not templates_dir.exists():
            self.create_default_templates()
        
        # 變量替換映射
        variables = {
            "project_name": project_name,
            "project_slug": project_path.name,
            "description": description,
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "created_iso": datetime.now().isoformat(),
            "keywords": json.dumps([project_name], ensure_ascii=False)
        }
        
        # 創建標準文件（_latest + _history 分離結構）
        file_list = [
            "README.md",
            "decisions.md",           # 決策完整歷史
            "learnings_latest.md",    # 最新學習摘要
            "learnings_history.md",   # 學習歷史記錄
            "technical_latest.md",    # 最新技術摘要
            "technical_history.md"    # 技術歷史記錄
        ]
        
        for filename in file_list:
            template_file = templates_dir / filename
            output_file = project_path / filename
            
            if template_file.exists():
                # 從模板讀取並替換變量
                template_content = template_file.read_text(encoding='utf-8')
                content = template_content.format(**variables)
            else:
                # 創建默認內容
                if filename.endswith("_latest.md"):
                    base_name = filename.replace("_latest.md", "")
                    content = f"# {base_name.capitalize()} - 最新摘要\n\n"
                    content += f"項目: {project_name}\n"
                    content += f"創建時間: {variables['created_date']}\n\n"
                    content += "## 最新更新\n\n"
                elif filename.endswith("_history.md"):
                    base_name = filename.replace("_history.md", "")
                    content = f"# {base_name.capitalize()} - 歷史記錄\n\n"
                    content += f"項目: {project_name}\n"
                    content += f"創建時間: {variables['created_date']}\n\n"
                    content += "## 歷史記錄\n\n"
                else:
                    content = f"# {filename.replace('.md', '')} - {project_name}\n\n"
                    content += f"創建時間: {variables['created_date']}\n\n"
            
            output_file.write_text(content, encoding='utf-8')
            logger.debug(f"創建文件: {output_file}")
    
    def create_default_templates(self):
        """創建默認模板"""
        templates_dir = self.projects_dir / "_templates"
        templates_dir.mkdir(exist_ok=True)
        
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
            "decisions.md": """# 關鍵決策

## 決策記錄
| 日期 | 決策內容 | 決策者 | 理由 | 影響 |
|------|----------|--------|------|------|
| {created_date} | 項目創建 | 系統 | 自動創建 | 開始項目 |
""",
            "learnings_latest.md": """# Learnings - 最新摘要

## 項目
{project_name}

## 創建時間
{created_date}

## 最新更新
*[此文件由對話摘要系統自動更新，包含項目最新學習摘要]*

### 核心學習
- 

### 成功經驗
- 

### 改進建議
- 

### 應用場景
- 

---
*更新時間: {created_date}*
""",
            "learnings_history.md": """# Learnings - 歷史記錄

## 項目
{project_name}

## 創建時間
{created_date}

## 歷史記錄
*[此文件記錄項目所有學習歷史，由對話摘要系統自動追加]*


---
*此文件為歷史記錄，請勿刪除已有內容，只追加新記錄*
""",
            "technical_latest.md": """# Technical - 最新摘要

## 項目
{project_name}

## 創建時間
{created_date}

## 最新更新
*[此文件由對話摘要系統自動更新，包含項目最新技術摘要]*

### 技術架構
- 

### 實現方案
- 

### 技術挑戰與解決
- 

### 性能優化
- 

---
*更新時間: {created_date}*
""",
            "technical_history.md": """# Technical - 歷史記錄

## 項目
{project_name}

## 創建時間
{created_date}

## 歷史記錄
*[此文件記錄項目所有技術歷史，由對話摘要系統自動追加]*


---
*此文件為歷史記錄，請勿刪除已有內容，只追加新記錄*
"""
        }
        
        for filename, content in templates.items():
            template_file = templates_dir / filename
            template_file.write_text(content, encoding='utf-8')
        
        logger.info(f"創建默認模板: {templates_dir}")
    
    def update_index(self, project_config: Dict[str, Any]):
        """更新INDEX.md"""
        if not self.index_file.exists():
            logger.error(f"索引文件不存在: {self.index_file}")
            return
        
        try:
            content = self.index_file.read_text(encoding='utf-8')
            lines = content.splitlines()
            
            # 查找表格開始行
            table_start = -1
            for i, line in enumerate(lines):
                if line.strip().startswith("| 項目 |"):
                    table_start = i
                    break
            
            if table_start == -1:
                logger.error("未找到索引表格")
                return
            
            # 準備新行
            keywords = ", ".join(project_config["keywords"][:3])
            new_row = f"| {project_config['name']} | {keywords} | {project_config['slug']}/ | {project_config['status']} | {project_config['created'][:10]} |\n"
            
            # 檢查是否已存在
            existing_line = -1
            for i in range(table_start + 1, len(lines)):
                if f"| {project_config['name']} |" in lines[i]:
                    existing_line = i
                    break
            
            if existing_line != -1:
                # 更新現有行
                lines[existing_line] = new_row
                logger.info(f"更新索引行: {project_config['name']}")
            else:
                # 插入新行（在表格標題後）
                insert_pos = table_start + 1
                while insert_pos < len(lines) and lines[insert_pos].strip().startswith("|"):
                    insert_pos += 1
                
                lines.insert(insert_pos, new_row)
                logger.info(f"添加索引行: {project_config['name']}")
            
            # 檢查token數量
            new_content = "\n".join(lines)
            if self.estimate_tokens(new_content) > self.config["index"]["max_tokens"]:
                logger.warning(f"索引文件超過{self.config['index']['max_tokens']}tokens，建議清理")
            
            # 保存
            self.index_file.write_text(new_content, encoding='utf-8')
            logger.info(f"索引更新完成: {self.index_file}")
            
        except Exception as e:
            logger.error(f"更新索引失敗: {e}")
    
    def analyze_memory(self, threshold_tokens: int = 500) -> List[Dict[str, Any]]:
        """分析MEMORY.md，識別超過閾值的主題"""
        if not self.memory_file.exists():
            logger.warning(f"MEMORY.md不存在: {self.memory_file}")
            return []
        
        try:
            content = self.memory_file.read_text(encoding='utf-8')
            lines = content.splitlines()
            
            # 簡單的主題識別：按時間戳和段落分組
            topics = []
            current_topic = []
            current_tokens = 0
            
            for line in lines:
                line_tokens = self.estimate_tokens(line)
                
                # 檢測主題邊界：空行、日期標記、標題等
                is_boundary = (
                    not line.strip() or
                    line.startswith("# ") or
                    line.startswith("## ") or
                    re.match(r'^\d{4}-\d{2}-\d{2}', line.strip())
                )
                
                if is_boundary and current_topic:
                    if current_tokens >= threshold_tokens:
                        topic_text = "\n".join(current_topic)
                        topics.append({
                            "text": topic_text,
                            "tokens": current_tokens,
                            "keywords": self.extract_keywords(topic_text),
                            "lines": len(current_topic)
                        })
                    current_topic = []
                    current_tokens = 0
                
                current_topic.append(line)
                current_tokens += line_tokens
            
            # 檢查最後一個主題
            if current_topic and current_tokens >= threshold_tokens:
                topic_text = "\n".join(current_topic)
                topics.append({
                    "text": topic_text,
                    "tokens": current_tokens,
                    "keywords": self.extract_keywords(topic_text),
                    "lines": len(current_topic)
                })
            
            logger.info(f"發現 {len(topics)} 個超過{threshold_tokens}tokens的主題")
            return topics
            
        except Exception as e:
            logger.error(f"分析MEMORY.md失敗: {e}")
            return []
    
    def auto_migrate(self, threshold_tokens: int = 500, dry_run: bool = False) -> List[Path]:
        """自動遷移超過閾值的主題到項目"""
        logger.info(f"自動遷移開始 (閾值: {threshold_tokens}t, 乾跑模式: {dry_run})")
        
        topics = self.analyze_memory(threshold_tokens)
        migrated_projects = []
        
        for i, topic in enumerate(topics):
            # 生成項目名稱
            if topic["keywords"]:
                project_name = f"{topic['keywords'][0]}-{datetime.now().strftime('%Y%m%d')}-{i+1}"
            else:
                project_name = f"主題-{datetime.now().strftime('%Y%m%d')}-{i+1}"
            
            description = f"自動從MEMORY.md遷移，{topic['tokens']}tokens，{topic['lines']}行"
            
            logger.info(f"遷移主題 {i+1}: {project_name} ({topic['tokens']}t)")
            
            if not dry_run:
                try:
                    # 創建項目
                    project_path = self.manual_create(project_name, description)
                    
                    # 將主題內容保存到項目文件
                    content_file = project_path / "migrated_content.md"
                    content_file.write_text(topic["text"], encoding='utf-8')
                    
                    migrated_projects.append(project_path)
                    logger.info(f"✅ 遷移完成: {project_name}")
                    
                except Exception as e:
                    logger.error(f"遷移失敗: {e}")
            else:
                logger.info(f"乾跑: 將創建項目 '{project_name}'")
        
        if not dry_run and migrated_projects:
            # 更新自動檢查時間
            self.config["auto_monitor"]["last_check"] = datetime.now().isoformat()
            self.save_config()
            
            logger.info(f"🎉 自動遷移完成，創建了 {len(migrated_projects)} 個項目")
        
        return migrated_projects
    
    def check_status(self) -> Dict[str, Any]:
        """檢查系統狀態"""
        status = {
            "workspace": str(self.workspace),
            "memory_file_exists": self.memory_file.exists(),
            "projects_dir_exists": self.projects_dir.exists(),
            "index_file_exists": self.index_file.exists(),
            "config_loaded": bool(self.config),
            "auto_monitor_enabled": self.config.get("auto_monitor", {}).get("enabled", False),
            "last_auto_check": self.config.get("auto_monitor", {}).get("last_check"),
            "project_count": 0,
            "total_tokens": 0
        }
        
        # 統計項目
        if self.projects_dir.exists():
            projects = [d for d in self.projects_dir.iterdir() if d.is_dir() and not d.name.startswith('_')]
            status["project_count"] = len(projects)
            
            # 估算總tokens
            for project_dir in projects:
                for md_file in project_dir.glob("*.md"):
                    try:
                        content = md_file.read_text(encoding='utf-8')
                        status["total_tokens"] += self.estimate_tokens(content)
                    except:
                        pass
        
        # 檢查MEMORY.md大小
        if self.memory_file.exists():
            try:
                content = self.memory_file.read_text(encoding='utf-8')
                status["memory_tokens"] = self.estimate_tokens(content)
                status["memory_lines"] = len(content.splitlines())
            except Exception as e:
                status["memory_error"] = str(e)
        
        return status
    
    def rebuild_index(self):
        """重建索引"""
        logger.info("重建索引...")
        
        if not self.projects_dir.exists():
            logger.error("項目目錄不存在")
            return
        
        # 收集所有項目
        projects = []
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('_'):
                config_file = project_dir / "project.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            project_config = json.load(f)
                            projects.append(project_config)
                    except Exception as e:
                        logger.error(f"讀取項目配置失敗 {project_dir}: {e}")
        
        # 創建新索引
        index_content = """# 項目索引

| 項目 | 關鍵詞 | 位置 | 狀態 | 創建時間 |
|------|--------|------|------|----------|
"""
        
        for project in sorted(projects, key=lambda x: x.get("created", ""), reverse=True):
            keywords = ", ".join(project.get("keywords", [])[:3])
            status = project.get("status", "active")
            created = project.get("created", "")[:10]
            
            index_content += f"| {project['name']} | {keywords} | {project['slug']}/ | {status} | {created} |\n"
        
        # 保存
        self.index_file.write_text(index_content, encoding='utf-8')
        logger.info(f"✅ 索引重建完成，包含 {len(projects)} 個項目")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="項目記憶管理器")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 手動創建命令
    manual_parser = subparsers.add_parser("manual", help="手動創建項目")
    manual_parser.add_argument("name", help="項目名稱")
    manual_parser.add_argument("description", nargs="?", default="", help="項目描述")
    
    # 自動遷移命令
    auto_parser = subparsers.add_parser("auto", help="自動遷移MEMORY.md內容")
    auto_parser.add_argument("--threshold", type=int, default=500, help="tokens閾值")
    auto_parser.add_argument("--dry-run", action="store_true", help="乾跑模式（不實際創建）")
    
    # 狀態檢查命令
    status_parser = subparsers.add_parser("status", help="檢查系統狀態")
    
    # 重建索引命令
    rebuild_parser = subparsers.add_parser("rebuild-index", help="重建INDEX.md")
    
    # 分析命令
    analyze_parser = subparsers.add_parser("analyze", help="分析MEMORY.md")
    analyze_parser.add_argument("--threshold", type=int, default=500, help="tokens閾值")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = ProjectManager()
    
    try:
        if args.command == "manual":
            project_path = manager.manual_create(args.name, args.description)
            print(f"✅ 項目創建成功: {project_path}")
            
        elif args.command == "auto":
            projects = manager.auto_migrate(args.threshold, args.dry_run)
            if args.dry_run:
                print(f"🔍 乾跑模式: 將創建 {len(projects)} 個項目")
            else:
                print(f"🎉 自動遷移完成，創建了 {len(projects)} 個項目")
                for p in projects:
                    print(f"  - {p}")
        
        elif args.command == "status":
            status = manager.check_status()
            print("📊 系統狀態:")
            print(f"  工作空間: {status['workspace']}")
            print(f"  MEMORY.md: {'✅' if status['memory_file_exists'] else '❌'}")
            if 'memory_tokens' in status:
                print(f"    Tokens: {status['memory_tokens']}t, 行數: {status['memory_lines']}")
            print(f"  項目目錄: {'✅' if status['projects_dir_exists'] else '❌'}")
            print(f"  項目數量: {status['project_count']}")
            print(f"  總Tokens: {status['total_tokens']}t")
            print(f"  自動監測: {'✅' if status['auto_monitor_enabled'] else '❌'}")
            if status['last_auto_check']:
                print(f"  最後檢查: {status['last_auto_check']}")
        
        elif args.command == "rebuild-index":
            manager.rebuild_index()
            print("✅ 索引重建完成")
        
        elif args.command == "analyze":
            topics = manager.analyze_memory(args.threshold)
            print(f"📊 MEMORY.md分析 (閾值: {args.threshold}t):")
            print(f"  發現 {len(topics)} 個超過閾值的主題")
            for i, topic in enumerate(topics):
                print(f"  主題 {i+1}: {topic['tokens']}tokens, {topic['lines']}行")
                print(f"    關鍵詞: {', '.join(topic['keywords'][:3])}")
        
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"命令執行失敗: {e}", exc_info=True)
        print(f"❌ 錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()