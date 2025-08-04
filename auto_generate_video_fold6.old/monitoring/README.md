# Auto Video System 監控系統

## 概述

本監控系統為 Auto Video 聲音克隆平台提供全面的系統監控、告警和可視化功能。基於 Prometheus + Grafana + Alertmanager 技術棧。

## 架構組件

### 核心監控服務
- **Prometheus**: 指標收集和存儲
- **Grafana**: 數據可視化和儀表板
- **Alertmanager**: 告警管理和通知

### 指標導出器
- **Node Exporter**: 系統級指標（CPU、記憶體、磁碟）
- **cAdvisor**: 容器指標
- **Redis Exporter**: Redis 指標
- **PostgreSQL Exporter**: 資料庫指標
- **Nginx Exporter**: Web 伺服器指標

## 快速開始

### 1. 啟動監控系統
```bash
./scripts/start-monitoring.sh
```

### 2. 訪問監控面板
- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### 3. 停止監控系統
```bash
./scripts/stop-monitoring.sh
```

## 監控指標

### 應用程式指標
- HTTP 請求率和回應時間
- 錯誤率統計
- API 端點效能
- 業務指標（影片處理、AI 推論等）

### 系統指標
- CPU 使用率
- 記憶體使用率
- 磁碟空間和 I/O
- 網路流量

### 服務指標
- 資料庫連接數和查詢效能
- Redis 快取命中率
- Celery 任務佇列狀態
- 微服務健康狀態

## 告警規則

### 嚴重告警 (Critical)
- 服務下線
- 磁碟空間不足 (<10%)
- 儲存空間不足

### 警告告警 (Warning)
- 高錯誤率 (>10%)
- 高回應時間 (>1s)
- 高 CPU 使用率 (>80%)
- 高記憶體使用率 (>80%)
- 資料庫連接數過高
- Celery 任務積壓

## 儀表板

### 系統概覽儀表板
- HTTP 請求率趨勢
- 服務狀態摘要
- 回應時間分佈
- CPU 使用率監控

### 詳細儀表板（可擴展）
- 個別服務詳細指標
- 資料庫效能分析
- AI 模型推論效能
- 社群媒體 API 使用統計

## 配置檔案

### Prometheus 配置
- `prometheus/prometheus.yml`: 主要配置
- `prometheus/rules/alerts.yml`: 告警規則

### Grafana 配置
- `grafana/provisioning/datasources/`: 資料源配置
- `grafana/provisioning/dashboards/`: 儀表板配置
- `grafana/dashboards/`: 儀表板 JSON 檔案

### Alertmanager 配置
- `alertmanager/alertmanager.yml`: 告警路由和接收器

## 維護指令

### 查看服務狀態
```bash
docker-compose -f docker-compose.monitoring.yml ps
```

### 查看服務日誌
```bash
docker-compose -f docker-compose.monitoring.yml logs [service-name]
```

### 重啟特定服務
```bash
docker-compose -f docker-compose.monitoring.yml restart [service-name]
```

### 更新配置
```bash
# 重新載入 Prometheus 配置
curl -X POST http://localhost:9090/-/reload

# 重啟 Grafana 以載入新儀表板
docker-compose -f docker-compose.monitoring.yml restart grafana
```

## 擴展功能

### 自訂指標
在各微服務中添加 Prometheus 指標端點：
```python
from prometheus_client import Counter, Histogram, generate_latest

# 自訂指標範例
REQUEST_COUNT = Counter('app_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('app_request_duration_seconds', 'Request duration')
```

### 新增告警規則
在 `prometheus/rules/alerts.yml` 中添加新規則：
```yaml
- alert: CustomAlert
  expr: your_metric > threshold
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "自訂告警"
    description: "詳細描述"
```

## 故障排除

### 常見問題
1. **服務無法啟動**: 檢查埠號衝突和權限設定
2. **指標收集失敗**: 確認目標服務的 `/metrics` 端點可訪問
3. **告警未觸發**: 檢查告警規則語法和時間窗口設定

### 日誌檢查
```bash
# 檢查 Prometheus 日誌
docker-compose -f docker-compose.monitoring.yml logs prometheus

# 檢查 Grafana 日誌
docker-compose -f docker-compose.monitoring.yml logs grafana
```

## 安全考量

- 預設密碼應在生產環境中更改
- 考慮啟用 HTTPS 和身份驗證
- 限制監控介面的網路訪問
- 定期備份監控數據和配置