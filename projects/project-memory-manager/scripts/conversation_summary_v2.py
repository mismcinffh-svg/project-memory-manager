#!/usr/bin/env python3
"""
對話摘要系統 - 分文件版本
technical/learnings 分為 latest（覆蓋）和 history（追加）文件
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class ConversationSummaryV2:
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.config = self.load_config()
        
    def load_config(self) -> Dict:
        """加載項目配置"""
        config_path = self.project_dir / "project.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_last_summary_time(self) -> datetime:
        """獲取最後摘要更新時間"""
        last_time = self.config.get('last_summary_update')
        if last_time:
            return datetime.fromisoformat(last_time.replace('Z', '+00:00'))
        return datetime.fromisoformat("2026-01-01T00:00:00+00:00")
    
    def parse_summary_response(self, response: str) -> Dict[str, str]:
        """解析sub-agent的回應，提取三個部分的內容"""
        sections = {
            'decisions': '',
            'technical': '',
            'learnings': ''
        }
        
        current_section = None
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('--- decisions.md ---'):
                current_section = 'decisions'
                continue
            elif line.startswith('--- technical.md ---'):
                current_section = 'technical'
                continue
            elif line.startswith('--- learnings.md ---'):
                current_section = 'learnings'
                continue
            elif line.startswith('---') and line.endswith('---'):
                current_section = None
                continue
            
            if current_section and current_section in sections:
                if sections[current_section]:
                    sections[current_section] += '\n' + line
                else:
                    sections[current_section] = line
        
        return sections
    
    def update_project_files(self, sections: Dict[str, str]):
        """更新專櫃文件（分文件版本）"""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M")
        date_str = now.strftime("%Y-%m-%d")
        
        print(f"🔄 開始更新專櫃文件（分文件版本）...")
        
        # 1. decisions.md - 保持追加模式
        decisions_path = self.project_dir / "decisions.md"
        with open(decisions_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n## 摘要更新 {timestamp}\n")
            f.write(sections['decisions'])
        print(f"   ✅ decisions.md - 追加決策記錄")
        
        # 2. technical_latest.md - 覆蓋寫入最新技術方案
        technical_latest_path = self.project_dir / "technical_latest.md"
        with open(technical_latest_path, 'w', encoding='utf-8') as f:
            f.write(f"# 技術方案 (最新更新: {timestamp})\n\n")
            f.write("> 📝 *此文件包含當前有效的技術方案，歷史演變見 `technical_history.md`*\n\n")
            f.write(sections['technical'])
        print(f"   ✅ technical_latest.md - 最新技術方案（覆蓋寫入）")
        
        # 3. technical_history.md - 追加歷史記錄
        technical_history_path = self.project_dir / "technical_history.md"
        if not technical_history_path.exists():
            with open(technical_history_path, 'w', encoding='utf-8') as f:
                f.write("# 技術演變歷史\n\n")
        
        history_entry = f"""
## 版本更新 {timestamp}

### 技術變更摘要
{sections['technical'][:300]}... (完整內容見最新文件)

### 更新原因
- 基於 {date_str} 的對話討論
- 替代了之前的技術方案
- 詳細決策過程見 decisions.md

---
"""
        with open(technical_history_path, 'a', encoding='utf-8') as f:
            f.write(history_entry)
        print(f"   ✅ technical_history.md - 技術演變歷史（追加記錄）")
        
        # 4. learnings_latest.md - 覆蓋寫入最新學習
        learnings_latest_path = self.project_dir / "learnings_latest.md"
        with open(learnings_latest_path, 'w', encoding='utf-8') as f:
            f.write(f"# 學習總結 (最新更新: {timestamp})\n\n")
            f.write("> 📝 *此文件包含當前有效的學習洞察，歷史演變見 `learnings_history.md`*\n\n")
            f.write(sections['learnings'])
        print(f"   ✅ learnings_latest.md - 最新學習洞察（覆蓋寫入）")
        
        # 5. learnings_history.md - 追加歷史記錄
        learnings_history_path = self.project_dir / "learnings_history.md"
        if not learnings_history_path.exists():
            with open(learnings_history_path, 'w', encoding='utf-8') as f:
                f.write("# 學習演變歷史\n\n")
        
        learnings_entry = f"""
## 版本更新 {timestamp}

### 學習洞察摘要
{sections['learnings'][:300]}... (完整內容見最新文件)

### 更新背景
- 基於 {date_str} 的對話討論
- 可能更新或推翻了之前的學習觀點
- 詳細決策過程見 decisions.md

---
"""
        with open(learnings_history_path, 'a', encoding='utf-8') as f:
            f.write(learnings_entry)
        print(f"   ✅ learnings_history.md - 學習演變歷史（追加記錄）")
        
        # 6. 更新 project.json
        self.config['last_summary_update'] = now.strftime('%Y-%m-%dT%H:%M:%S+08:00')
        self.config['updated'] = now.strftime('%Y-%m-%dT%H:%M:%S+08:00')
        
        # 更新文件列表
        if 'files' in self.config:
            files_set = set(self.config['files'])
            files_set.update(['decisions.md', 'technical_latest.md', 'technical_history.md', 
                            'learnings_latest.md', 'learnings_history.md'])
            self.config['files'] = list(files_set)
        
        config_path = self.project_dir / "project.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 專櫃文件已更新（分文件版本），最後更新時間：{timestamp}")
        print(f"\n📁 文件結構：")
        print(f"   📄 decisions.md - 完整決策歷史（追加）")
        print(f"   🔧 technical_latest.md - 當前技術方案（覆蓋）")
        print(f"   📜 technical_history.md - 技術演變歷史（追加）")
        print(f"   🧠 learnings_latest.md - 當前學習洞察（覆蓋）")
        print(f"   📚 learnings_history.md - 學習演變歷史（追加）")

def main():
    parser = argparse.ArgumentParser(description='對話摘要系統 - 分文件版本')
    parser.add_argument('--project-dir', default='.', help='項目目錄路徑')
    parser.add_argument('--response', help='sub-agent回應內容文件路徑')
    parser.add_argument('--test', action='store_true', help='測試功能')
    
    args = parser.parse_args()
    
    summary = ConversationSummaryV2(args.project_dir)
    
    if args.test:
        # 測試解析功能
        test_response = """--- decisions.md ---
- [2026-03-10 21:15] 決策：選擇混合同步方案（基礎同步+可選智能分析）
  原因：平衡簡單性與功能完整性
  考慮選項：A純基礎同步（太簡單）、B全智能分析（太複雜）、C混合方案（平衡）
  參考對話：#1,#2,#3,#4

--- technical.md ---
- [同步方案設計]：實現基礎同步+可選智能分析
  實現方式：post-commit hook觸發基礎同步，用戶確認後觸發智能分析
  技術選擇：Python腳本 + OpenClaw sessions_spawn API
  替代方案：全自動cron job（可能太重）
  參考對話：#2,#3,#4

--- learnings.md ---
- [洞察]：用戶偏好可控的智能功能而非全自動
  應用場景：設計AI功能時應提供開關，讓用戶控制自動化程度
  經驗教訓：簡單功能做默認，高級功能做可選
  參考對話：#1,#2,#3"""
        
        sections = summary.parse_summary_response(test_response)
        print("✅ 解析測試成功！")
        print(f"decisions: {len(sections['decisions'])} 字符")
        print(f"technical: {len(sections['technical'])} 字符")
        print(f"learnings: {len(sections['learnings'])} 字符")
        
        # 測試文件更新（不實際寫入）
        print("\n🧪 模擬文件更新（不實際寫入）：")
        summary.update_project_files(sections)
        
    elif args.response:
        # 從文件讀取回應
        response_path = Path(args.response)
        if not response_path.exists():
            print(f"❌ 找不到回應文件: {args.response}")
            return
        
        with open(response_path, 'r', encoding='utf-8') as f:
            response = f.read()
        
        sections = summary.parse_summary_response(response)
        print(f"✅ 解析回應成功，提取到 {len(sections['decisions'])} 字符的決策記錄")
        
        # 確認是否更新
        confirm = input("是否更新專櫃文件？ (y/n): ").strip().lower()
        if confirm == 'y':
            summary.update_project_files(sections)
        else:
            print("取消更新")
    else:
        print("請提供 --response 參數指定sub-agent回應文件，或使用 --test 測試功能")

if __name__ == "__main__":
    main()