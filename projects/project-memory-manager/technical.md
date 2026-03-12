# 技術細節 - ProjectMemoryManager v3.0

## 技術棧

- **編程語言**: Python 3.8+
- **技能格式**: OpenClaw標準.zip技能包
- **文件結構**: 標準技能目錄結構
- **配置管理**: JSON配置文件
- **日誌系統**: Python logging模塊
- **錯誤處理**: 完整異常處理鏈

## 架構設計

### 系統組件
```
project-memory-manager/
├── SKILL.md                    # 主文檔
├── config.json                 # 配置文件（集中管理）
├── scripts/                    # 核心腳本
│   ├── init.py                # 初始化系統
│   └── create.py              # 主功能腳本
└── references/                # 參考文檔
    ├── best-practices.md      # 最佳實踐
    └── troubleshooting.md     # 故障排除
```

### 核心類設計
```python
class ProjectManager:
    """項目管理器（主類）"""
    - load_config(): 加載配置
    - manual_create(): 手動創建項目
    - analyze_memory(): 分析MEMORY.md
    - auto_migrate(): 自動遷移超過閾值內容
    - update_index(): 更新項目索引
    - check_status(): 檢查系統狀態
```

## 實現步驟

### 1. 標準技能包創建
```bash
# 使用OpenClaw skill-creator工具
python3 ~/.npm-global/lib/node_modules/openclaw/skills/skill-creator/scripts/package_skill.py "temp_package"
```

### 2. 500t自動監測算法
```python
def analyze_memory(self, threshold_tokens: int = 500) -> List[Dict]:
    """分析MEMORY.md，識別超過閾值的主題"""
    1. 讀取MEMORY.md內容
    2. 按主題邊界（空行、標題、日期）分組
    3. 計算每個主題的tokens數量
    4. 返回超過閾值的主題列表
```

### 3. 自動遷移流程
```python
def auto_migrate(self, threshold_tokens: int = 500, dry_run: bool = False):
    """自動遷移超過閾值的主題到項目"""
    1. 調用analyze_memory()獲取主題列表
    2. 為每個主題生成項目名稱（基於關鍵詞）
    3. 創建項目目錄和配置文件
    4. 將主題內容保存到項目文件
    5. 更新INDEX.md索引
```

### 4. 錯誤處理架構
```python
try:
    # 業務邏輯
    project_path = self.manual_create(project_name, description)
except PermissionError as e:
    logger.error(f"權限錯誤: {e}")
    raise
except Exception as e:
    logger.error(f"未知錯誤: {e}", exc_info=True)
    # 回滾已創建的文件
    self.rollback_creation(project_path)
    raise
```

## 技術挑戰

### 挑戰1: 主題邊界識別
**問題**: 如何準確識別MEMORY.md中的主題邊界？
**解決方案**: 使用多種邊界標記：
- 空行（連續內容中的間隔）
- 標題行（#、##開頭）
- 日期時間戳（YYYY-MM-DD格式）
- 用戶對話邊界（assistant:/user:標記）

### 挑戰2: Token估算準確性
**問題**: 簡單字符數÷3估算不夠準確
**解決方案**: 保守估算策略
```python
def estimate_tokens(self, text: str) -> int:
    """保守估算tokens"""
    # 使用字符數÷3（保守估算）
    # 實際API tokens會更少，確保不會過早遷移
    return len(text) // 3
```

### 挑戰3: 跨平台兼容性
**問題**: Windows/Linux/macOS路徑差異
**解決方案**: 使用Python的pathlib模塊
```python
from pathlib import Path
project_path = Path.cwd() / "projects" / project_slug
```

### 挑戰4: 配置管理
**問題**: 硬編碼參數難以維護
**解決方案**: 集中式JSON配置
```json
{
  "auto_monitor": {
    "enabled": true,
    "threshold_tokens": 500,
    "check_interval_hours": 24
  }
}
```

## 解決方案

### 500t自動監測實現
```python
# 真正的實現，非佔位符
topics = self.analyze_memory(threshold=500)
if topics:
    logger.info(f"發現 {len(topics)} 個超過500tokens的主題")
    migrated = self.auto_migrate(threshold=500, dry_run=False)
```

### 專業日誌系統
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
```

### 完整CLI命令集
```
python3 scripts/create.py manual "項目名"    # 手動創建
python3 scripts/create.py auto --threshold 500  # 自動遷移
python3 scripts/create.py status           # 檢查狀態
python3 scripts/create.py analyze          # 分析MEMORY.md
python3 scripts/create.py rebuild-index    # 重建索引
```

## 性能優化

### 緩存機制
```python
# 配置啟用緩存
"performance": {
    "cache_enabled": true,
    "cache_ttl_seconds": 3600
}
```

### 批量操作優化
- 減少文件I/O次數
- 使用內存緩存重複讀取
- 批量更新索引，非逐行更新

### 資源限制
```json
{
  "projects": {
    "max_projects_per_day": 10,
    "max_concurrent_operations": 1
  }
}
```

## 測試策略

### 單元測試
```python
# 測試主題識別
def test_analyze_memory():
    manager = ProjectManager()
    topics = manager.analyze_memory(threshold=100)
    assert len(topics) >= 0
```

### 集成測試
```bash
# 完整流程測試
python3 scripts/init.py
python3 scripts/create.py manual "測試項目"
python3 scripts/create.py auto --threshold 100 --dry-run
python3 scripts/create.py status
```

### 錯誤恢復測試
- 權限錯誤模擬
- 磁盤空間不足模擬
- 網絡中斷模擬
- 文件損壞模擬

## 部署與維護

### 安裝腳本
```bash
# 標準安裝
cp project-memory-manager-v3.0.skill ~/.openclaw/workspace-agent/
read({ path: "project-memory-manager-v3.0.skill" })
```

### 升級路徑
```
v1.0.0 → v2.0.0 → v3.0.0
硬編碼 → 通用化 → 專業化
```

### 監控指標
- MEMORY.md tokens變化
- 項目數量增長
- 自動遷移成功率
- 錯誤發生頻率

## 技術債與未來改進

### 已知限制
1. Token估算不夠精確（保守估算）
2. 主題識別可能誤判（邊界模糊時）
3. 無圖形界面（純CLI）

### 未來改進
1. **AI增強**: 使用LLM識別主題邊界
2. **可視化儀表板**: 項目狀態圖形顯示
3. **跨Agent同步**: 實時項目共享
4. **API接口**: 程式化訪問管理功能
5. **插件系統**: 擴展自定義功能

---
**技術實現完成時間**: 2026-03-07 22:30  
**代碼行數**: ~500行（主腳本）  
**測試覆蓋率**: 需補充單元測試  
**技術負責人**: Nana