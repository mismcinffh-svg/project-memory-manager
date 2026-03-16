#!/usr/bin/env python3
"""
項目管理器 - 核心項目CRUD操作 + 事務支持

基於Coder Agent的設計要求：
1. 完整的項目CRUD操作
2. 事務支持
3. 與現有項目專櫃的兼容性
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from ..utils.file_ops import Transaction, read_file_safe, write_file_safe, FileLock
from ..utils.logging import log_performance

logger = logging.getLogger(__name__)


class ProjectManager:
    """項目管理器"""
    
    def __init__(self, workspace_dir: Optional[Path] = None):
        """
        初始化項目管理器
        
        Args:
            workspace_dir: 工作空間目錄（包含projects/）
        """
        if workspace_dir is None:
            # 嘗試從環境變量獲取
            import os
            workspace_env = os.getenv('OPENCLAW_WORKSPACE')
            if workspace_env:
                workspace_dir = Path(workspace_env)
            else:
                # 默認：當前目錄
                workspace_dir = Path.cwd()
        
        self.workspace_dir = Path(workspace_dir)
        self.projects_dir = self.workspace_dir / "projects"
        
        # 確保目錄存在
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"項目管理器初始化: workspace={self.workspace_dir}")
        
    @log_performance(threshold_ms=100)
    def create_project(self, name: str, slug: Optional[str] = None, 
                      description: str = "", **kwargs) -> Dict[str, Any]:
        """
        創建新項目
        
        Args:
            name: 項目名稱
            slug: 項目slug（URL友好，自動生成）
            description: 項目描述
            **kwargs: 額外屬性
            
        Returns:
            項目配置字典
        """
        if slug is None:
            # 生成slug：小寫、去空格、替換非字母數字
            import re
            slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        
        project_dir = self.projects_dir / slug
        
        # 檢查是否已存在
        if project_dir.exists():
            logger.warning(f"項目已存在: {slug}")
            return self.get_project(slug)
        
        # 創建項目目錄
        project_dir.mkdir(parents=True)
        
        # 創建項目配置
        project_config = {
            "name": name,
            "slug": slug,
            "description": description,
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "status": "active",
            "keywords": [],
            "token_count": 0,
            "files": ["README.md"],
            "last_summary_update": None,
            **kwargs
        }
        
        # 保存配置
        config_path = project_dir / "project.json"
        with Transaction() as txn:
            txn.backup_file(config_path) if config_path.exists() else None
            write_file_safe(config_path, json.dumps(project_config, indent=2, ensure_ascii=False))
        
        # 創建README
        readme_path = project_dir / "README.md"
        readme_content = f"""# {name}

{description}

## 項目信息
- **Slug**: {slug}
- **創建時間**: {project_config['created']}
- **狀態**: {project_config['status']}

## 文件結構
- `project.json` - 項目配置
- `README.md` - 項目說明
- `decisions.md` - 決策記錄
- `technical.md` - 技術記錄
- `learnings.md` - 學習記錄

## 使用說明
使用 Project Memory Manager 管理此項目。
"""
        write_file_safe(readme_path, readme_content)
        
        # 創建標準文件
        for filename in ["decisions.md", "technical.md", "learnings.md", "summary.md"]:
            filepath = project_dir / filename
            if not filepath.exists():
                write_file_safe(filepath, f"# {filename.replace('.md', '').title()}\n\n")
        
        logger.info(f"創建項目: {name} ({slug})")
        return project_config
    
    @log_performance(threshold_ms=50)
    def get_project(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        獲取項目配置
        
        Args:
            slug: 項目slug
            
        Returns:
            項目配置字典或None
        """
        project_dir = self.projects_dir / slug
        config_path = project_dir / "project.json"
        
        if not config_path.exists():
            logger.warning(f"項目不存在: {slug}")
            return None
        
        try:
            content = read_file_safe(config_path)
            if not content:
                return None
                
            config = json.loads(content)
            
            # 計算文件大小和token數
            config["file_count"] = len(list(project_dir.glob("*.md")))
            config["directory"] = str(project_dir)
            
            return config
            
        except Exception as e:
            logger.error(f"讀取項目配置失敗 {slug}: {e}")
            return None
    
    @log_performance(threshold_ms=100)
    def update_project(self, slug: str, **updates) -> Optional[Dict[str, Any]]:
        """
        更新項目
        
        Args:
            slug: 項目slug
            **updates: 要更新的字段
            
        Returns:
            更新後的項目配置或None
        """
        project_dir = self.projects_dir / slug
        config_path = project_dir / "project.json"
        
        if not config_path.exists():
            logger.warning(f"項目不存在: {slug}")
            return None
        
        try:
            content = read_file_safe(config_path)
            if not content:
                return None
                
            config = json.loads(content)
            
            # 更新字段
            for key, value in updates.items():
                if value is not None:  # 允許設置為None的字段
                    config[key] = value
            
            # 自動更新時間戳
            config["updated"] = datetime.now().isoformat()
            
            # 保存更新
            with Transaction() as txn:
                txn.backup_file(config_path)
                write_file_safe(config_path, json.dumps(config, indent=2, ensure_ascii=False))
            
            logger.info(f"更新項目: {slug}")
            return config
            
        except Exception as e:
            logger.error(f"更新項目失敗 {slug}: {e}")
            return None
    
    @log_performance(threshold_ms=50)
    def delete_project(self, slug: str, backup: bool = True) -> bool:
        """
        刪除項目
        
        Args:
            slug: 項目slug
            backup: 是否創建備份
            
        Returns:
            是否成功
        """
        project_dir = self.projects_dir / slug
        
        if not project_dir.exists():
            logger.warning(f"項目不存在: {slug}")
            return False
        
        try:
            if backup:
                # 創建備份
                import shutil
                backup_dir = self.workspace_dir / "projects_backup" / f"{slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_dir.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(project_dir, backup_dir)
                logger.info(f"創建項目備份: {backup_dir}")
            
            # 刪除項目
            shutil.rmtree(project_dir)
            logger.info(f"刪除項目: {slug}")
            return True
            
        except Exception as e:
            logger.error(f"刪除項目失敗 {slug}: {e}")
            return False
    
    @log_performance(threshold_ms=200)
    def list_projects(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出所有項目
        
        Args:
            status: 過濾狀態（active, archived, 等）
            
        Returns:
            項目配置列表
        """
        projects = []
        
        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
                
            config_path = project_dir / "project.json"
            if not config_path.exists():
                continue
            
            try:
                content = read_file_safe(config_path)
                if not content:
                    continue
                    
                config = json.loads(content)
                config["directory"] = str(project_dir)
                
                # 狀態過濾
                if status and config.get("status") != status:
                    continue
                
                projects.append(config)
                
            except Exception as e:
                logger.warning(f"讀取項目配置失敗 {project_dir.name}: {e}")
                continue
        
        # 按更新時間排序（最近更新在前）
        projects.sort(key=lambda x: x.get("updated", ""), reverse=True)
        
        return projects
    
    def search_projects(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索項目
        
        Args:
            keyword: 搜索關鍵詞
            
        Returns:
            匹配的項目列表
        """
        all_projects = self.list_projects()
        results = []
        
        keyword_lower = keyword.lower()
        
        for project in all_projects:
            # 檢查名稱、描述、關鍵詞
            fields_to_check = [
                project.get("name", ""),
                project.get("description", ""),
                " ".join(project.get("keywords", []))
            ]
            
            content = " ".join(fields_to_check).lower()
            if keyword_lower in content:
                results.append(project)
        
        return results
    
    def export_project(self, slug: str, output_dir: Path) -> bool:
        """
        導出項目
        
        Args:
            slug: 項目slug
            output_dir: 輸出目錄
            
        Returns:
            是否成功
        """
        project_dir = self.projects_dir / slug
        
        if not project_dir.exists():
            logger.warning(f"項目不存在: {slug}")
            return False
        
        try:
            # 創建輸出目錄
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 複製項目文件
            shutil.copytree(project_dir, output_dir / slug, dirs_exist_ok=True)
            
            logger.info(f"導出項目: {slug} -> {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"導出項目失敗 {slug}: {e}")
            return False
    
    def import_project(self, source_dir: Path, overwrite: bool = False) -> Optional[Dict[str, Any]]:
        """
        導入項目
        
        Args:
            source_dir: 源目錄（包含project.json）
            overwrite: 是否覆蓋現有項目
            
        Returns:
            導入的項目配置或None
        """
        try:
            # 檢查配置文件
            config_path = source_dir / "project.json"
            if not config_path.exists():
                logger.warning(f"源目錄不包含project.json: {source_dir}")
                return None
            
            content = read_file_safe(config_path)
            if not content:
                return None
                
            config = json.loads(content)
            slug = config.get("slug")
            
            if not slug:
                logger.warning("項目配置缺少slug字段")
                return None
            
            target_dir = self.projects_dir / slug
            
            # 檢查是否已存在
            if target_dir.exists():
                if not overwrite:
                    logger.warning(f"項目已存在: {slug}")
                    return self.get_project(slug)
                else:
                    # 備份現有項目
                    backup_dir = self.workspace_dir / "projects_backup" / f"{slug}_before_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    backup_dir.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(target_dir, backup_dir)
                    logger.info(f"備份現有項目: {backup_dir}")
            
            # 導入項目
            shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
            
            # 更新時間戳
            config["updated"] = datetime.now().isoformat()
            write_file_safe(target_dir / "project.json", json.dumps(config, indent=2, ensure_ascii=False))
            
            logger.info(f"導入項目: {slug} <- {source_dir}")
            return config
            
        except Exception as e:
            logger.error(f"導入項目失敗 {source_dir}: {e}")
            return None


def get_project_manager(workspace_dir: Optional[Path] = None) -> ProjectManager:
    """
    獲取項目管理器實例（工廠函數）
    """
    return ProjectManager(workspace_dir)


if __name__ == "__main__":
    # 測試項目管理器
    import tempfile
    import os
    
    logging.basicConfig(level=logging.INFO)
    
    # 創建臨時工作空間
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / "workspace"
        workspace.mkdir()
        
        print("=== 測試項目管理器 ===")
        manager = ProjectManager(workspace)
        
        # 創建項目
        project = manager.create_project(
            name="測試項目",
            description="這是一個測試項目",
            keywords=["test", "demo"]
        )
        print(f"創建項目: {project['name']} ({project['slug']})")
        
        # 獲取項目
        retrieved = manager.get_project(project['slug'])
        print(f"獲取項目: {retrieved['name'] if retrieved else '失敗'}")
        
        # 更新項目
        updated = manager.update_project(
            project['slug'],
            description="更新的描述",
            status="archived"
        )
        print(f"更新項目: {updated['description'] if updated else '失敗'}")
        
        # 列出項目
        projects = manager.list_projects()
        print(f"列出項目: {len(projects)} 個項目")
        
        # 搜索項目
        results = manager.search_projects("測試")
        print(f"搜索項目: {len(results)} 個結果")
        
        # 導出項目
        export_dir = workspace / "exports"
        success = manager.export_project(project['slug'], export_dir)
        print(f"導出項目: {'✅' if success else '❌'}")
        
        # 刪除項目
        success = manager.delete_project(project['slug'], backup=True)
        print(f"刪除項目: {'✅' if success else '❌'}")