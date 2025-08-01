# Phase 4-6 完整部署指南
# 🚀 CI/CD + 監控 + 性能優化系統

> **完成時間**: 2025-08-01  
> **涵蓋階段**: Phase 4 (CI/CD)、Phase 5 (監控告警)、Phase 6 (性能優化)

## 📋 概述

本指南涵蓋了 Auto Video Generation System 的完整部署策略，包括：
- ✅ **Phase 4**: CI/CD 流水線自動化
- ✅ **Phase 5**: Prometheus/Grafana 監控告警系統  
- ✅ **Phase 6**: Docker 優化與性能調優

## 🎯 快速開始

### 1. 一鍵部署命令

```bash
# 1. 複製環境配置
cp .env.template .env

# 2. 啟動完整系統 (包含監控)
chmod +x scripts/deploy-unified.sh
./scripts/deploy-unified.sh docker development --with-monitoring

# 3. 驗證部署狀態
python scripts/deployment-test.py --env development --json
```

### 2. 訪問系統服務

| 服務 | URL | 說明 |
|------|-----|------|
| **API Gateway** | http://localhost:8000 | 主要 API 入口 |
| **Frontend** | http://localhost:3000 | Web 界面 |
| **Prometheus** | http://localhost:9090 | 監控指標 |
| **Grafana** | http://localhost:3001 | 儀表板 (admin/admin123) |
| **AlertManager** | http://localhost:9093 | 告警管理 |

## 🏗️ Phase 4: CI/CD 自動化流程

### GitHub Actions 工作流程

#### 主要 CI/CD 流水線 (`.github/workflows/ci-cd-main.yml`)

```yaml
# 觸發條件
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [development, staging, production]
```

#### 流程階段

1. **程式碼品質檢查** 🔍
   - Python: Black, Flake8, MyPy, Bandit
   - Frontend: ESLint, Prettier, TypeScript
   - 差異化檢測 (只測試變更的服務)

2. **安全性掃描** 🛡️
   - Snyk 依賴漏洞掃描
   - Trivy 容器安全掃描
   - SARIF 結果上傳到 GitHub Security

3. **自動化測試** 🧪
   - 單元測試 (pytest + jest)
   - 整合測試 (PostgreSQL + Redis)
   - E2E 測試 (完整服務鏈測試)

4. **容器構建** 🐳
   - 多階段 Docker 構建
   - 多架構支援 (amd64/arm64)
   - GitHub Container Registry 推送

5. **自動部署** 🚀
   - Development: 自動部署
   - Staging: PR 合併觸發
   - Production: 手動觸發 + 審核

### 本地 CI/CD 測試

```bash
# 1. 運行程式碼品質檢查
black --check auto_generate_video_fold6/
flake8 auto_generate_video_fold6/
mypy auto_generate_video_fold6/

# 2. 安全性掃描
python scripts/security-audit.py

# 3. 運行測試套件
pytest tests/ -v --cov=auto_generate_video_fold6

# 4. 容器構建測試
docker build -t test-image -f services/api-gateway/Dockerfile services/api-gateway/
```

## 📊 Phase 5: 監控告警系統

### Prometheus 監控配置

#### 監控目標 (`monitoring/prometheus/prometheus.yml`)

```yaml
scrape_configs:
  - job_name: 'api-gateway'
    static_configs:
      - targets: ['api-gateway:8000']
    metrics_path: /metrics
    scrape_interval: 5s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 10s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 10s
```

#### 關鍵告警規則 (`monitoring/prometheus/alert_rules.yml`)

| 告警名稱 | 觸發條件 | 嚴重程度 | 說明 |
|----------|----------|----------|------|
| **ServiceDown** | `up == 0` (1分鐘) | Critical | 服務停機 |
| **HighCPUUsage** | CPU > 80% (5分鐘) | Warning | CPU 使用率過高 |
| **HighMemoryUsage** | Memory > 85% (5分鐘) | Warning | 記憶體不足 |
| **HighHTTPErrorRate** | 5xx 錯誤率 > 5% | Critical | API 錯誤率過高 |
| **DatabaseConnections** | PG 連接數 > 80% | Warning | 資料庫連接池耗盡 |

### Grafana 儀表板

#### 系統概覽儀表板

```bash
# 啟動監控服務
cd monitoring/
docker-compose -f docker-compose.monitoring.yml up -d

# 訪問 Grafana
open http://localhost:3001
# 帳號: admin / 密碼: admin123
```

#### 預設儀表板
- **System Overview**: 整體系統狀態
- **Service Performance**: 各服務性能指標
- **Database Monitoring**: 資料庫監控
- **Container Metrics**: Docker 容器指標

### 告警通知配置

#### AlertManager 設定 (`monitoring/alertmanager/alertmanager.yml`)

```yaml
# 告警路由
route:
  group_by: ['alertname', 'cluster', 'service']
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      group_wait: 0s
      repeat_interval: 30m

# 通知接收器  
receivers:
  - name: 'critical-alerts'
    email_configs:
      - to: 'admin@auto-video-generation.com'
        subject: '🚨 [CRITICAL] {{ .GroupLabels.alertname }}'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#alerts-critical'
```

#### 設置告警通知

```bash
# 1. 設置環境變數
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# 2. 重啟 AlertManager
docker-compose -f monitoring/docker-compose.monitoring.yml restart alertmanager
```

## ⚡ Phase 6: 性能優化

### Docker 容器優化

#### 優化策略

1. **基礎映像優化**
   ```dockerfile
   # 使用 Alpine Linux 減少映像大小
   FROM python:3.11-alpine as base
   
   # 多階段構建
   FROM base as builder
   # 安裝依賴
   
   FROM base as production
   # 只複製運行時需要的文件
   ```

2. **層次合併**
   ```dockerfile
   # ❌ 多個 RUN 指令
   RUN apt-get update
   RUN apt-get install -y curl
   RUN rm -rf /var/lib/apt/lists/*
   
   # ✅ 合併 RUN 指令
   RUN apt-get update && \
       apt-get install -y curl && \
       rm -rf /var/lib/apt/lists/*
   ```

#### 容器優化工具

```bash
# 1. 分析容器大小
python scripts/docker-optimization.py --service api-gateway

# 2. 優化所有服務
python scripts/docker-optimization.py --output docker-optimization-report.md

# 3. 使用優化的 Dockerfile
cp services/optimization/Dockerfile.optimized services/api-gateway/Dockerfile.optimized
```

### 系統性能調優

#### 性能分析工具

```bash
# 1. 系統性能分析
python scripts/system-performance-analyzer.py --json --output performance-report.md

# 2. 性能測試 (60秒)
python scripts/system-performance-analyzer.py --test 60

# 3. 生成成本分析
python scripts/system-performance-analyzer.py --json
```

#### 關鍵性能指標

| 指標 | 目標值 | 監控方式 |
|------|--------|----------|
| **API 回應時間** | < 200ms (95th) | Prometheus |
| **CPU 使用率** | < 70% | Node Exporter |
| **記憶體使用率** | < 80% | Node Exporter |
| **資料庫連接** | < 80% | PostgreSQL Exporter |
| **錯誤率** | < 1% | Application Metrics |

#### 性能優化建議

1. **應用層優化**
   - 使用連接池 (PostgreSQL, Redis)
   - 實施快取策略 (Redis, 記憶體快取)
   - 異步處理 (Celery 任務佇列)

2. **資料庫優化**
   - 索引優化
   - 查詢優化
   - 讀寫分離

3. **基礎設施優化**
   - 負載均衡 (Nginx)
   - CDN 加速 (靜態資源)
   - 自動擴展 (Kubernetes HPA)

## 🚀 實際部署測試

### 部署測試工具

```bash
# 1. 綜合部署測試
python scripts/deployment-test.py --env development --json

# 2. 特定環境測試
python scripts/deployment-test.py --env staging --load-test

# 3. 生產環境健康檢查
python scripts/deployment-test.py --env production --output prod-health-check.md
```

### 測試覆蓋範圍

#### 自動化測試項目

- ✅ **Docker 服務狀態**: 容器運行狀況
- ✅ **資料庫連接**: PostgreSQL, Redis 連接測試
- ✅ **服務健康檢查**: 各微服務 `/health` 端點
- ✅ **API 端點測試**: 關鍵 API 功能測試
- ✅ **監控服務**: Prometheus, Grafana 可用性
- ✅ **負載測試**: 基本並發能力測試

#### 測試報告範例

```bash
# 部署測試報告
**測試時間**: 2025-08-01T10:30:00
**測試環境**: development

## 測試總結
- **總測試數**: 12
- **通過**: 11 ✅
- **失敗**: 1 ❌  
- **錯誤**: 0 ⚠️
- **整體狀態**: mostly_passed

## 負載測試結果
- **總請求數**: 450
- **成功率**: 98.9%
- **平均回應時間**: 45.2ms
- **請求/秒**: 30.0
```

## 📋 部署檢查清單

### 部署前準備

- [ ] 環境變數配置完成 (`.env` 文件)
- [ ] 資料庫連接字串正確
- [ ] API 密鑰已設定 (OpenAI, Google AI, etc.)
- [ ] Docker 和 Docker Compose 已安裝
- [ ] SSL 憑證準備 (生產環境)

### 部署步驟

1. **基礎設施部署**
   ```bash
   # 啟動資料庫和快取
   docker-compose -f docker-compose.unified.yml up -d postgres redis minio
   
   # 執行資料庫遷移
   docker-compose -f docker-compose.unified.yml up migrations
   ```

2. **應用服務部署**
   ```bash
   # 啟動微服務
   docker-compose -f docker-compose.unified.yml up -d auth-service video-service api-gateway
   
   # 啟動前端
   docker-compose -f docker-compose.unified.yml up -d frontend
   ```

3. **監控系統部署**
   ```bash
   # 啟動監控服務
   cd monitoring/
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

### 部署後驗證

- [ ] 所有服務健康檢查通過
- [ ] API 端點回應正常
- [ ] 前端應用載入正常
- [ ] 資料庫遷移成功執行
- [ ] 監控指標正常收集
- [ ] 告警規則正常運作

## 🔧 故障排除

### 常見問題

#### 1. 服務啟動失敗
```bash
# 檢查服務日誌
docker-compose -f docker-compose.unified.yml logs service-name

# 檢查容器狀態
docker ps -a
```

#### 2. 資料庫連接失敗
```bash
# 測試資料庫連接
pg_isready -h localhost -p 5432
redis-cli -h localhost -p 6379 ping

# 檢查網路連接
docker network ls
docker network inspect auto-video-network
```

#### 3. 監控服務異常
```bash
# 檢查 Prometheus 配置
docker exec prometheus promtool check config /etc/prometheus/prometheus.yml

# 重啟監控服務
cd monitoring/
docker-compose -f docker-compose.monitoring.yml restart
```

#### 4. CI/CD 流程失敗
- 檢查 GitHub Secrets 配置
- 驗證 Docker 映像構建
- 查看 GitHub Actions 日誌

### 性能問題診斷

```bash
# 1. 系統資源監控
python scripts/system-performance-analyzer.py --test 30

# 2. 容器資源使用
docker stats

# 3. 應用程式日誌分析
docker-compose logs --follow api-gateway
```

## 🔄 維護和更新

### 定期維護任務

#### 每日
- [ ] 檢查服務健康狀態
- [ ] 查看告警通知
- [ ] 監控系統資源使用

#### 每週  
- [ ] 清理未使用的 Docker 映像
- [ ] 檔案系統空間檢查
- [ ] 性能指標分析

#### 每月
- [ ] 更新依賴套件
- [ ] 安全性掃描
- [ ] 備份和恢復測試
- [ ] 成本分析和優化

### 更新部署

```bash
# 1. 拉取最新代碼
git pull origin main

# 2. 重建服務 (零停機時間)
docker-compose -f docker-compose.unified.yml up -d --no-deps --build service-name

# 3. 驗證部署
python scripts/deployment-test.py --env production
```

## 📈 擴展策略

### 水平擴展

```bash
# Docker Compose 擴展
docker-compose -f docker-compose.unified.yml up -d --scale api-gateway=3

# Kubernetes 擴展  
kubectl scale deployment api-gateway --replicas=5 -n auto-video-generation
```

### 垂直擴展

```yaml
# 增加資源限制
services:
  api-gateway:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
```

## 🎯 下一步發展

### 進階優化
- [ ] 實施服務網格 (Istio)
- [ ] 建立 CI/CD GitOps 流程
- [ ] 機器學習驅動的自動擴展
- [ ] 全球 CDN 部署

### 企業級功能
- [ ] 多租戶架構
- [ ] 企業級 SSO 整合
- [ ] 合規性和審核日誌
- [ ] 災難恢復策略

---

## 📞 支援和文檔

- **項目倉庫**: https://github.com/ilyi1116/auto-video-generation-fold6
- **問題報告**: GitHub Issues
- **技術文檔**: `/docs` 目錄
- **API 文檔**: http://localhost:8000/docs (啟動後訪問)

---

> 🎉 **恭喜！** 您現在擁有一個完整的生產級 AI 影片生成系統，包含 CI/CD、監控告警和性能優化！