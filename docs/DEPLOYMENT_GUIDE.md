# 部署指南

## 環境準備

### 先決條件
- Kubernetes 集群 (1.22+)
- Docker (20.10+)
- Helm (3.8+)
- kubectl
- 最低 16GB RAM, 8 CPU

## 部署架構

### 基礎架構
- Kubernetes 叢集
- 微服務容器化
- 服務網格 (Istio)
- 監控與日誌系統

## 部署步驟

### 1. 容器建置
```bash
# 建置所有服務鏡像
make build-images

# 推送到私有倉庫
make push-images
```

### 2. Kubernetes 部署
```bash
# 部署核心基礎設施
kubectl apply -f infra/kubernetes/base/

# 部署微服務
kubectl apply -f infra/kubernetes/services/

# 部署監控與日誌
kubectl apply -f infra/kubernetes/monitoring/
```

### 3. Helm 部署
```bash
# 使用 Helm 安裝服務
helm install voice-cloning-system ./helm/
```

## 環境配置

### 配置管理
- 使用 Kubernetes ConfigMaps
- 敏感資訊使用 Secrets
- 環境特定配置

### 範例配置
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: voice-service-config
data:
  DATABASE_URL: postgresql://...
  REDIS_HOST: redis-service
```

## 服務發現與負載平衡

### 服務網格配置
- Istio 流量管理
- 斷路器
- 重試策略

## 監控與日誌

### 可觀測性工具
- Prometheus 指標收集
- Grafana 儀表板
- ELK 日誌系統
- OpenTelemetry 追蹤

### 日誌收集
```yaml
apiVersion: logging.banzaicloud.io/v1beta1
kind: Flow
metadata:
  name: voice-service-logs
spec:
  match:
    - select:
        labels:
          app: voice-service
  outputs:
    - elasticsearch:
        host: elasticsearch.logging.svc
```

## 持續部署

### CI/CD 流程
- GitHub Actions
- 自動測試
- 鏡像建置
- 安全掃描
- 自動部署

### 部署工作流程範例
```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and Push
        run: |
          make build-images
          make push-images
      - name: Deploy to Kubernetes
        run: kubectl rollout restart deployment voice-service
```

## disaster recovery

### 備份策略
- 資料庫每日備份
- 狀態恢復點
- 多區域部署

### 故障切換
```bash
# 手動切換到備份叢集
kubectl config use-context backup-cluster
```

## 安全考量

### 網路安全
- 網路策略
- 入口控制器
- 最小權限原則

### 安全掃描
```bash
# 容器安全掃描
trivy image voice-service:latest
```

## 效能調優

### 資源管理
```yaml
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2
    memory: 2Gi
```

### 水平自動擴展
```bash
kubectl autoscale deployment voice-service \
  --cpu-percent=70 \
  --min=2 --max=10
```

## 常見問題排除

### 診斷工具
```bash
# 查看服務日誌
kubectl logs -l app=voice-service

# 檢查服務狀態
kubectl describe pod voice-service
```

## 版本管理

### 滾動更新
- 零停機部署
- 漸進式更新
- A/B 測試策略