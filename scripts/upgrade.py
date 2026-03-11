#!/usr/bin/env python3
"""
Project Memory Manager 升級腳本
從 v3.0/v4.0 升級到 v4.1.0
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ProjectMemoryUpgrader:
    """項目記憶管理器升級器"""
    
    def __init__(self, workspace_dir: str = None):
        if workspace_dir is None:
            # 嘗試自動檢測workspace
            current_dir = Path.cwd()
            # 向上查找包含MEMORY.md的目錄
            for parent in [current_dir] + list(current_dir.parents):
                if (parent / "MEMORY.md").exists():
                    self.workspace_dir = parent
                    break
            else:
                self.workspace_dir = current_dir
        else:
            self.workspace_dir = Path(workspace_dir)
        
        self.skill_dir = self.workspace_dir / "skills" / "project-memory-manager"
        self.projects_dir = self.workspace_dir / "projects"
        
        logger.info(f"Workspace目錄: {self.workspace_dir}")
        logger.info(f"技能目錄: {self.skill_dir}")
        logger.info(f"項目目錄: {self.projects_dir}")
    
    def detect_current_version(self) -> str:
        """檢測當前版本"""
        # 檢查config.json
        config_path = self.skill_dir / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    version = config.get('system', {}).get('version')
                    if version:
                        return version
            except Exception as e:
                logger.warning(f"讀取config.json失敗: {e}")
        
        # 檢查SKILL.md中的版本號
        skill_md_path = self.skill_dir / "SKILL.md"
        if skill_md_path.exists():
            try:
                content = skill_md_path.read_text(encoding='utf-8')
                import re
                # 查找版本號模式
                pattern = r'v(\d+\.\d+\.\d+)'
                matches = re.findall(pattern, content)
                if matches:
                    return matches[0]
            except Exception as e:
                logger.warning(f"讀取SKILL.md失敗: {e}")
        
        return "未知"
    
    def backup_existing_files(self) -> bool:
        """備份現有文件"""
        backup_dir = self.workspace_dir / "backup_project_memory"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"v{self.detect_current_version()}_{timestamp}"
        
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 備份技能目錄
            if self.skill_dir.exists():
                skill_backup = backup_path / "skills"
                shutil.copytree(self.skill_dir, skill_backup / "project-memory-manager")
                logger.info(f"備份技能目錄到: {skill_backup}")
            
            # 備份projects目錄
            if self.projects_dir.exists():
                projects_backup = backup_path / "projects"
                shutil.copytree(self.projects_dir, projects_backup)
                logger.info(f"備份項目目錄到: {projects_backup}")
            
            # 創建備份信息文件
            info = {
                "backup_time": datetime.now().isoformat(),
                "original_version": self.detect_current_version(),
                "backup_location": str(backup_path),
                "workspace": str(self.workspace_dir)
            }
            
            info_path = backup_path / "backup_info.json"
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ 備份完成: {backup_path}")
            logger.info(f"   備份信息: {info_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"備份失敗: {e}")
            return False
    
    def migrate_project_files(self, project_path: Path) -> bool:
        """遷移項目文件到新結構"""
        try:
            logger.info(f"遷移項目: {project_path.name}")
            
            # 檢查是否有舊版文件
            old_technical = project_path / "technical.md"
            old_learnings = project_path / "learnings.md"
            
            # 創建新文件（如果不存在）
            new_files = [
                "learnings_latest.md",
                "learnings_history.md", 
                "technical_latest.md",
                "technical_history.md"
            ]
            
            for filename in new_files:
                filepath = project_path / filename
                if not filepath.exists():
                    if filename.endswith("_latest.md"):
                        base = filename.replace("_latest.md", "")
                        content = f"# {base.capitalize()} - 最新摘要\n\n"
                        content += f"項目: {project_path.name}\n"
                        content += f"遷移時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                        content += "## 最新更新\n\n"
                        content += "*[從舊版文件遷移而來]*\n"
                    elif filename.endswith("_history.md"):
                        base = filename.replace("_history.md", "")
                        content = f"# {base.capitalize()} - 歷史記錄\n\n"
                        content += f"項目: {project_path.name}\n"
                        content += f"遷移時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                        content += "## 歷史記錄\n\n"
                        content += "*[從舊版文件遷移而來]*\n"
                    else:
                        content = f"# {filename.replace('.md', '')}\n\n"
                    
                    filepath.write_text(content, encoding='utf-8')
                    logger.debug(f"創建新文件: {filename}")
            
            # 遷移舊版technical.md內容
            if old_technical.exists():
                content = old_technical.read_text(encoding='utf-8')
                # 將內容添加到technical_latest.md
                latest_path = project_path / "technical_latest.md"
                if latest_path.exists():
                    existing = latest_path.read_text(encoding='utf-8')
                    # 在文件末尾添加舊內容
                    migration_note = f"\n\n## 遷移內容（從舊版technical.md）\n\n{content}"
                    latest_path.write_text(existing + migration_note, encoding='utf-8')
                    logger.info(f"遷移technical.md內容到technical_latest.md")
                
                # 也添加到technical_history.md
                history_path = project_path / "technical_history.md"
                if history_path.exists():
                    existing = history_path.read_text(encoding='utf-8')
                    history_entry = f"\n\n## 遷移記錄 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                    history_entry += f"從舊版technical.md遷移內容\n\n"
                    history_entry += f"{content[:500]}..." if len(content) > 500 else content
                    history_path.write_text(existing + history_entry, encoding='utf-8')
            
            # 遷移舊版learnings.md內容
            if old_learnings.exists():
                content = old_learnings.read_text(encoding='utf-8')
                # 將內容添加到learnings_latest.md
                latest_path = project_path / "learnings_latest.md"
                if latest_path.exists():
                    existing = latest_path.read_text(encoding='utf-8')
                    migration_note = f"\n\n## 遷移內容（從舊版learnings.md）\n\n{content}"
                    latest_path.write_text(existing + migration_note, encoding='utf-8')
                    logger.info(f"遷移learnings.md內容到learnings_latest.md")
                
                # 也添加到learnings_history.md
                history_path = project_path / "learnings_history.md"
                if history_path.exists():
                    existing = history_path.read_text(encoding='utf-8')
                    history_entry = f"\n\n## 遷移記錄 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                    history_entry += f"從舊版learnings.md遷移內容\n\n"
                    history_entry += f"{content[:500]}..." if len(content) > 500 else content
                    history_path.write_text(existing + history_entry, encoding='utf-8')
            
            # 更新project.json中的文件列表
            config_path = project_path / "project.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 更新文件列表
                old_files = config.get('files', [])
                new_files_list = []
                for file in old_files:
                    if file == "technical.md":
                        new_files_list.extend(["technical_latest.md", "technical_history.md"])
                    elif file == "learnings.md":
                        new_files_list.extend(["learnings_latest.md", "learnings_history.md"])
                    else:
                        new_files_list.append(file)
                
                # 移除重複
                config['files'] = list(dict.fromkeys(new_files_list))
                config['updated'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')
                config['migrated_to_v4.1.0'] = True
                config['migration_time'] = datetime.now().isoformat()
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                logger.info(f"更新project.json文件列表")
            
            logger.info(f"✅ 項目遷移完成: {project_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"項目遷移失敗 {project_path.name}: {e}")
            return False
    
    def migrate_all_projects(self) -> bool:
        """遷移所有項目"""
        if not self.projects_dir.exists():
            logger.warning("projects目錄不存在，無需遷移")
            return True
        
        success = True
        migrated_count = 0
        
        for item in self.projects_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                config_path = item / "project.json"
                if config_path.exists():
                    if self.migrate_project_files(item):
                        migrated_count += 1
                    else:
                        success = False
                        logger.error(f"項目遷移失敗: {item.name}")
        
        logger.info(f"✅ 遷移完成: {migrated_count} 個項目")
        return success
    
    def update_skill_files(self, source_dir: Path) -> bool:
        """更新技能文件"""
        try:
            # 確保目標目錄存在
            self.skill_dir.mkdir(parents=True, exist_ok=True)
            
            # 複製所有文件
            for item in source_dir.rglob("*"):
                if item.is_file():
                    # 計算相對路徑
                    rel_path = item.relative_to(source_dir)
                    target_path = self.skill_dir / rel_path
                    
                    # 確保目錄存在
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 複製文件
                    shutil.copy2(item, target_path)
                    logger.debug(f"複製文件: {rel_path}")
            
            logger.info(f"✅ 技能文件更新完成: {self.skill_dir}")
            return True
            
        except Exception as e:
            logger.error(f"更新技能文件失敗: {e}")
            return False
    
    def update_configuration(self) -> bool:
        """更新配置"""
        try:
            config_path = self.skill_dir / "config.json"
            if not config_path.exists():
                logger.warning("config.json不存在，將創建新配置")
                return True
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新系統信息
            if 'system' in config:
                config['system']['version'] = "4.1.0"
                config['system']['updated'] = datetime.now().strftime('%Y-%m-%d')
                config['system']['description'] = "通用項目記憶管理系統 - 帶對話摘要與版本管理"
            
            # 更新項目文件配置
            if 'projects' in config:
                projects_config = config['projects']
                # 確保包含新文件
                if 'required_files' in projects_config:
                    # 確保包含decisions.md
                    if 'decisions.md' not in projects_config['required_files']:
                        projects_config['required_files'].append('decisions.md')
                
                if 'optional_files' in projects_config:
                    # 移除舊文件，添加新文件
                    old_files = ['technical.md', 'learnings.md']
                    new_files = ['learnings_latest.md', 'learnings_history.md', 
                                'technical_latest.md', 'technical_history.md']
                    
                    for old in old_files:
                        if old in projects_config['optional_files']:
                            projects_config['optional_files'].remove(old)
                    
                    for new in new_files:
                        if new not in projects_config['optional_files']:
                            projects_config['optional_files'].append(new)
            
            # 添加升級記錄
            if 'upgrade_history' not in config:
                config['upgrade_history'] = []
            
            upgrade_record = {
                'from_version': self.detect_current_version(),
                'to_version': "4.1.0",
                'time': datetime.now().isoformat(),
                'migrated_projects': True
            }
            config['upgrade_history'].append(upgrade_record)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info("✅ 配置更新完成")
            return True
            
        except Exception as e:
            logger.error(f"配置更新失敗: {e}")
            return False
    
    def run_upgrade(self, source_dir: Path = None) -> bool:
        """運行完整升級流程"""
        print("=" * 60)
        print("Project Memory Manager 升級工具")
        print(f"從 v{self.detect_current_version()} 升級到 v4.1.0")
        print("=" * 60)
        
        # 1. 顯示當前狀態
        print(f"\n📊 當前狀態:")
        print(f"   Workspace: {self.workspace_dir}")
        print(f"   當前版本: v{self.detect_current_version()}")
        print(f"   項目數量: {len(list(self.projects_dir.glob('*/project.json'))) if self.projects_dir.exists() else 0}")
        
        # 2. 確認升級
        print("\n⚠️  升級將執行以下操作:")
        print("   1. 備份現有文件（安全第一）")
        print("   2. 更新技能文件到 v4.1.0")
        print("   3. 遷移項目文件到新結構 (_latest + _history)")
        print("   4. 更新配置")
        print("   5. 保留所有現有數據")
        
        try:
            response = input("\n是否繼續升級？ (y/N): ").strip().lower()
            if response not in ['y', 'yes', '是']:
                print("升級取消")
                return False
        except:
            # 非交互模式，自動繼續
            print("非交互模式，自動繼續升級")
        
        # 3. 備份
        print("\n🔄 步驟1: 備份現有文件...")
        if not self.backup_existing_files():
            print("❌ 備份失敗，升級中止")
            return False
        
        # 4. 更新技能文件（如果提供了源目錄）
        if source_dir and source_dir.exists():
            print(f"\n🔄 步驟2: 更新技能文件從 {source_dir}...")
            if not self.update_skill_files(source_dir):
                print("❌ 技能文件更新失敗")
                return False
        else:
            print("\n⏭️  步驟2: 跳過技能文件更新（未提供源目錄）")
        
        # 5. 遷移項目
        print("\n🔄 步驟3: 遷移項目文件到新結構...")
        if not self.migrate_all_projects():
            print("⚠️  部分項目遷移失敗，繼續升級")
        
        # 6. 更新配置
        print("\n🔄 步驟4: 更新配置...")
        if not self.update_configuration():
            print("❌ 配置更新失敗")
            return False
        
        # 7. 完成
        print("\n" + "=" * 60)
        print("✅ 升級完成！")
        print("=" * 60)
        print(f"\n📋 升級摘要:")
        print(f"   • 從 v{self.detect_current_version()} 升級到 v4.1.0")
        print(f"   • 備份位置: {self.workspace_dir / 'backup_project_memory'}")
        print(f"   • 新功能已啟用:")
        print(f"     - 對話摘要系統（檢測「更新版本」等關鍵詞）")
        print(f"     - 版本自動管理（CHANGELOG更新、Git操作）")
        print(f"     - _latest + _history 文件分離結構")
        print(f"\n🚀 下一步:")
        print(f"   1. 測試新功能: python3 {self.skill_dir / 'scripts' / 'project_update_integration.py'} --demo")
        print(f"   2. 查看文檔: cat {self.skill_dir / 'SKILL.md'} | head -50")
        print(f"   3. 創建測試項目: python3 {self.skill_dir / 'scripts' / 'create.py'} manual \"測試項目\"")
        
        return True

def main():
    """命令行入口點"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Project Memory Manager 升級工具')
    parser.add_argument('--workspace', help='OpenClaw workspace目錄')
    parser.add_argument('--source-dir', help='v4.1.0源代碼目錄')
    parser.add_argument('--yes', action='store_true', help='自動確認，不詢問')
    parser.add_argument('--backup-only', action='store_true', help='只備份不升級')
    
    args = parser.parse_args()
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    upgrader = ProjectMemoryUpgrader(args.workspace)
    
    if args.backup_only:
        print("執行備份...")
        upgrader.backup_existing_files()
        print("備份完成")
        return
    
    # 如果提供了源目錄，轉換為Path
    source_dir = Path(args.source_dir) if args.source_dir else None
    
    success = upgrader.run_upgrade(source_dir)
    
    if not success:
        print("❌ 升級失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()