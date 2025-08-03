# 分散式追蹤系統

這是一個完整的分散式追蹤系統，提供跨服務的請求追蹤、性能監控和問題診斷功能。

## 功能特色

### 🔍 核心功能
- **OpenTelemetry 整合**: 標準化的追蹤數據收集
- **自動儀器化**: FastAPI、Celery、HTTP 請求自動追蹤
- **分散式上下文傳播**: 跨服務的追蹤上下文維護
- **實時數據收集**: 高性能的追蹤數據收集器
- **智能分析**: 多維度的性能和錯誤分析

### 📊 分析能力
- **性能分析**: 響應時間統計、P95/P99 指標
- **錯誤分析**: 錯誤模式識別和趨勢分析
- **服務依賴**: 服務間調用關係分析
- **健康評分**: 基於多指標的系統健康評估
- **慢操作識別**: 性能瓶頸自動發現

### 🎯 可視化界面
- **追蹤列表**: 詳細的追蹤記錄瀏覽
- **性能儀表板**: 實時性能指標展示
- **健康監控**: 系統健康狀態監控
- **搜索功能**: 強大的追蹤數據搜索
- **導出功能**: 追蹤數據批量導出

## 系統架構

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Tracer Core   │    │   Middleware    │    │   Collector     │
│                 │    │                 │    │                 │
│ - OpenTelemetry │    │ - HTTP 追蹤     │    │ - 數據收集      │
│ - 上下文管理    │    │ - DB 追蹤       │    │ - 批量處理      │
│ - Span 管理     │    │ - Celery 追蹤   │    │ - 檔案存儲      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                ┌─────────────────┴─────────────────┐
                │            Analyzer              │
                │                                  │
                │ - 性能分析     - 錯誤分析        │
                │ - 服務分析     - 趨勢分析        │
                │ - 健康評分     - 報告生成        │
                └──────────────────────────────────┘
```

## 快速開始

### 1. 基本配置

```python
# 在 main.py 中啟用追蹤中間件
from .tracing import TracingMiddleware

app.add_middleware(
    TracingMiddleware,
    service_name="admin-service",
    exclude_paths=["/health", "/metrics"]
)
```

### 2. 函數追蹤

```python
from .tracing import trace_function

@trace_function("user.get_profile", capture_args=True)
async def get_user_profile(user_id: str):
    # 函數會自動被追蹤
    return user_profile
```

### 3. 手動追蹤

```python
from .tracing import start_span, add_span_attributes

# 開始新的 Span
context = start_span("custom.operation")

# 添加屬性
add_span_attributes({
    "user_id": "12345",
    "operation_type": "data_processing"
})

# 完成操作後會自動結束 Span
```

## API 端點

### 追蹤查詢
```http
GET /admin/tracing?service_name=admin-service&hours=24
```

### 性能分析
```http
GET /admin/tracing/analysis/performance?hours=24
```

### 錯誤分析
```http
GET /admin/tracing/analysis/errors?hours=24
```

### 服務健康檢查
```http
GET /admin/tracing/health/admin-service
```

### 導出追蹤數據
```http
POST /admin/tracing/export?start_date=2024-01-01&end_date=2024-01-31
```

## 配置選項

### TracingMiddleware 選項
```python
TracingMiddleware(
    app,
    service_name="your-service",           # 服務名稱
    exclude_paths=["/health", "/metrics"], # 排除的路徑
    capture_headers=False,                 # 是否捕獲 HTTP 標頭
    capture_params=False                   # 是否捕獲查詢參數
)
```

### TraceCollector 選項
```python
TraceCollector(
    storage_path="/path/to/traces",  # 存儲路徑
    max_memory_traces=10000,         # 內存中最大追蹤數
    batch_size=100                   # 批量寫入大小
)
```

## 性能指標

### 收集的指標
- **響應時間**: 平均值、中位數、P95、P99
- **錯誤率**: 錯誤請求百分比
- **吞吐量**: 每分鐘/每小時請求數
- **服務依賴**: 服務間調用次數和延遲

### 健康評分算法
```
健康評分 = 錯誤率評分 × 0.6 + 性能評分 × 0.4

錯誤率評分 = max(0, 100 - 錯誤率 × 10)
性能評分 = max(0, 100 - 平均響應時間 / 10)
```

## 最佳實踐

### 1. 追蹤粒度
- ✅ 追蹤 API 端點和主要業務邏輯
- ✅ 追蹤外部服務調用
- ❌ 避免追蹤過於細粒度的操作
- ❌ 避免在高頻循環中創建 Span

### 2. 屬性設置
```python
# 推薦的屬性設置
add_span_attributes({
    "user.id": user_id,
    "operation.type": "database_query",
    "database.table": "users",
    "result.count": len(results)
})
```

### 3. 錯誤處理
```python
@trace_function("service.operation")
async def risky_operation():
    try:
        result = await external_service_call()
        return result
    except Exception as e:
        # 錯誤會自動被追蹤
        add_span_attributes({
            "error.handled": True,
            "error.recovery": "fallback_used"
        })
        return fallback_result
```

## 故障排除

### 常見問題

1. **追蹤數據不顯示**
   - 檢查中間件是否正確安裝
   - 確認服務名稱配置正確
   - 查看 TraceCollector 日誌

2. **性能影響**
   - 調整批量處理大小
   - 減少追蹤的屬性數量
   - 使用排除路徑過濾高頻請求

3. **存儲空間不足**
   - 縮短數據保留期限
   - 啟用自動清理任務
   - 調整批量寫入策略

### 監控指標
```python
# 獲取收集器統計
stats = trace_collector.get_stats()
print(f"總追蹤數: {stats['total_traces']}")
print(f"錯誤追蹤數: {stats['error_traces']}")
print(f"內存使用: {stats['memory_traces_count']}")
```

## 進階功能

### 自定義分析器
```python
from .tracing.analyzer import TraceAnalyzer

analyzer = TraceAnalyzer()

# 自定義分析
async def custom_analysis():
    traces = await trace_collector.get_traces(
        service_name="my-service",
        hours=24
    )
    
    # 自定義邏輯
    slow_traces = [
        trace for trace in traces 
        if trace.get("duration_ms", 0) > 1000
    ]
    
    return {"slow_traces_count": len(slow_traces)}
```

### 自定義導出格式
```python
async def export_to_custom_format():
    traces = await trace_collector.get_traces(limit=1000)
    
    # 轉換為自定義格式
    custom_format = {
        "version": "1.0",
        "traces": [
            {
                "id": trace["trace_id"],
                "duration": trace.get("duration_ms", 0),
                "service": trace["service_name"]
            }
            for trace in traces
        ]
    }
    
    return custom_format
```

## 維護和運維

### 定期任務
- **健康檢查**: 每10分鐘檢查系統健康狀態
- **數據清理**: 每天清理過期的追蹤數據
- **報告生成**: 每天生成分析報告

### 備份和恢復
```bash
# 備份追蹤數據
cp -r /data/traces /backup/traces_$(date +%Y%m%d)

# 恢復追蹤數據
cp -r /backup/traces_20240101 /data/traces
```

### 性能調優
```python
# 調整收集器參數
trace_collector = TraceCollector(
    max_memory_traces=20000,    # 增加內存緩存
    batch_size=200              # 增加批量大小
)

# 調整清理策略
tracer.clear_cache(max_age=1800)  # 30分鐘清理一次
```

## 集成指南

### 與監控系統集成
```python
# Prometheus 指標導出
from prometheus_client import Counter, Histogram

trace_counter = Counter('traces_total', 'Total traces')
response_time = Histogram('response_time_seconds', 'Response time')

@trace_function("api.endpoint")
async def api_endpoint():
    trace_counter.inc()
    with response_time.time():
        return await process_request()
```

### 與告警系統集成
```python
async def health_check_with_alerts():
    health = await trace_analyzer.get_health_score()
    
    if health["health_score"] < 70:
        await send_alert({
            "severity": "warning",
            "message": f"系統健康評分偏低: {health['health_score']}"
        })
```

## 版本更新

### v1.0.0 (2024-01-01)
- ✨ 初始版本發布
- ✨ 基礎追蹤功能
- ✨ 性能分析
- ✨ Web 界面

### 即將推出
- 📊 更豐富的可視化圖表
- 🔔 實時告警功能
- 📈 趨勢預測
- 🔗 更多第三方系統集成

---

**支持和反饋**: 如有問題或建議，請提交 Issue 或聯繫開發團隊。