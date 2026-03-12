#!/usr/bin/env python3
"""
基礎同步腳本：從GitHub同步信息到專櫃
只更新基礎信息，不處理決策摘要
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

# 配置
GITHUB_REPO = "mismcinffh-svg/project-memory-manager"
GITHUB_BRANCH = "main"
PROJECT_DIR = Path(__file__).parent

def fetch_github_file(filename: str) -> str:
    """從GitHub獲取文件內容"""
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{filename}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ 無法獲取 {filename}: {e}")
        return ""

def update_readme():
    """更新README.md，反映最新版本信息"""
    readme_path = PROJECT_DIR / "README.md"
    
    # 讀取當前README
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 從GitHub獲取CHANGELOG提取版本信息
    changelog = fetch_github_file("CHANGELOG.md")
    
    # 提取v4.0.0信息
    v4_info = ""
    if "## [4.0.0]" in changelog:
        start = changelog.find("## [4.0.0]")
        end = changelog.find("## [3.0.0]", start)
        if end == -1:
            end = len(changelog)
        v4_info = changelog[start:end].strip()
    
    # 更新版本號（簡單替換）
    content = content.replace("**版本**: v3.0.0", "**版本**: v4.0.0")
    
    # 更新項目狀態部分
    if "## 項目狀態" in content:
        # 重寫項目狀態部分
        status_section = f"""## 項目狀態

**當前狀態**: active  
**版本**: v4.0.0  
**完成度**: 100%  
**最後更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**GitHub倉庫**: https://github.com/{GITHUB_REPO}

### v4.0.0 主要改進
從 **v3.0.0** → **v4.0.0** 的主要提升：

1. **交互式設置嚮導**：方向鍵選擇（↑↓←→）、簡單顏色、進度條百分比
2. **智能環境檢測**：自動識別 Git、GitHub CLI、Telegram Bot 配置
3. **雙模式界面**：curses 圖形界面 + 文本模式回退，100% 兼容
4. **配置持久化**：JSON 格式保存到 `~/.openclaw/project-memory-config.json`
5. **Git 自動化增強**：post-commit 鉤子實現零配置自動推送
6. **安全遷移策略**：單項目遷移 + 24小時觀察期避免GitHub風控

### 專業體驗提升
- **模仿 openclaw config**：相同交互邏輯和視覺風格
- **快速設置流程**：5步完成所有配置
- **進度可視化**：實時百分比進度條
- **零技術門檻**：新手只需按箭頭和回車鍵"""
        
        # 替換舊的項目狀態部分
        old_start = content.find("## 項目狀態")
        old_end = content.find("## 效益評估", old_start)
        if old_end == -1:
            old_end = content.find("---", old_start)
        if old_end == -1:
            old_end = len(content)
        
        content = content[:old_start] + status_section + content[old_end:]
    
    # 更新下一步行動
    if "## 下一步行動" in content:
        next_actions = f"""## 下一步行動

1. **推廣測試**：讓其他Agent安裝驗證v4.0.0
2. **收集反饋**：根據實際使用優化交互體驗
3. **智能摘要系統**：實現commit時自動更新專櫃摘要（開發中）
4. **持續維護**：定期更新，添加新功能

---
**項目創建時間**: 2026-03-07 22:30  
**最後同步時間**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**記錄者**: Nana  
**工作空間**: ~/.openclaw/workspace-secretary/"""
        
        old_start = content.find("## 下一步行動")
        old_end = content.find("---", old_start)
        if old_end == -1:
            old_end = len(content)
        
        content = content[:old_start] + next_actions + content[old_end:]
    
    # 寫回文件
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ README.md 已更新到 v4.0.0")

def update_project_json():
    """更新project.json的last_summary_update時間"""
    json_path = PROJECT_DIR / "project.json"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 更新時間戳
    now_iso = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')
    data['last_summary_update'] = now_iso
    data['updated'] = now_iso
    data['description'] = "項目記憶管理系統重構與問題解決 v4.0.0"
    
    # 添加GitHub URL（如果沒有）
    if 'github_url' not in data:
        data['github_url'] = f"https://github.com/{GITHUB_REPO}"
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ project.json 已更新，last_summary_update: {now_iso}")

def main():
    print(f"🔄 開始同步專櫃內容: {GITHUB_REPO}")
    print(f"📁 專櫃目錄: {PROJECT_DIR}")
    
    # 更新README
    update_readme()
    
    # 更新project.json
    update_project_json()
    
    print("🎉 基礎同步完成！")
    print("\n📝 注意：此同步僅更新基礎信息（版本號、狀態等）")
    print("   決策摘要需要通過「對話摘要系統」更新")

if __name__ == "__main__":
    main()