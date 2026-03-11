# Project Memory Manager v4.1.0 - Agent 集成指南

## 🎯 兩個核心觸發場景

### 場景1：口語化歸檔
```
用戶：「將剛才傾嘅內容歸檔」
Agent：「好的，而家準備更新項目專櫃內嘅內容，請問是否確認？」
用戶：「要」/「唔要」
→ 執行/停止
```

**觸發關鍵詞**：歸檔、記錄落去、記錄返、update落去、更新落去、整理落去、整理記錄、放入專櫃、存檔、保存記錄、寫入專櫃、更新專櫃、內容歸檔、對話歸檔、傾過嘅歸檔、更新項目

### 場景2：GitHub同步必做
```
每次 git commit/push 上GitHub
→ 自動 session_spawn 分身更新專櫃
→ 無需詢問（寫死）
```

**觸發關鍵詞**：commit、上github、git push、push、同步上github、同步到github、上傳github、更新倉庫、同步倉庫、上傳代碼、提交代碼

## 🔧 Agent 集成方法

### 方法A：修改 HEARTBEAT.md（最簡單）
在 HEARTBEAT.md 中添加以下邏輯：

```markdown
## 項目記憶觸發器
1. 收到消息時，運行：
   ```bash
   python3 skills/project-memory-manager/scripts/trigger_detector.py "{{消息內容}}" --workspace .
   ```
2. 如果返回 `"triggered": true`：
   - 場景 "archive"：發送確認消息，等待用戶回應
   - 場景 "github_sync"：自動執行，無需確認
3. 根據場景執行相應操作
```

### 方法B：創建專用 Agent Hook（推薦）
在 Agent 的 SOUL.md 或 AGENTS.md 中添加：

```python
# 偽代碼示例
def handle_message(message):
    # 檢測觸發
    result = trigger_detector.process_message(message)
    
    if result["triggered"]:
        if result["scenario"] == "archive":
            # 發送確認消息
            send_message(result["confirmation_message"])
            # 等待用戶回應
            wait_for_confirmation()
            
            if user_confirmed:
                # 執行歸檔
                trigger_detector.execute_archive_scenario(
                    result["project_name"], 
                    user_confirmed=True
                )
                
        elif result["scenario"] == "github_sync":
            # 自動執行，無需確認
            trigger_detector.execute_github_sync_scenario(
                result["project_name"]
            )
```

### 方法C：使用 session_spawn 分身（進階）
對於 GitHub 同步場景，使用 JSON 格式與分身溝通：

```python
# 使用 OpenClaw 的 sessions_spawn 工具
sessions_spawn({
    "runtime": "subagent",
    "task": f"更新項目專櫃內容 - {project_name}",
    "prompt": f"""
    請為項目「{project_name}」更新專櫃內容。
    
    任務：
    1. 使用 conversation_summary.py 生成最新摘要
    2. 更新 _latest 和 _history 文件
    3. 執行版本遞增和 CHANGELOG 更新
    
    要求：
    - 僅返回最終結果，省略內部推演
    - 使用 JSON 格式回應
    """,
    "model": "deepseek-chat"  # 成本控制
})
```

## 🚀 快速測試

### 測試觸發檢測
```bash
cd ~/.openclaw/workspace-secretary
python3 skills/project-memory-manager/scripts/trigger_detector.py "將剛才傾嘅內容歸檔" --workspace .
```

### 測試完整執行
```bash
# 場景1：歸檔（需要確認）
python3 skills/project-memory-manager/scripts/trigger_detector.py "歸檔 project-memory-manager" --workspace . --execute

# 場景2：GitHub同步（自動執行）
python3 skills/project-memory-manager/scripts/trigger_detector.py "commit project-memory-manager上GitHub" --workspace . --execute
```

### 測試項目更新集成
```bash
# 手動觸發完整工作流程
python3 skills/project-memory-manager/scripts/project_update_integration.py --project project-memory-manager --update-summary --yes

# 後台執行
python3 skills/project-memory-manager/scripts/project_update_integration.py --project project-memory-manager --update-summary --background
```

## ⚙️ 配置文件

### 觸發關鍵詞自定義
編輯 `scripts/trigger_detector.py`：
```python
# 場景1：口語化歸檔關鍵詞
self.archive_keywords = [
    "歸檔", "記錄落去", "記錄返", "update落去",
    "更新落去", "整理落去", "整理記錄", "放入專櫃",
    # 添加自定義關鍵詞...
]

# 場景2：GitHub同步關鍵詞
self.github_sync_keywords = [
    "commit", "上github", "git push", "push",
    "同步上github", "同步到github", "上傳github",
    # 添加自定義關鍵詞...
]
```

### 項目名稱提取改進
如果項目名稱提取不準確，修改 `extract_project_name` 方法中的正則表達式：
```python
# 當前正則
self.project_pattern = r'(?:項目|project)[:：\s]*([^\s。，,.!！?？]+)'

# 可改進為：
self.project_pattern = r'(?:項目|project)[:：\s]*([a-zA-Z0-9_-]+)'
```

## 📊 執行流程圖

```
用戶消息
    ↓
觸發檢測
    ├── 場景1: 口語化歸檔 → 確認 → 執行專櫃更新
    └── 場景2: GitHub同步 → 自動執行專櫃更新
    ↓
專櫃更新
    ├── 獲取對話歷史 (sessions_history)
    ├── 生成摘要 (session_spawn 分身)
    ├── 更新 _latest/_history 文件
    └── 版本管理 (遞增版本、更新CHANGELOG、Git操作)
    ↓
GitHub同步
    ├── git add/commit
    ├── 創建 tag
    └── git push
```

## 🔧 故障排除

### 常見問題
1. **項目名稱無法識別**
   - 明確指定：「歸檔 project-memory-manager」
   - 或使用最近項目自動識別

2. **權限問題**
   - 確保 Agent 有權限執行 Python 腳本
   - 檢查 workspace 目錄權限

3. **Git 操作失敗**
   - 檢查 Git 配置
   - 確保 GitHub 令牌有效

4. **對話歷史獲取失敗**
   - 確保 OpenClaw 的 sessions_history 工具可用
   - 或使用模擬對話歷史進行測試

### 日誌檢查
```bash
# 查看詳細日誌
cd ~/.openclaw/workspace-secretary
python3 skills/project-memory-manager/scripts/trigger_detector.py "測試消息" --workspace . --execute 2>&1 | tail -50
```

## 📞 支援
- GitHub: https://github.com/mismcinffh-svg/project-memory-manager
- 問題報告：GitHub Issues
- 版本檢查：`python3 scripts/upgrade.py --github-check`