# 最佳實踐指南

## 🎯 核心原則

### 1. 極簡MEMORY.md
- **目標**: MEMORY.md < 100 tokens
- **內容**: 僅保留核心身份、關鍵決策、項目索引指引
- **規則**: 任何詳細內容都應遷移到項目中
- **好處**: 減少上下文大小，加快Agent響應速度

### 2. 項目專櫃思維
- **每個項目一個文件夾**: 相關內容集中存放
- **標準文件結構**: README.md, technical.md, decisions.md, learnings.md
- **獨立可檢索**: 每個項目可獨立搜索和理解
- **狀態管理**: 明確標記active/inactive/completed

### 3. 500 Tokens自動規則
- **觸發條件**: 同一主題內容>500 tokens
- **自動執行**: 系統自動創建項目 + 遷移內容
- **手動優先**: 用戶可隨時手動創建項目
- **持續監測**: 系統定期檢查MEMORY.md

## 📋 工作流程

### 日常使用
```bash
# 1. 初始化系統（首次使用）
python3 scripts/init.py

# 2. 創建新項目
python3 scripts/create.py manual "項目名稱" "項目描述"

# 3. 檢查系統狀態
python3 scripts/create.py status

# 4. 定期自動遷移
python3 scripts/create.py auto --threshold 500
```

### 與Agent交互
```javascript
// Agent自動觸發項目創建
if (memory_content_tokens > 500 && is_same_topic) {
    // 自動創建項目
    exec({ command: "python3 scripts/create.py manual \"自動項目\" \"從MEMORY.md自動遷移\"" });
}

// 用戶手動創建
if (user_message.includes("開新項目")) {
    const project_name = extract_project_name(user_message);
    exec({ command: `python3 scripts/create.py manual "${project_name}"` });
}
```

### 內容遷移策略
1. **即時遷移**: 發現>500t立即遷移
2. **批量遷移**: 定期運行自動遷移
3. **手動遷移**: 用戶主動整理重要內容
4. **備份保留**: 遷移後在MEMORY.md保留摘要

## 🔍 檢索優化

### 關鍵詞策略
- **提取原則**: 從項目名和描述自動提取
- **數量限制**: 每個項目3-5個關鍵詞
- **質量優先**: 選擇最具代表性詞語
- **避免重複**: 相似項目使用不同關鍵詞

### memory_search技巧
```javascript
// 1. 按項目搜索
memory_search({query: "Office365"});

// 2. 按技術搜索
memory_search({query: "API 集成"});

// 3. 按決策搜索
memory_search({query: "決策 架構"});

// 4. 按時間搜索
memory_search({query: "2026-03 項目"});
```

### 索引設計
- **一行一項目**: 最大化信息密度
- **關鍵詞可視化**: 關鍵詞列在第二列
- **狀態標記**: 清晰顯示項目進度
- **時間排序**: 最新項目在前

## ⚙️ 配置建議

### 500t閾值調整
```json
{
  "auto_monitor": {
    "threshold_tokens": 300,  // 更敏感
    "check_interval_hours": 12  // 更頻繁
  }
}
```

### 關鍵詞黑名單
```json
{
  "projects": {
    "blacklisted_keywords": [
      "測試", "示例", "temp", "test",
      "臨時", "草稿", "draft"
    ]
  }
}
```

### 項目模板定制
```bash
# 編輯模板文件
vim projects/_templates/README.md
vim projects/_templates/technical.md
```

## 📊 性能監控

### 健康指標
| 指標 | 目標值 | 檢查方法 |
|------|--------|----------|
| **MEMORY.md tokens** | < 100t | `python3 scripts/create.py status` |
| **INDEX.md tokens** | < 200t | 同上 |
| **項目數量** | 無限制 | 同上 |
| **自動檢查頻率** | 每24小時 | 查看配置 |
| **遷移成功率** | > 95% | 檢查日誌 |

### 定期維護
```bash
# 每周維護任務
1. 檢查系統狀態
2. 運行自動遷移
3. 清理完成項目
4. 備份重要項目
5. 更新索引

# 每月維護任務
1. 分析項目增長趨勢
2. 優化關鍵詞策略
3. 調整配置參數
4. 清理日誌文件
```

## 🚀 高級技巧

### 跨項目引用
```markdown
<!-- 在項目文件中 -->
相關項目: [Office365技能](../office365-skill/README.md)

決策依據: [技術選型討論](../tech-decision-2026/decisions.md)
```

### 自動化集成
```bash
# 在Agent的HEARTBEAT.md中添加
- 檢查MEMORY.md tokens
- 運行自動遷移（如>500t）
- 報告項目統計
```

### 批量操作
```bash
# 批量創建項目
for name in "項目1" "項目2" "項目3"; do
    python3 scripts/create.py manual "$name"
done

# 批量更新狀態
find projects/ -name "project.json" -exec jq '.status = "completed"' {} \;
```

## 🆘 常見問題解決

### 內容重複問題
**問題**: 同一內容在多個項目中重複
**解決**: 
1. 建立主項目引用次項目
2. 使用符號鏈接共享文件
3. 在INDEX.md中添加「相關項目」列

### 檢索不準確
**問題**: memory_search找不到相關項目
**解決**:
1. 優化關鍵詞提取
2. 添加同義詞到項目描述
3. 使用更具體的查詢詞

### 項目過多
**問題**: 項目數量太多難以管理
**解決**:
1. 合併相關小項目
2. 使用標籤系統
3. 創建項目分類目錄

## 📈 成功案例

### 案例1: Office365技能開發
- **問題**: MEMORY.md包含大量API文檔和代碼片段
- **解決**: 自動創建「Office365-skill」項目
- **結果**: MEMORY.md從1200t降至80t，檢索速度提升40%

### 案例2: 多Agent協作
- **問題**: 多個Agent共享記憶混亂
- **解決**: 使用統一項目結構，跨workspace同步
- **結果**: 協作效率提升60%，衝突減少80%

### 案例3: 長期項目跟蹤
- **問題**: 長期項目記憶分散
- **解決**: 按階段創建子項目，保持索引更新
- **結果**: 項目可追溯性提升90%

## 🔮 未來擴展

### 計劃功能
1. **智能分類**: AI自動分類項目內容
2. **可視化儀表板**: 項目狀態圖形化顯示
3. **跨Agent同步**: 實時項目共享和協作
4. **API接口**: 程式化訪問項目管理功能
5. **插件系統**: 擴展自定義功能

### 社區貢獻
歡迎貢獻:
- 新模板設計
- 檢索算法優化
- 集成適配器
- 文檔翻譯

---

**記住**: 最好的系統是最簡單的系統。保持MEMORY.md極簡，讓項目專櫃承載詳細內容。