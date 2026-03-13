#!/usr/bin/env python3
"""
對話摘要系統 - 概念驗證
假設從外部獲取對話歷史，生成專櫃摘要
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class ConversationSummary:
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
            # 解析ISO格式時間
            return datetime.fromisoformat(last_time.replace('Z', '+00:00'))
        # 如果沒有記錄，返回很舊的時間
        return datetime.fromisoformat("2026-01-01T00:00:00+00:00")
    
    def build_summary_prompt(self, project_name: str, conversations: List[Dict], 
                           since_time: datetime) -> str:
        """構建摘要生成的prompt"""
        
        # 格式化對話歷史
        conv_text = ""
        for i, conv in enumerate(conversations, 1):
            role = conv.get('role', 'unknown')
            content = self.extract_text_content(conv.get('content', ''))
            timestamp = conv.get('timestamp', '')
            
            # 簡單格式化時間
            time_str = ""
            if timestamp:
                try:
                    ts = int(timestamp) / 1000  # 毫秒轉秒
                    dt = datetime.fromtimestamp(ts)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    time_str = ""
            
            conv_text += f"{i}. [{role}] {time_str}\n"
            conv_text += f"   {content[:200]}{'...' if len(content) > 200 else ''}\n\n"
        
        prompt = f"""請根據以下對話，為項目「{project_name}」生成專櫃摘要。

## 項目信息
- 項目名稱：{project_name}
- 最後摘要更新：{since_time.strftime('%Y-%m-%d %H:%M')}
- 對話條數：{len(conversations)}

## 對話歷史
{conv_text}

## 摘要要求
請生成三個部分的內容：

### 1. decisions.md 更新（決策記錄）
格式：
```
- [YYYY-MM-DD HH:MM] 決策：[具體決策內容]
  原因：[為什麼做出這個決策]
  考慮選項：[考慮了哪些選項，為什麼選擇這個]
  參考對話：[相關對話編號，如#1,#3]
```

要求：
- 只記錄重要決策，不是所有討論
- 包含決策原因和考慮過程
- 引用相關對話編號

### 2. technical.md 更新（技術要點）
格式：
```
- [技術模塊/功能]：[技術實現要點]
  實現方式：[具體實現方法]
  技術選擇：[為什麼選擇這個技術方案]
  替代方案：[考慮過的其他方案]
  參考對話：[相關對話編號]
```

要求：
- 記錄技術實現的關鍵選擇
- 包含技術方案的比較

### 3. learnings.md 更新（學習總結）
格式：
```
- [洞察/學習]：[學到了什麼]
  應用場景：[這個學習可以應用到什麼場景]
  經驗教訓：[從中得到的經驗教訓]
  參考對話：[相關對話編號]
```

要求：
- 提煉有價值的學習點
- 思考如何應用到未來項目

## 輸出格式
請直接輸出三個部分的內容，用分隔線分開：
```
--- decisions.md ---
[這裡是decisions.md內容]

--- technical.md ---
[這裡是technical.md內容]

--- learnings.md ---
[這裡是learnings.md內容]
```

注意：內容要簡潔、有價值，便於未來查閱。"""
        
        return prompt
    
    def extract_text_content(self, content) -> str:
        """從OpenClaw消息內容中提取文本"""
        if isinstance(content, str):
            return content
        
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                    elif 'text' in item:
                        text_parts.append(item['text'])
                elif isinstance(item, str):
                    text_parts.append(item)
            return ' '.join(text_parts)
        
        return str(content)
    
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
            
            # 檢測分節標題
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
                # 其他分節，忽略
                current_section = None
                continue
            
            # 添加到當前分節
            if current_section and current_section in sections:
                if sections[current_section]:
                    sections[current_section] += '\n' + line
                else:
                    sections[current_section] = line
        
        return sections
    
    def update_project_files(self, sections: Dict[str, str]):
        """更新專櫃文件 (_latest + _history 分離結構)"""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M")
        iso_timestamp = now.strftime('%Y-%m-%dT%H:%M:%S+08:00')
        
        # 1. 更新 decisions.md（追加完整歷史）
        decisions_path = self.project_dir / "decisions.md"
        with open(decisions_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n## 摘要更新 {timestamp}\n")
            f.write(sections['decisions'])
        
        # 2. 更新 learnings_latest.md（替換為最新摘要）
        learnings_latest_path = self.project_dir / "learnings_latest.md"
        latest_learnings_content = f"""# Learnings - 最新摘要

## 項目
{self.config.get('name', '未知項目')}

## 更新時間
{timestamp}

## 最新更新
*[此文件由對話摘要系統自動更新於 {timestamp}]*

{sections['learnings']}

---
*最後更新: {timestamp}*
"""
        learnings_latest_path.write_text(latest_learnings_content, encoding='utf-8')
        
        # 3. 更新 learnings_history.md（追加歷史記錄）
        learnings_history_path = self.project_dir / "learnings_history.md"
        history_entry = f"""

## 更新記錄 {timestamp}

{sections['learnings']}

---
"""
        with open(learnings_history_path, 'a', encoding='utf-8') as f:
            f.write(history_entry)
        
        # 4. 更新 technical_latest.md（替換為最新摘要）
        technical_latest_path = self.project_dir / "technical_latest.md"
        latest_technical_content = f"""# Technical - 最新摘要

## 項目
{self.config.get('name', '未知項目')}

## 更新時間
{timestamp}

## 最新更新
*[此文件由對話摘要系統自動更新於 {timestamp}]*

{sections['technical']}

---
*最後更新: {timestamp}*
"""
        technical_latest_path.write_text(latest_technical_content, encoding='utf-8')
        
        # 5. 更新 technical_history.md（追加歷史記錄）
        technical_history_path = self.project_dir / "technical_history.md"
        history_entry = f"""

## 更新記錄 {timestamp}

{sections['technical']}

---
"""
        with open(technical_history_path, 'a', encoding='utf-8') as f:
            f.write(history_entry)
        
        # 6. 更新 project.json
        self.config['last_summary_update'] = iso_timestamp
        self.config['updated'] = iso_timestamp
        
        config_path = self.project_dir / "project.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 專櫃文件已更新（分離結構），最後更新時間：{timestamp}")
        print(f"   📝 decisions.md: 追加決策記錄")
        print(f"   📚 learnings_latest.md: 更新最新摘要")
        print(f"   📚 learnings_history.md: 追加歷史記錄")
        print(f"   🔧 technical_latest.md: 更新最新摘要")
        print(f"   🔧 technical_history.md: 追加歷史記錄")
    
    def generate_sample_prompt(self):
        """生成示例prompt（用於測試）"""
        sample_conversations = [
            {
                'role': 'user',
                'content': '我覺得專櫃應該同GitHub同步，但唔知點設計好',
                'timestamp': '1773147757393'
            },
            {
                'role': 'assistant', 
                'content': '我地可以考慮三個方案：A基礎同步、B智能分析、C混合模式',
                'timestamp': '1773147757394'
            },
            {
                'role': 'user',
                'content': '方案B好似太複雜，方案A又太簡單，有冇中間方案？',
                'timestamp': '1773147867087'
            },
            {
                'role': 'assistant',
                'content': '可以考慮方案C：基礎同步+可選智能分析，平衡簡單同功能',
                'timestamp': '1773147867088'
            }
        ]
        
        project_name = self.config.get('name', '未知項目')
        since_time = self.get_last_summary_time()
        
        prompt = self.build_summary_prompt(project_name, sample_conversations, since_time)
        return prompt

def main():
    parser = argparse.ArgumentParser(description='對話摘要系統')
    parser.add_argument('--project-dir', default='.', help='項目目錄路徑')
    parser.add_argument('--generate-prompt', action='store_true', help='生成示例prompt')
    parser.add_argument('--test-parse', action='store_true', help='測試解析功能')
    
    args = parser.parse_args()
    
    summary = ConversationSummary(args.project_dir)
    
    if args.generate_prompt:
        prompt = summary.generate_sample_prompt()
        print("=== 示例Prompt ===")
        print(prompt)
        print("\n=== Prompt結束 ===")
        
        # 保存到文件
        prompt_path = Path(args.project_dir) / "sample_prompt.txt"
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt)
        print(f"✅ Prompt已保存到: {prompt_path}")
    
    elif args.test_parse:
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
        
        # 顯示解析結果
        for section_name, content in sections.items():
            print(f"\n--- {section_name}.md ---")
            print(content[:200] + "..." if len(content) > 200 else content)
    
    else:
        print("使用方法：")
        print("  --generate-prompt   生成示例prompt")
        print("  --test-parse        測試解析功能")
        print("\n示例：")
        print("  python conversation_summary.py --generate-prompt")
        print("  python conversation_summary.py --test-parse")

if __name__ == "__main__":
    main()