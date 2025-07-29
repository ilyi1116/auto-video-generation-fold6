# 🚀 Auto Video 部署指南

## 📖 部署概覽

本指南將詳細說明如何在不同環境中部署 Auto Video 系統，包括開發、測試、預生產和生產環境的完整部署流程。

## 🎯 部署架構圖

```mermaid
graph TB
    subgraph "Load Balancer Layer"
        LB[Nginx Load Balancer]
    end
    
    subgraph "Application Layer"
        GW[API Gateway]
        FE[Frontend]
        
        subgraph "Microservices"
            AUTH[Auth Service]
            VIDEO[Video Service]
            AI[AI Service]
            SOCIAL[Social Service]
            ANALYTICS[Analytics Service]
        end
    end
    
    subgraph "Data Layer"
        PG[PostgreSQL]
        REDIS[Redis]
        S3[Object Storage]
    end
    
    subgraph "Monitoring Layer"
        PROM[Prometheus]
        GRAF[Grafana]
        ALERT[Alertmanager]
    end
    
    LB --> GW
    LB --> FE
    GW --> AUTH
    GW --> VIDEO
    GW --> AI
    GW --> SOCIAL
    GW --> ANALYTICS
    
    AUTH --> PG
    AUTH --> REDIS
    VIDEO --> PG
    VIDEO --> S3
    AI --> S3
    
    PROM --> AUTH
    PROM --> VIDEO
    PROM --> AI
    GRAF --> PROM
    ALERT --> PROM
```

## 🛠️ 環境準備

### 系統要求

#### 最低配置
- **CPU**: 4 核心
- **記憶體**: 16GB RAM
- **儲存**: 100GB SSD
- **網路**: 100Mbps

#### 推薦配置（生產環境）
- **CPU**: 8+ 核心
- **記憶體**: 32GB+ RAM
- **儲存**: 500GB+ NVMe SSD
- **網路**: 1Gbps+

#### 軟體要求
- Docker 24.0+
- Docker Compose 2.20+
- Linux 系統 (Ubuntu 22.04 LTS 推薦)
- Git 2.30+

### 網路端口配置

| 服務 | 端口 | 協議 | 說明 |
|------|------|------|------|
| Nginx | 80, 443 | HTTP/HTTPS | 負載均衡器 |
| API Gateway | 8000 | HTTP | 主要 API 入口 |
| Frontend | 3000 | HTTP | Web 應用 |
| Auth Service | 8001 | HTTP | 認證服務 |
| Video Service | 8004 | HTTP | 影片處理 |
| AI Service | 8005 | HTTP | AI 服務 |
| PostgreSQL | 5432 | TCP | 主資料庫 |
| Redis | 6379 | TCP | 快取和會話 |
| Prometheus | 9090 | HTTP | 監控指標 |
| Grafana | 3001 | HTTP | 監控儀表板 |

## 🏗️ 部署方式

### 方式一：Docker Compose（推薦用於開發和小規模部署）

#### 1. 準備部署環境

```bash
# 創建部署目錄
mkdir -p /opt/autovideo
cd /opt/autovideo

# 克隆專案
git clone https://github.com/your-org/auto-video.git .

# 創建必要的目錄
mkdir -p {logs,data,ssl,backup}
```

#### 2. 環境變數配置

創建生產環境配置文件：

```bash
# 複製環境變數範本
cp .env.example .env.prod

# 編輯生產環境配置
nano .env.prod
```

**`.env.prod` 配置範例：**

```bash
# 基本配置
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secret-key-32-chars-minimum

# 資料庫配置
DATABASE_URL=postgresql://autovideo:secure_password@postgres:5432/autovideo_prod
REDIS_URL=redis://redis:6379/0

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret-key-must-be-32-chars-or-longer
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# AI 服務 API 金鑰
OPENAI_API_KEY=sk-your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key
STABILITY_API_KEY=your-stability-ai-key

# 社群媒體 API
YOUTUBE_CLIENT_ID=your-youtube-client-id
YOUTUBE_CLIENT_SECRET=your-youtube-client-secret
TIKTOK_CLIENT_ID=your-tiktok-client-id
TIKTOK_CLIENT_SECRET=your-tiktok-client-secret

# 檔案儲存
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=ap-southeast-1
S3_BUCKET_NAME=autovideo-prod-storage

# 郵件服務
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# 監控配置
GRAFANA_ADMIN_PASSWORD=secure_grafana_password
PROMETHEUS_RETENTION_TIME=15d

# 域名配置
DOMAIN=yourdomain.com
FRONTEND_URL=https://yourdomain.com
API_URL=https://api.yourdomain.com

# SSL 配置
SSL_EMAIL=admin@yourdomain.com
```

#### 3. SSL 證書設置

**使用 Let's Encrypt（推薦）：**

```bash
# 安裝 Certbot
sudo apt install certbot python3-certbot-nginx

# 生成 SSL 證書
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# 複製證書到專案目錄
sudo cp /etc/letsencrypt/live/yourdomain.com/*.pem ssl/
sudo chown $(whoami):$(whoami) ssl/*.pem
```

**使用自簽名證書（僅測試用）：**

```bash
# 生成自簽名證書
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/private.key \
  -out ssl/certificate.crt \
  -subj "/C=TW/ST=Taiwan/L=Taipei/O=AutoVideo/OU=IT/CN=yourdomain.com"
```

#### 4. 部署執行

```bash
# 設置執行權限
chmod +x scripts/*.sh

# 執行健康檢查
./scripts/pre-deployment-check.sh

# 啟動生產環境
docker-compose -f docker-compose.prod.yml up -d

# 檢查服務狀態
docker-compose -f docker-compose.prod.yml ps

# 查看日誌
docker-compose -f docker-compose.prod.yml logs -f
```

#### 5. 資料庫初始化

```bash
# 等待資料庫啟動
sleep 30

# 執行資料庫遷移
docker-compose -f docker-compose.prod.yml exec api-gateway alembic upgrade head

# 創建管理員帳戶
docker-compose -f docker-compose.prod.yml exec api-gateway python scripts/create-admin.py \
  --email admin@yourdomain.com \
  --password SecureAdminPassword123!

# 載入初始數據
docker-compose -f docker-compose.prod.yml exec api-gateway python scripts/load-initial-data.py
```

### 方式二：Kubernetes 部署（推薦用於大規模生產環境）

#### 1. 準備 Kubernetes 集群

**使用 kubeadm 搭建集群：**

```bash
# 主節點初始化
sudo kubeadm init --pod-network-cidr=10.244.0.0/16

# 配置 kubectl
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# 安裝網路外掛（Flannel）
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml

# 允許主節點運行 Pod（單節點部署）
kubectl taint nodes --all node-role.kubernetes.io/control-plane-
```

**或使用托管 Kubernetes（推薦）：**
- AWS EKS
- Google GKE
- Azure AKS
- DigitalOcean Kubernetes

#### 2. 創建 Kubernetes 配置文件

**命名空間配置 (`k8s/namespace.yaml`)：**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: autovideo
  labels:
    name: autovideo
    environment: production
```

**ConfigMap 配置 (`k8s/configmap.yaml`)：**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: autovideo-config
  namespace: autovideo
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  DATABASE_HOST: "postgresql"
  DATABASE_PORT: "5432"
  DATABASE_NAME: "autovideo_prod"
  REDIS_HOST: "redis"
  REDIS_PORT: "6379"
  JWT_ALGORITHM: "HS256"
  JWT_EXPIRE_MINUTES: "60"
  FRONTEND_URL: "https://yourdomain.com"
  API_URL: "https://api.yourdomain.com"
```

**Secret 配置 (`k8s/secrets.yaml`)：**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: autovideo-secrets
  namespace: autovideo
type: Opaque
data:
  DATABASE_PASSWORD: <base64-encoded-password>
  JWT_SECRET_KEY: <base64-encoded-jwt-secret>
  OPENAI_API_KEY: <base64-encoded-openai-key>
  GEMINI_API_KEY: <base64-encoded-gemini-key>
  AWS_ACCESS_KEY_ID: <base64-encoded-aws-key>
  AWS_SECRET_ACCESS_KEY: <base64-encoded-aws-secret>
```

**PostgreSQL 部署 (`k8s/postgresql.yaml`)：**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
  namespace: autovideo
spec:
  serviceName: postgresql
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          valueFrom:
            configMapKeyRef:
              name: autovideo-config
              key: DATABASE_NAME
        - name: POSTGRES_USER
          value: "autovideo"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: autovideo-secrets
              key: DATABASE_PASSWORD
        volumeMounts:
        - name: postgresql-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
  volumeClaimTemplates:
  - metadata:
      name: postgresql-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "standard"
      resources:
        requests:
          storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgresql
  namespace: autovideo
spec:
  selector:
    app: postgresql
  ports:
  - port: 5432
    targetPort: 5432
  clusterIP: None
```

**API Gateway 部署 (`k8s/api-gateway.yaml`)：**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: autovideo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: autovideo/api-gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://autovideo:$(DATABASE_PASSWORD)@postgresql:5432/autovideo_prod"
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: autovideo-secrets
              key: DATABASE_PASSWORD
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: autovideo-secrets
              key: JWT_SECRET_KEY
        envFrom:
        - configMapRef:
            name: autovideo-config
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
  namespace: autovideo
spec:
  selector:
    app: api-gateway
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

**Ingress 配置 (`k8s/ingress.yaml`)：**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: autovideo-ingress
  namespace: autovideo
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/use-regex: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - yourdomain.com
    - api.yourdomain.com
    secretName: autovideo-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8000
```

#### 3. 部署到 Kubernetes

```bash
# 創建命名空間
kubectl apply -f k8s/namespace.yaml

# 創建 ConfigMap 和 Secrets
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# 部署資料庫
kubectl apply -f k8s/postgresql.yaml
kubectl apply -f k8s/redis.yaml

# 等待資料庫啟動
kubectl wait --for=condition=ready pod -l app=postgresql -n autovideo --timeout=300s

# 部署微服務
kubectl apply -f k8s/api-gateway.yaml
kubectl apply -f k8s/auth-service.yaml
kubectl apply -f k8s/video-service.yaml
kubectl apply -f k8s/ai-service.yaml

# 部署前端
kubectl apply -f k8s/frontend.yaml

# 設置 Ingress
kubectl apply -f k8s/ingress.yaml

# 檢查部署狀態
kubectl get pods -n autovideo
kubectl get services -n autovideo
kubectl get ingress -n autovideo
```

## 🔍 健康檢查與監控

### 應用健康檢查

每個服務都應實現以下健康檢查端點：

```python
# 健康檢查端點實現
from fastapi import FastAPI, HTTPException
import asyncio
import asyncpg
import redis

app = FastAPI()

@app.get("/health")
async def health_check():
    """基本健康檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "api-gateway",
        "version": "1.0.0"
    }

@app.get("/ready")
async def readiness_check():
    """就緒檢查 - 檢查依賴服務"""
    checks = {
        "database": False,
        "redis": False,
        "external_apis": False
    }
    
    try:
        # 檢查資料庫連接
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.fetchval("SELECT 1")
        await conn.close()
        checks["database"] = True
    except Exception:
        pass
    
    try:
        # 檢查 Redis 連接
        r = redis.Redis.from_url(REDIS_URL)
        r.ping()
        checks["redis"] = True
    except Exception:
        pass
    
    try:
        # 檢查外部 API
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.openai.com/v1/models", timeout=5)
            if response.status_code == 200:
                checks["external_apis"] = True
    except Exception:
        pass
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### 監控配置

**Prometheus 配置 (`monitoring/prometheus/prometheus.yml`)：**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'api-gateway'
    static_configs:
      - targets: ['api-gateway:8000']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'auth-service'
    static_configs:
      - targets: ['auth-service:8001']
    metrics_path: /metrics

  - job_name: 'video-service'
    static_configs:
      - targets: ['video-service:8004']
    metrics_path: /metrics

  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

**告警規則 (`monitoring/prometheus/rules/alerts.yml`)：**

```yaml
groups:
  - name: autovideo_alerts
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"
          description: "{{ $labels.instance }} has been down for more than 1 minute."

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second."

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds."

      - alert: DatabaseConnectionFailure
        expr: postgresql_up == 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Database connection failure"
          description: "Cannot connect to PostgreSQL database."

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 90%."

      - alert: DiskSpaceLow
        expr: (node_filesystem_size_bytes{fstype!="tmpfs"} - node_filesystem_free_bytes{fstype!="tmpfs"}) / node_filesystem_size_bytes{fstype!="tmpfs"} > 0.8
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Disk space low"
          description: "Disk usage is above 80%."
```

## 🔄 CI/CD 流程

### GitHub Actions 配置

**主要工作流程 (`.github/workflows/deploy.yml`)：**

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest tests/ --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Run security scan
      uses: github/super-linter@v4
      env:
        DEFAULT_BRANCH: main
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Run Snyk security scan
      uses: snyk/actions/python@master
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [api-gateway, auth-service, video-service, ai-service, frontend]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/${{ matrix.service }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: ./services/${{ matrix.service }}
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Configure kubectl
      uses: azure/k8s-set-context@v3
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG }}
    
    - name: Deploy to Kubernetes
      run: |
        # 更新映像標籤
        sed -i "s/:latest/:${{ github.sha }}/g" k8s/*.yaml
        
        # 應用配置
        kubectl apply -f k8s/
        
        # 等待部署完成
        kubectl rollout status deployment/api-gateway -n autovideo
        kubectl rollout status deployment/auth-service -n autovideo
        kubectl rollout status deployment/video-service -n autovideo
        kubectl rollout status deployment/ai-service -n autovideo
        kubectl rollout status deployment/frontend -n autovideo
    
    - name: Run smoke tests
      run: |
        # 等待服務就緒
        sleep 30
        
        # 執行煙霧測試
        curl -f https://api.yourdomain.com/health || exit 1
        curl -f https://yourdomain.com || exit 1
        
        # 執行 API 測試
        python scripts/smoke-tests.py

  notify:
    needs: [deploy]
    runs-on: ubuntu-latest
    if: always()
    
    steps:
    - name: Notify Slack
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 藍綠部署腳本

```bash
#!/bin/bash
# scripts/blue-green-deploy.sh

set -e

NAMESPACE="autovideo"
NEW_VERSION=$1
CURRENT_VERSION=$(kubectl get deployment api-gateway -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d':' -f2)

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <new-version>"
    exit 1
fi

echo "Starting blue-green deployment..."
echo "Current version: $CURRENT_VERSION"
echo "New version: $NEW_VERSION"

# 1. 部署新版本（綠色環境）
echo "Deploying green environment..."
sed "s/:$CURRENT_VERSION/:$NEW_VERSION/g" k8s/*.yaml | kubectl apply -f -

# 2. 等待新版本就緒
echo "Waiting for green environment to be ready..."
kubectl rollout status deployment/api-gateway -n $NAMESPACE --timeout=600s
kubectl rollout status deployment/auth-service -n $NAMESPACE --timeout=600s
kubectl rollout status deployment/video-service -n $NAMESPACE --timeout=600s

# 3. 執行健康檢查
echo "Running health checks..."
for i in {1..30}; do
    if kubectl exec deployment/api-gateway -n $NAMESPACE -- curl -f http://localhost:8000/health; then
        echo "Health check passed"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "Health check failed, rolling back..."
        kubectl rollout undo deployment/api-gateway -n $NAMESPACE
        kubectl rollout undo deployment/auth-service -n $NAMESPACE
        kubectl rollout undo deployment/video-service -n $NAMESPACE
        exit 1
    fi
    
    echo "Health check attempt $i failed, retrying..."
    sleep 10
done

# 4. 執行煙霧測試
echo "Running smoke tests..."
if ! python scripts/smoke-tests.py; then
    echo "Smoke tests failed, rolling back..."
    kubectl rollout undo deployment/api-gateway -n $NAMESPACE
    exit 1
fi

# 5. 切換流量（更新 Ingress）
echo "Switching traffic to green environment..."
kubectl patch ingress autovideo-ingress -n $NAMESPACE -p '{"metadata":{"labels":{"version":"'$NEW_VERSION'"}}}'

echo "Blue-green deployment completed successfully!"
echo "New version $NEW_VERSION is now live"

# 6. 清理舊版本（可選，建議保留一段時間以便快速回滾）
read -p "Do you want to clean up the blue environment? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleaning up blue environment..."
    # 這裡可以添加清理邏輯
fi
```

## 🔐 安全配置

### SSL/TLS 設置

**Nginx SSL 配置：**

```nginx
# /etc/nginx/sites-available/autovideo
server {
    listen 80;
    server_name yourdomain.com api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支援
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://api-gateway:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' 'https://yourdomain.com' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;
        
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
}
```

### 防火牆設置

```bash
# UFW 防火牆配置
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允許 SSH
sudo ufw allow 22/tcp

# 允許 HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允許監控端口（僅內部）
sudo ufw allow from 10.0.0.0/8 to any port 9090
sudo ufw allow from 10.0.0.0/8 to any port 3001

# 啟用防火牆
sudo ufw --force enable

# 檢查狀態
sudo ufw status
```

## 📊 效能調校

### 資料庫優化

**PostgreSQL 配置 (`postgresql.conf`)：**

```ini
# 記憶體設定
shared_buffers = 4GB                    # 系統記憶體的 25%
effective_cache_size = 12GB             # 系統記憶體的 75%
maintenance_work_mem = 512MB
work_mem = 16MB

# 檢查點設定
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# 連接設定
max_connections = 200
shared_preload_libraries = 'pg_stat_statements'

# 日誌設定
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_min_duration_statement = 1000      # 記錄執行超過 1 秒的查詢
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
```

### Redis 調校

**Redis 配置 (`redis.conf`)：**

```ini
# 記憶體設定
maxmemory 2gb
maxmemory-policy allkeys-lru

# 持久性設定
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes

# 網路設定
tcp-keepalive 300
timeout 0

# 安全設定
requirepass your_redis_password
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG "CONFIG_c0nf1g_ch4ng3_m3"
```

## 🔧 維護與備份

### 自動化備份腳本

```bash
#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_DIR="/opt/autovideo/backup"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# 創建備份目錄
mkdir -p $BACKUP_DIR/{database,files,config}

echo "Starting backup process at $(date)"

# 1. 資料庫備份
echo "Backing up PostgreSQL..."
docker-compose exec -T postgres pg_dump -U autovideo -d autovideo_prod > \
    $BACKUP_DIR/database/postgres_backup_$DATE.sql

# 2. Redis 備份
echo "Backing up Redis..."
docker-compose exec -T redis redis-cli BGSAVE
sleep 5
docker cp $(docker-compose ps -q redis):/data/dump.rdb \
    $BACKUP_DIR/database/redis_backup_$DATE.rdb

# 3. 檔案備份
echo "Backing up uploaded files..."
if [ -d "/opt/autovideo/data/uploads" ]; then
    tar -czf $BACKUP_DIR/files/uploads_backup_$DATE.tar.gz \
        -C /opt/autovideo/data uploads/
fi

# 4. 配置備份
echo "Backing up configuration..."
tar -czf $BACKUP_DIR/config/config_backup_$DATE.tar.gz \
    -C /opt/autovideo \
    .env.prod docker-compose.prod.yml config/ k8s/

# 5. 上傳到雲端存儲（可選）
if [ ! -z "$AWS_BACKUP_BUCKET" ]; then
    echo "Uploading to S3..."
    aws s3 sync $BACKUP_DIR s3://$AWS_BACKUP_BUCKET/autovideo-backup/$DATE/
fi

# 6. 清理舊備份
echo "Cleaning up old backups..."
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

# 7. 驗證備份
echo "Verifying backup integrity..."
if [ -f "$BACKUP_DIR/database/postgres_backup_$DATE.sql" ]; then
    if pg_restore --list $BACKUP_DIR/database/postgres_backup_$DATE.sql > /dev/null 2>&1; then
        echo "PostgreSQL backup verified successfully"
    else
        echo "WARNING: PostgreSQL backup verification failed"
    fi
fi

echo "Backup process completed at $(date)"

# 發送通知
curl -X POST "$SLACK_WEBHOOK_URL" \
    -H 'Content-type: application/json' \
    --data '{"text":"✅ AutoVideo backup completed successfully at '$(date)'"}'
```

### 系統更新腳本

```bash
#!/bin/bash
# scripts/update-system.sh

set -e

echo "Starting system update process..."

# 1. 備份當前狀態
echo "Creating backup before update..."
./scripts/backup.sh

# 2. 拉取最新程式碼
echo "Pulling latest code..."
git pull origin main

# 3. 更新 Docker 映像
echo "Updating Docker images..."
docker-compose -f docker-compose.prod.yml pull

# 4. 執行資料庫遷移
echo "Running database migrations..."
docker-compose -f docker-compose.prod.yml run --rm api-gateway alembic upgrade head

# 5. 重啟服務
echo "Restarting services..."
docker-compose -f docker-compose.prod.yml up -d

# 6. 健康檢查
echo "Performing health checks..."
sleep 30

for service in api-gateway auth-service video-service ai-service frontend; do
    if ! docker-compose -f docker-compose.prod.yml exec $service curl -f http://localhost:8000/health; then
        echo "Health check failed for $service"
        
        # 回滾
        echo "Rolling back..."
        git checkout HEAD~1
        docker-compose -f docker-compose.prod.yml up -d
        exit 1
    fi
done

echo "System update completed successfully!"
```

## 🚨 故障處理

### 常見問題排解

#### 1. 服務無法啟動

```bash
# 檢查服務狀態
docker-compose -f docker-compose.prod.yml ps

# 查看服務日誌
docker-compose -f docker-compose.prod.yml logs service-name

# 檢查資源使用
docker stats

# 檢查磁碟空間
df -h

# 檢查記憶體使用
free -h
```

#### 2. 資料庫連接問題

```bash
# 檢查 PostgreSQL 狀態
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U autovideo

# 檢查連接數
docker-compose -f docker-compose.prod.yml exec postgres psql -U autovideo -d autovideo_prod -c "SELECT count(*) FROM pg_stat_activity;"

# 檢查資料庫大小
docker-compose -f docker-compose.prod.yml exec postgres psql -U autovideo -d autovideo_prod -c "SELECT pg_size_pretty(pg_database_size('autovideo_prod'));"
```

#### 3. 效能問題診斷

```bash
# 檢查系統負載
htop

# 檢查 I/O 使用
iotop

# 檢查網路連接
netstat -tulpn

# 檢查應用日誌中的慢查詢
grep "slow query" /opt/autovideo/logs/*.log
```

### 災難恢復流程

```bash
#!/bin/bash
# scripts/disaster-recovery.sh

BACKUP_DATE=$1
BACKUP_DIR="/opt/autovideo/backup"

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup-date>"
    echo "Available backups:"
    ls -la $BACKUP_DIR/database/postgres_backup_*.sql | head -10
    exit 1
fi

echo "Starting disaster recovery process..."
echo "WARNING: This will overwrite current data!"
read -p "Are you sure you want to continue? (yes/no): " -r

if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "Recovery cancelled"
    exit 1
fi

# 1. 停止所有服務
echo "Stopping services..."
docker-compose -f docker-compose.prod.yml down

# 2. 恢復資料庫
echo "Restoring PostgreSQL database..."
docker-compose -f docker-compose.prod.yml up -d postgres
sleep 30

# 刪除現有資料庫
docker-compose -f docker-compose.prod.yml exec postgres dropdb -U autovideo autovideo_prod
docker-compose -f docker-compose.prod.yml exec postgres createdb -U autovideo autovideo_prod

# 恢復資料
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U autovideo -d autovideo_prod < \
    $BACKUP_DIR/database/postgres_backup_$BACKUP_DATE.sql

# 3. 恢復 Redis
echo "Restoring Redis..."
docker-compose -f docker-compose.prod.yml up -d redis
sleep 10
docker cp $BACKUP_DIR/database/redis_backup_$BACKUP_DATE.rdb \
    $(docker-compose ps -q redis):/data/dump.rdb
docker-compose -f docker-compose.prod.yml restart redis

# 4. 恢復檔案
echo "Restoring files..."
if [ -f "$BACKUP_DIR/files/uploads_backup_$BACKUP_DATE.tar.gz" ]; then
    tar -xzf $BACKUP_DIR/files/uploads_backup_$BACKUP_DATE.tar.gz -C /opt/autovideo/data/
fi

# 5. 啟動所有服務
echo "Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

# 6. 驗證恢復
echo "Verifying recovery..."
sleep 60

if curl -f http://localhost:8000/health; then
    echo "✅ Disaster recovery completed successfully!"
else
    echo "❌ Recovery verification failed"
    exit 1
fi
```

---

## 📞 支援與維護

### 日常維護檢查清單

**每日檢查：**
- [ ] 檢查所有服務健康狀態
- [ ] 查看錯誤日誌
- [ ] 監控資源使用率
- [ ] 驗證備份完成

**每週檢查：**
- [ ] 更新依賴套件
- [ ] 檢查安全漏洞
- [ ] 清理日誌文件
- [ ] 測試災難恢復流程

**每月檢查：**
- [ ] 執行完整系統測試
- [ ] 更新 SSL 證書（如需要）
- [ ] 檢查效能指標趨勢
- [ ] 更新部署文檔

### 聯繫資訊

- **技術支援**: support@autovideo.com
- **緊急聯繫**: +886 2 1234 5678
- **文檔更新**: 請提交 GitHub Issues

---

*本部署指南會持續更新，如有任何問題或建議，歡迎透過 GitHub Issues 回饋。*