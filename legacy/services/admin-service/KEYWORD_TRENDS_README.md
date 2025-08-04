# 熱門關鍵字趨勢模組

## 概述

熱門關鍵字趨勢模組允許收集並展示 TikTok、YouTube、Instagram、Facebook、Twitter 等平台的熱門關鍵字趨勢數據。

## 功能特性

### 🎯 核心功能
- **多平台支援**: 支援 5 大主流社交媒體平台
- **多時間週期**: 支援日、週、月、3個月、6個月週期
- **即時收集**: 定期自動收集最新趨勢數據
- **智能分析**: 提供趨勢統計和排行榜
- **搜尋功能**: 支援關鍵字搜尋和篩選
- **後台管理**: 完整的管理介面

### 📊 資料模型

#### `keyword_trends` 表格結構
```sql
CREATE TABLE keyword_trends (
    id INTEGER PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,           -- 平台名稱
    keyword VARCHAR(500) NOT NULL,            -- 關鍵字
    period VARCHAR(20) NOT NULL,              -- 時間週期
    rank INTEGER NOT NULL,                    -- 排名
    search_volume INTEGER,                    -- 搜尋量
    collected_at TIMESTAMP DEFAULT NOW(),     -- 收集時間
    region VARCHAR(10) DEFAULT 'global',      -- 地區
    category VARCHAR(100),                    -- 分類
    score INTEGER,                            -- 分數
    change_percentage VARCHAR(10),            -- 變化百分比
    metadata JSON                             -- 額外數據
);
```

## API 端點

### 1. 獲取關鍵字趨勢
```http
GET /admin/keyword-trends
```

**參數**:
- `platform` (可選): 平台名稱 (TikTok, YouTube, Instagram, Facebook, Twitter)
- `period` (可選): 時間週期 (day, week, month, 3_months, 6_months)
- `limit` (可選): 返回數量限制，預設 50

**回應範例**:
```json
{
  "success": true,
  "data": {
    "trends": [
      {
        "id": 1,
        "platform": "TikTok",
        "keyword": "AI影片生成",
        "period": "day",
        "rank": 1,
        "search_volume": 1500000,
        "change_percentage": "+25%",
        "region": "global",
        "category": "科技",
        "collected_at": "2025-08-03T12:00:00Z",
        "metadata": {
          "source": "tiktok_api_v1",
          "confidence": 0.95
        }
      }
    ],
    "total": 50,
    "platform": "TikTok",
    "period": "day"
  }
}
```

### 2. 獲取各平台熱門關鍵字排行榜
```http
GET /admin/keyword-trends/platforms
```

**參數**:
- `period` (可選): 時間週期，預設 "day"
- `top_n` (可選): 每個平台返回數量，預設 10

### 3. 獲取趨勢統計數據
```http
GET /admin/keyword-trends/statistics
```

**參數**:
- `days` (可選): 統計天數，預設 7

### 4. 搜尋關鍵字趨勢
```http
GET /admin/keyword-trends/search
```

**參數**:
- `q` (必需): 搜尋關鍵字
- `platforms` (可選): 平台列表，用逗號分隔
- `limit` (可選): 返回數量限制，預設 100

### 5. 手動觸發趨勢收集
```http
POST /admin/keyword-trends/collect
```

**請求體**:
```json
{
  "platforms": ["TikTok", "YouTube"],
  "period": "day"
}
```

### 6. 根據日期範圍獲取趨勢數據
```http
GET /admin/keyword-trends/date-range
```

**參數**:
- `start_date` (必需): 開始日期 (ISO 格式)
- `end_date` (必需): 結束日期 (ISO 格式)
- `platform` (可選): 平台名稱
- `period` (可選): 時間週期，預設 "day"

## 定時任務

### Celery 排程設定

系統自動設定以下定時任務：

1. **關鍵字趨勢收集**: 每小時15分執行
2. **舊版趨勢收集**: 每小時整點執行
3. **數據清理**: 每天凌晨3點清理90天前的數據

### 手動觸發任務

```python
from services.admin-service.tasks.trends_tasks import (
    schedule_keyword_trends_collection,
    trigger_daily_trends_collection,
    trigger_weekly_trends_collection
)

# 排程關鍵字趨勢收集
task = schedule_keyword_trends_collection(
    platforms=["TikTok", "YouTube"], 
    period="day"
)

# 觸發每日趨勢收集
daily_task = trigger_daily_trends_collection()

# 觸發每週趨勢收集
weekly_task = trigger_weekly_trends_collection()
```

## 使用方式

### 1. 資料庫遷移

```bash
# 執行 Alembic 遷移
alembic upgrade head
```

### 2. 啟動 Celery Worker

```bash
# 啟動 worker
celery -A services.admin-service.celery_app worker --loglevel=info --queues=trends

# 啟動 beat 排程器
celery -A services.admin-service.celery_app beat --loglevel=info
```

### 3. 啟動後台管理系統

```bash
# 啟動 FastAPI 應用
uvicorn services.admin-service.main:app --host 0.0.0.0 --port 8080
```

### 4. 訪問管理介面

瀏覽器訪問: `http://localhost:8080/trends`

## 數據收集策略

### 平台支援

| 平台 | API 來源 | 數據類型 | 更新頻率 |
|------|----------|----------|----------|
| TikTok | 模擬數據* | 熱門關鍵字 | 30分鐘 |
| YouTube | YouTube Data API v3 | 熱門影片標題 | 2小時 |
| Instagram | Instagram Basic Display API | 熱門標籤 | 1小時 |
| Facebook | Facebook Graph API | 熱門話題 | 1小時 |
| Twitter | Twitter API v2 | 即時趨勢 | 30分鐘 |

*註: TikTok 使用模擬數據，實際部署需要第三方服務或爬蟲

### 數據清理

- **自動清理**: 每天凌晨3點清理90天前的數據
- **手動清理**: 可透過 API 觸發清理任務
- **數據備份**: 建議在清理前備份重要數據

## 安全考慮

### API 認證
- 所有 API 端點需要 JWT 認證
- 支援權限控制 (trends:read, trends:write)

### 數據隱私
- API Key 加密存儲
- 日誌記錄操作審計
- 符合 GDPR 要求

### 速率限制
- API 調用頻率限制
- 防止濫用和過載

## 故障排除

### 常見問題

1. **趨勢數據為空**
   - 檢查 Celery worker 是否正常運行
   - 確認 API 配置正確
   - 查看任務執行日誌

2. **API 調用失敗**
   - 檢查認證 token 是否有效
   - 確認用戶權限設定
   - 檢查資料庫連接

3. **性能問題**
   - 檢查資料庫索引
   - 調整查詢參數 limit
   - 考慮增加 Redis 快取

### 日誌查看

```bash
# 查看 Celery 任務日誌
tail -f logs/celery.log

# 查看應用程式日誌
tail -f logs/app.log

# 查看趨勢收集日誌
grep "keyword_trends" logs/app.log
```

## 開發指南

### 添加新平台

1. 在 `social_trends.py` 中創建新的收集器類別
2. 實現 `collect_trends` 方法
3. 在 `SocialTrendsService` 中註冊新收集器
4. 更新前端平台選項

### 自訂時間週期

1. 在 `models.py` 中更新 period 選項
2. 在前端更新 `periodOptions`
3. 調整 Celery 排程設定

### 擴展 API

參考現有 API 端點的實現模式，確保：
- 適當的認證和權限檢查
- 錯誤處理和日誌記錄
- API 文檔更新

## 測試

### 運行測試

```bash
# 運行所有測試
pytest services/admin-service/test_keyword_trends.py -v

# 運行特定測試類別
pytest services/admin-service/test_keyword_trends.py::TestKeywordTrendModel -v

# 生成覆蓋率報告
pytest --cov=services.admin-service services/admin-service/test_keyword_trends.py
```

### 測試覆蓋

- ✅ 資料模型測試
- ✅ CRUD 操作測試 
- ✅ API 端點測試
- ✅ 趨勢收集服務測試
- ✅ Celery 任務測試
- ✅ 數據完整性測試
- ✅ 性能測試

## 部署建議

### 生產環境

1. **使用 PostgreSQL** 替代 SQLite
2. **設定 Redis 集群** 提高可用性
3. **配置負載均衡** 處理高流量
4. **啟用監控** Prometheus + Grafana
5. **設定備份策略** 定期備份數據

### 擴展性考慮

- 水平擴展 Celery worker
- 資料庫分片策略
- CDN 加速靜態資源
- 快取策略優化

## 版本歷史

- **v1.0.0** (2025-08-03): 初始版本，支援基本趨勢收集和管理功能
- 支援 5 大社交媒體平台
- 完整的 REST API
- 後台管理介面
- 定時任務排程
- 全面測試覆蓋

## 聯繫方式

如有問題或建議，請聯繫開發團隊或提交 Issue。