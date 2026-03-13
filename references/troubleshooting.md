# 故障排除指南

## 🚨 緊急問題

### P0: 安裝失敗 - 文件格式混淆
**症狀**: Agent無法識別.skill文件，或執行錯誤
**原因**: 舊版本使用Python腳本作為.skill文件，不符合OpenClaw標準

**解決方案**:
```bash
# 1. 使用新版標準技能包
# 文件: project-memory-manager-v3.0.skill
# 格式: 標準zip包，包含SKILL.md和所有文件

# 2. 標準安裝流程
cp project-memory-manager-v3.0.skill ~/.openclaw/workspace-[agent]/
# 讓Agent閱讀文件，自動安裝

# 3. 如果已有舊版，先清理
rm -rf ~/.openclaw/workspace-[agent]/skills/project-memory-manager/
rm -f ~/.openclaw/workspace-[agent]/ProjectMemoryManager-*.skill
```

### P0: Python環境問題
**症狀**: `python3: command not found` 或版本過低
**原因**: Python 3.8+未安裝

**解決方案**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# macOS (使用Homebrew)
brew install python@3.11

# Windows (WSL)
wsl --install -d Ubuntu
# 然後安裝Python

# 驗證安裝
python3 --version  # 需要3.8+
```

### P0: 權限不足
**症狀**: `Permission denied` 創建文件/目錄失敗
**原因**: 對workspace目錄無寫入權限

**解決方案**:
```bash
# 檢查權限
ls -la ~/.openclaw/

# 修復權限
chmod -R 755 ~/.openclaw/
chmod +x ~/.openclaw/workspace-*/skills/project-memory-manager/scripts/*.py

# 如果使用sudo創建的目錄
sudo chown -R $USER:$USER ~/.openclaw/
```

## 🔧 常見問題 (P1-P2)

### P1: 缺乏清晰安裝指引
**症狀**: 不知道如何開始，步驟混亂

**標準安裝流程**:
```bash
# 方法A: 標準技能安裝（推薦）
1. 複製技能包到workspace
   cp project-memory-manager-v3.0.skill ~/.openclaw/workspace-your-agent/

2. 讓Agent閱讀技能文件
   read({ path: "project-memory-manager-v3.0.skill" })

3. 系統自動初始化
4. 驗證安裝: python3 scripts/create.py status

# 方法B: 手動安裝（調試用）
1. 創建技能目錄
   mkdir -p ~/.openclaw/workspace-your-agent/skills/project-memory-manager/{scripts,references}

2. 複製所有文件
   cp -r skills/project-memory-manager/* ~/.openclaw/workspace-your-agent/skills/project-memory-manager/

3. 初始化
   cd ~/.openclaw/workspace-your-agent
   python3 skills/project-memory-manager/scripts/init.py

4. 測試
   python3 skills/project-memory-manager/scripts/create.py manual "測試項目"
```

### P1: Python代碼質量問題
**症狀**: 腳本運行錯誤、異常退出、日誌混亂

**診斷命令**:
```bash
# 1. 檢查Python語法
python3 -m py_compile skills/project-memory-manager/scripts/*.py

# 2. 運行單元測試（如果有的話）
python3 -m pytest skills/project-memory-manager/tests/

# 3. 檢查代碼風格
python3 -m pylint skills/project-memory-manager/scripts/

# 4. 查看日誌
tail -f projects/_logs/*.log
```

**常見錯誤修復**:
```python
# 錯誤: ModuleNotFoundError
# 解決: 安裝缺失模塊或使用內置模塊
import sys
sys.path.append('/path/to/modules')

# 錯誤: UnicodeDecodeError
# 解決: 指定編碼
with open(file, 'r', encoding='utf-8') as f:

# 錯誤: PermissionError
# 解決: 檢查權限或使用try-except
try:
    os.mkdir(path)
except PermissionError:
    print(f"權限不足: {path}")
```

### P2: 500t自動監測未觸發
**症狀**: MEMORY.md超過500tokens但未自動遷移

**診斷步驟**:
```bash
# 1. 檢查配置
cat skills/project-memory-manager/config.json | jq '.auto_monitor'

# 2. 手動運行檢測
python3 scripts/create.py analyze --threshold 500

# 3. 強制運行遷移
python3 scripts/create.py auto --threshold 500

# 4. 檢查日誌
grep -i "auto_migrate\|analyze" projects/_logs/*.log
```

**可能原因**:
1. **配置關閉**: `auto_monitor.enabled: false`
2. **閾值過高**: 設置為>500
3. **主題識別失敗**: 無法識別連續主題
4. **權限問題**: 無法創建項目目錄

**解決方案**:
```bash
# 編輯配置
vi skills/project-memory-manager/config.json
# 設置: "enabled": true, "threshold_tokens": 300

# 手動觸發
python3 scripts/create.py auto --threshold 300 --dry-run  # 先測試
python3 scripts/create.py auto --threshold 300  # 實際執行

# 設置定時任務 (crontab)
0 */6 * * * cd /path/to/workspace && python3 scripts/create.py auto --threshold 500
```

### P2: 文檔不完整
**症狀**: 缺少某些功能的說明，步驟不清晰

**完整文檔結構**:
```
skills/project-memory-manager/
├── SKILL.md                    # 主文檔（含安裝指引）
├── references/
│   ├── best-practices.md      # 最佳實踐
│   ├── troubleshooting.md     # 故障排除（本文檔）
│   └── api-reference.md       # API參考（如有）
├── scripts/
│   ├── init.py                # 初始化腳本
│   ├── create.py              # 主功能腳本
│   └── README.txt             # 腳本說明
└── examples/                  # 示例文件
    ├── sample-project/
    └── migration-demo/
```

**缺少時補充**:
```bash
# 生成幫助文檔
python3 scripts/create.py --help > references/command-help.txt
python3 scripts/init.py --help >> references/command-help.txt

# 創建示例
mkdir -p examples/sample-project
cp -r projects/_templates/* examples/sample-project/
```

## 🛠️ 系統問題 (P3)

### P3: 索引損壞
**症狀**: INDEX.md格式錯誤，項目顯示異常

**修復命令**:
```bash
# 1. 備份當前索引
cp projects/INDEX.md projects/INDEX.md.backup.$(date +%Y%m%d)

# 2. 重建索引
python3 scripts/create.py rebuild-index

# 3. 驗證
python3 scripts/create.py status
```

**預防措施**:
```bash
# 定期備份
0 2 * * * cd /path/to/workspace && cp projects/INDEX.md projects/_backups/INDEX.md.$(date +\%Y\%m\%d)

# 完整性檢查
0 3 * * * cd /path/to/workspace && python3 scripts/create.py status | grep -q "index_file_exists: true" || echo "索引損壞"
```

### P3: 項目文件丟失
**症狀**: 項目目錄存在但文件缺失

**恢復步驟**:
```bash
# 1. 檢查項目結構
find projects/ -type d -name "project-*" | while read dir; do
    echo "檢查: $dir"
    ls -la "$dir"
done

# 2. 從模板恢復文件
for dir in projects/project-*/; do
    cp projects/_templates/*.md "$dir" 2>/dev/null
done

# 3. 重新生成project.json
python3 scripts/repair.py --repair-projects  # 需實現此腳本
```

### P3: 性能問題
**症狀**: 腳本運行緩慢，影響Agent響應

**優化建議**:
```bash
# 1. 啟用緩存
# 在config.json中添加
"cache": {
    "enabled": true,
    "ttl_seconds": 3600
}

# 2. 減少檢查頻率
"auto_monitor": {
    "check_interval_hours": 24  # 改為每天一次
}

# 3. 限制項目數量
"projects": {
    "max_projects": 100,
    "auto_archive_days": 30
}
```

## 📋 診斷工具

### 系統健康檢查腳本
創建 `scripts/health-check.py`:
```python
#!/usr/bin/env python3
import sys
from pathlib import Path

def check_system():
    workspace = Path.cwd()
    print(f"工作空間: {workspace}")
    
    # 檢查核心文件
    checks = [
        ("MEMORY.md", workspace / "MEMORY.md"),
        ("projects/", workspace / "projects"),
        ("INDEX.md", workspace / "projects" / "INDEX.md"),
        ("技能目錄", workspace / "skills" / "project-memory-manager"),
        ("配置", workspace / "skills" / "project-memory-manager" / "config.json")
    ]
    
    for name, path in checks:
        exists = path.exists()
        print(f"{'✅' if exists else '❌'} {name}: {path}")
        if exists and path.is_file():
            try:
                size = path.stat().st_size
                print(f"    大小: {size} bytes")
            except:
                pass
    
    # 檢查Python環境
    import subprocess
    try:
        result = subprocess.run(["python3", "--version"], capture_output=True, text=True)
        print(f"✅ Python: {result.stdout.strip()}")
    except:
        print("❌ Python: 未安裝")
    
    # 檢查腳本權限
    script_dir = workspace / "skills" / "project-memory-manager" / "scripts"
    if script_dir.exists():
        for script in script_dir.glob("*.py"):
            if script.is_file() and oct(script.stat().st_mode)[-3:] != "755":
                print(f"⚠️  腳本權限需修復: {script}")
    
    print("\n🎯 建議:")
    print("1. 運行: python3 scripts/create.py status")
    print("2. 測試: python3 scripts/create.py manual \"測試\"")
    print("3. 檢查: tail -n 20 projects/_logs/*.log")

if __name__ == "__main__":
    check_system()
```

### 日誌分析命令
```bash
# 查看錯誤日誌
grep -i "error\|exception\|failed" projects/_logs/*.log

# 查看自動遷移日誌
grep -i "auto_migrate\|analyze" projects/_logs/*.log | tail -20

# 查看項目創建記錄
grep -i "manual_create\|項目創建" projects/_logs/*.log

# 查看系統啟動日誌
grep -i "init\|initialize" projects/_logs/*.log
```

## 📞 支持渠道

### 即時診斷
```bash
# 複製此命令運行
cd ~/.openclaw/workspace-your-agent && \
echo "=== 系統診斷 ===" && \
python3 scripts/create.py status && \
echo "=== 日誌最後10行 ===" && \
tail -10 projects/_logs/*.log 2>/dev/null || echo "無日誌" && \
echo "=== 項目統計 ===" && \
ls projects/ | grep -v "^_" | wc -l | xargs echo "項目數量:" && \
echo "=== 完成 ==="
```

### 問題報告模板
```
**問題描述**:
**重現步驟**:
**期望結果**:
**實際結果**:
**環境信息**:
- Agent: workspace-xxx
- Python版本: 
- 技能版本: 
- 錯誤日誌: (貼上相關日誌)
**已嘗試的解決方案**:
```

### 緊急聯繫
如果以上方法都無效:
1. **恢復備份**: 從 `projects/_backups/` 恢復最近備份
2. **重新安裝**: 刪除技能目錄，重新安裝v3.0
3. **手動修復**: 直接編輯MEMORY.md和INDEX.md
4. **尋求幫助**: 聯繫技能作者(Nana)或OpenClaw社區

---

**記住**: 定期備份是防止數據丟失的最佳方法。建議每天自動備份項目目錄。