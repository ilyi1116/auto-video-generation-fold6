# Auto Video Generation System - 部署策略指南

## 📋 概述

本文檔說明自動影片生成系統的完整部署策略，整合了 Phase 2 的統一資料庫系統和 Phase 3 的容器化部署配置。

## 🏗️ 系統架構

### 核心服務架構
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  API Gateway    │    │  Load Balancer  │
│  (SvelteKit)    │◄───┤   (FastAPI)     │◄───┤    (Nginx)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
     ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
     │  Auth Service   │ │  Video Service  │ │  Trend Service  │
     │   (FastAPI)     │ │   (FastAPI)     │ │   (FastAPI)     │
     └─────────────────┘ └─────────────────┘ └─────────────────┘
                │               │               │
                └───────────────┼───────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │ PostgreSQL  │    │    Redis    │    │   MinIO     │
    │ (Database)  │    │   (Cache)   │    │ (Storage)   │
    └─────────────┘    └─────────────┘    └─────────────┘
```

## 🚀 部署選項

### 1. 開發環境部署 (Docker Compose)

#### 快速啟動
```bash
# 複製環境配置
cp .env.template .env

# 編輯環境變數
nano .env

# 啟動整個系統
docker-compose -f docker-compose.unified.yml up -d

# 檢查服務狀態
docker-compose -f docker-compose.unified.yml ps
```

#### 階段性啟動
```bash
# 1. 先啟動基礎設施
docker-compose -f docker-compose.unified.yml up -d postgres redis minio

# 2. 執行資料庫遷移
docker-compose -f docker-compose.unified.yml up migrations

# 3. 啟動微服務
docker-compose -f docker-compose.unified.yml up -d auth-service trend-service video-service

# 4. 啟動前端和閘道器
docker-compose -f docker-compose.unified.yml up -d frontend api-gateway
```

### 2. 生產環境部署 (Kubernetes)

#### 前置準備
```bash
# 建立命名空間
kubectl apply -f k8s/unified-deployment.yaml

# 檢查命名空間
kubectl get namespaces
```

#### 部署步驟
```bash
# 1. 部署基礎設施 (資料庫、快取、儲存)
kubectl apply -f k8s/unified-deployment.yaml

# 2. 等待基礎設施準備完成
kubectl wait --for=condition=Ready pod -l app=postgres -n auto-video-generation --timeout=300s
kubectl wait --for=condition=Ready pod -l app=redis -n auto-video-generation --timeout=300s
kubectl wait --for=condition=Ready pod -l app=minio -n auto-video-generation --timeout=300s

# 3. 執行資料庫遷移
kubectl wait --for=condition=Complete job/database-migration -n auto-video-generation --timeout=600s

# 4. 部署應用服務
kubectl rollout status deployment/api-gateway -n auto-video-generation
kubectl rollout status deployment/auth-service -n auto-video-generation
kubectl rollout status deployment/video-service -n auto-video-generation

# 5. 檢查服務狀態
kubectl get pods -n auto-video-generation
kubectl get services -n auto-video-generation
```

## 🔧 配置管理

### Docker Compose 配置說明

本專案提供多個 Docker Compose 配置檔案，用途如下：

- **`docker-compose.unified.yml`** - **主要配置** (Phase 3 統一部署)
  - 整合所有微服務的完整部署配置
  - 包含 Phase 2 資料庫系統配置
  - 支援開發、測試、生產三種環境
  - **建議使用此配置進行所有部署**

- **`docker-compose.yml`** - 向下相容配置
  - 保留用於向下相容
  - 不建議新專案使用

### Kubernetes 配置說明

- **`k8s/unified-deployment.yaml`** - **生產環境 K8s 配置**
  - 包含 25 個 Kubernetes 資源定義
  - 整合 Phase 2 資料庫系統
  - 支援自動擴展 (HPA)、網路政策、Ingress
  - **用於 Staging 和 Production 環境**

### 環境變數配置

#### 開發環境 (.env.development)
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug

# 資料庫配置
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=dev_password
DATABASE_URL=postgresql://postgres:dev_password@localhost:5432/auto_video_generation_dev

# API 密鑰 (開發用預設值)
OPENAI_API_KEY=sk-dev-test-key
GOOGLE_AI_API_KEY=dev-google-key
```

#### 生產環境 (Kubernetes Secrets)
```bash
# 建立機密資料
kubectl create secret generic app-secrets \
  --from-literal=POSTGRES_PASSWORD=prod-strong-password \
  --from-literal=JWT_SECRET_KEY=prod-jwt-secret-key \
  --from-literal=OPENAI_API_KEY=sk-prod-... \
  -n auto-video-generation

# 建立 TLS 憑證
kubectl create secret tls app-tls-secret \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key \
  -n auto-video-generation
```

### 配置同步指南

為確保 Docker Compose 和 Kubernetes 配置保持同步，請遵循以下步驟：

#### 1. 環境變數同步
```bash
# 更新 .env.template 後，同步到 Kubernetes ConfigMap
# 手動檢查 k8s/unified-deployment.yaml 中的 ConfigMap 部分
# 確保環境變數名稱和預設值一致
```

#### 2. 服務版本同步
```bash
# 更新 Docker Compose 中的映像版本後
# 同步更新 Kubernetes Deployment 中的映像標籤
# 使用統一的映像版本管理策略
```

#### 3. 使用腳本驗證同步
```bash
# 執行配置驗證腳本
python scripts/validate-alembic.py

# 執行 Phase 3 驗證
python scripts/test-phase3-deployment.py
```

### 資料庫配置 (Phase 2 統一系統)

#### Alembic 遷移執行
```bash
# 開發環境
alembic upgrade head

# 容器環境 (使用統一配置)
docker-compose -f docker-compose.unified.yml exec api-gateway alembic upgrade head

# Kubernetes 環境
kubectl exec -it deployment/api-gateway -n auto-video-generation -- alembic upgrade head
```

#### 資料庫健康檢查
```bash
# 使用 Phase 2 的同步管理器
python -m auto_generate_video_fold6.database.sync_manager

# 或使用管理腳本
python scripts/db-migration-manager.py health-check
```

## 📊 監控與日誌

### Prometheus 監控
```bash
# 啟動監控服務
docker-compose -f docker-compose.unified.yml --profile monitoring up -d

# 或在 Kubernetes 中
kubectl apply -f k8s/monitoring.yaml
```

### Grafana 儀表板
- **URL**: http://localhost:3001 (開發) / https://grafana.yourdomain.com (生產)
- **預設帳號**: admin / admin123

### 日誌收集
```bash
# 查看服務日誌
docker-compose -f docker-compose.unified.yml logs -f api-gateway

# Kubernetes 日誌
kubectl logs -f deployment/api-gateway -n auto-video-generation
```

## 🔒 安全性配置

### SSL/TLS 設定
```bash
# 生成自簽憑證 (開發用)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/domain.key \
  -out certs/domain.crt

# 生產環境使用 Let's Encrypt
certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com
```

### 網路安全
- **Docker**: 使用自定義網路隔離服務
- **Kubernetes**: 實施 NetworkPolicy 限制流量
- **防火牆**: 只開放必要端口 (80, 443, 22)

## ⚡ 性能優化

### 資源配置
```yaml
# 生產環境資源限制
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### 自動擴展
```yaml
# HPA 配置
minReplicas: 2
maxReplicas: 10
targetCPUUtilizationPercentage: 70
```

### 快取策略
- **Redis**: 分散式快取，每個服務使用不同 DB
- **CDN**: 靜態資源使用 CloudFront/CloudFlare
- **資料庫**: 讀寫分離、連接池優化

## 🚨 災難復原

### 備份策略
```bash
# 資料庫備份
docker-compose -f docker-compose.unified.yml exec postgres pg_dump -U postgres auto_video_generation > backup.sql

# MinIO 資料備份
docker-compose -f docker-compose.unified.yml exec minio mc mirror /data s3://backup-bucket
```

### 復原程序
```bash
# 資料庫復原
docker-compose -f docker-compose.unified.yml exec postgres psql -U postgres auto_video_generation < backup.sql

# 應用程式復原
kubectl rollout undo deployment/api-gateway -n auto-video-generation
```

## 📈 擴展策略

### 水平擴展
```bash
# Docker Compose 擴展
docker-compose -f docker-compose.unified.yml up -d --scale api-gateway=3 --scale video-service=2

# Kubernetes 擴展
kubectl scale deployment api-gateway --replicas=5 -n auto-video-generation
```

### 垂直擴展
```bash
# 增加資源限制
kubectl patch deployment api-gateway -n auto-video-generation -p '{"spec":{"template":{"spec":{"containers":[{"name":"api-gateway","resources":{"limits":{"memory":"2Gi","cpu":"2000m"}}}]}}}}'
```

## 🔍 故障排除

### 常見問題

#### 1. 資料庫連接失敗
```bash
# 檢查資料庫狀態
docker-compose -f docker-compose.unified.yml logs postgres

# 測試連接
docker-compose -f docker-compose.unified.yml exec postgres pg_isready -U postgres
```

#### 2. 服務啟動失敗
```bash
# 檢查服務日誌
kubectl describe pod <pod-name> -n auto-video-generation
kubectl logs <pod-name> -n auto-video-generation
```

#### 3. 記憶體不足
```bash
# 檢查資源使用
kubectl top nodes
kubectl top pods -n auto-video-generation
```

### 健康檢查端點
- **API Gateway**: `GET /health`
- **Auth Service**: `GET /health`
- **Video Service**: `GET /health`
- **Database**: `pg_isready` 命令

## 📝 部署檢查清單

### 部署前檢查
- [ ] 環境變數配置完成
- [ ] 資料庫連接字串正確
- [ ] API 密鑰已設定
- [ ] SSL 憑證已準備
- [ ] 域名 DNS 已設定

### 部署後驗證
- [ ] 所有服務健康檢查通過
- [ ] 資料庫遷移執行成功
- [ ] API 端點回應正常
- [ ] 前端應用載入正常
- [ ] 監控系統運作正常

### 生產環境特殊注意事項
- [ ] 備份策略已實施
- [ ] 日誌輪轉已設定
- [ ] 資源監控已啟用
- [ ] 安全掃描已完成
- [ ] 負載測試已執行

## 🎯 下一步

完成 Phase 3 部署後，建議考慮：

1. **Phase 4**: 實施 CI/CD 流水線
2. **Phase 5**: 建立監控告警系統
3. **Phase 6**: 優化性能與成本控制

---

> 📚 更多詳細資訊請參考：
> - [系統架構文檔](./ARCHITECTURE.md)
> - [開發者指南](./DEVELOPER_GUIDE.md)
> - [安全配置指南](./SECURITY.md)