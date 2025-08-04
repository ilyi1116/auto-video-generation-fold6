# Auto Video 系統部署指南

## 🎯 系統概述

Auto Video 是一個企業級的 AI 驅動自動影片生成平台，具備完整的微服務架構、監控系統、安全機制和備份恢復功能。

### 系統架構
- **前端**: SvelteKit + Tailwind CSS + TypeScript
- **後端**: FastAPI (Python) 微服務架構
- **資料庫**: PostgreSQL + Redis
- **文件儲存**: AWS S3 相容
- **監控**: Prometheus + Grafana + Jaeger
- **部署**: Docker + Kubernetes
- **CI/CD**: GitHub Actions

## 📋 系統需求

### 硬體需求
- **最低配置**:
  - CPU: 4 核心
  - 記憶體: 8GB RAM
  - 儲存: 100GB SSD
  - 網路: 100Mbps

- **建議配置**:
  - CPU: 8 核心 (含 GPU 支援)
  - 記憶體: 16GB RAM
  - 儲存: 500GB SSD
  - 網路: 1Gbps

### 軟體需求
- Docker 20.10+
- Docker Compose 2.0+
- Kubernetes 1.24+ (生產環境)
- Node.js 18+ (開發環境)
- Python 3.11+ (開發環境)

## 🚀 快速開始

### 1. 開發環境部署

```bash
# 1. 克隆專案
git clone <repository-url>
cd auto_generate_video_fold6

# 2. 複製環境配置
cp .env.example .env.development
cp .env.example .env.production

# 3. 編輯環境變數
nano .env.development

# 4. 啟動開發環境
docker-compose -f docker-compose.yml up -d

# 5. 初始化資料庫
docker-compose exec auth-service alembic upgrade head
docker-compose exec data-service alembic upgrade head

# 6. 啟動前端開發服務器
cd frontend
npm install
npm run dev
```

### 2. 生產環境部署

#### 使用 Docker Compose

```bash
# 1. 設定環境變數
cp .env.example .env.production
# 編輯生產環境配置

# 2. 生成 SSL 憑證
sudo scripts/ssl/setup_ssl.sh your-domain.com admin@your-domain.com

# 3. 啟動生產環境
docker-compose -f docker-compose.prod.yml up -d

# 4. 驗證部署
curl -k https://your-domain.com/health
```

#### 使用 Kubernetes

```bash
# 1. 設定命名空間
kubectl create namespace auto-video

# 2. 創建配置映射
kubectl create configmap auto-video-config \
  --from-env-file=.env.production \
  -n auto-video

# 3. 應用 Kubernetes 配置
kubectl apply -f k8s/ -n auto-video

# 4. 檢查部署狀態
kubectl get pods -n auto-video
kubectl get services -n auto-video
```

## 🔧 配置說明

### 環境變數配置

#### 核心配置
```bash
# 應用基本設定
APP_NAME=auto-video-system
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false

# 資料庫設定
DATABASE_URL=postgresql://username:password@localhost:5432/autovideo
REDIS_URL=redis://localhost:6379/0

# S3 儲存設定
S3_BUCKET=auto-video-files
S3_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# JWT 設定
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# API 設定
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["https://your-domain.com"]
```

#### 監控設定
```bash
# Prometheus
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=your-grafana-password

# Jaeger 追蹤
JAEGER_ENDPOINT=http://jaeger:14268/api/traces

# 告警設定
ALERT_EMAIL=admin@your-domain.com
SLACK_WEBHOOK_URL=your-slack-webhook-url
```

### 服務端口分配

| 服務 | 端口 | 說明 |
|------|------|------|
| Frontend | 3000 | SvelteKit 前端 |
| API Gateway | 8080 | API 閘道器 |
| Auth Service | 8001 | 身份驗證服務 |
| Data Service | 8002 | 資料管理服務 |
| AI Service | 8003 | AI 處理服務 |
| Video Service | 8004 | 影片處理服務 |
| Training Worker | 8005 | 模型訓練工作者 |
| PostgreSQL | 5432 | 主資料庫 |
| Redis | 6379 | 快取資料庫 |
| Prometheus | 9090 | 監控指標 |
| Grafana | 3000 | 監控儀表板 |

## 🔐 安全配置

### SSL/TLS 設定

```bash
# 自動化 SSL 憑證設定
sudo scripts/ssl/setup_ssl.sh your-domain.com admin@your-domain.com

# 手動 Let's Encrypt 設定
certbot certonly --standalone \
  -d your-domain.com \
  -d www.your-domain.com \
  -d api.your-domain.com
```

### 防火牆設定

```bash
# 開放必要端口
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 22/tcp    # SSH

# 限制內部服務端口
sudo ufw deny 5432/tcp   # PostgreSQL
sudo ufw deny 6379/tcp   # Redis
sudo ufw enable
```

### 資料庫安全

```sql
-- 創建應用用戶
CREATE USER autovideo WITH PASSWORD 'strong-password';
CREATE DATABASE autovideo OWNER autovideo;

-- 設定權限
GRANT CONNECT ON DATABASE autovideo TO autovideo;
GRANT USAGE ON SCHEMA public TO autovideo;
GRANT CREATE ON SCHEMA public TO autovideo;
```

## 📊 監控與維護

### 監控系統存取

- **Grafana**: https://your-domain.com:3000
  - 用戶名: admin
  - 密碼: 環境變數中設定的密碼

- **Prometheus**: https://your-domain.com:9090
- **Jaeger**: https://your-domain.com:16686

### 健康檢查端點

```bash
# 系統整體健康檢查
curl https://your-domain.com/health

# 個別服務健康檢查
curl https://your-domain.com/api/auth/health
curl https://your-domain.com/api/data/health
curl https://your-domain.com/api/ai/health
curl https://your-domain.com/api/video/health
```

### 日誌管理

```bash
# 查看服務日誌
docker-compose logs -f api-gateway
docker-compose logs -f auth-service

# Kubernetes 日誌
kubectl logs -f deployment/api-gateway -n auto-video
kubectl logs -f deployment/auth-service -n auto-video
```

## 🔄 備份與恢復

### 自動備份設定

```bash
# 啟動備份系統
python3 scripts/backup/backup_system.py

# 設定 cron 任務
crontab -e
# 添加：0 2 * * * /usr/bin/python3 /path/to/backup_system.py
```

### 手動備份

```bash
# 資料庫備份
pg_dump -h localhost -U autovideo -d autovideo > backup_$(date +%Y%m%d).sql

# 文件備份
tar -czf files_backup_$(date +%Y%m%d).tar.gz /var/data/auto-video/

# 配置備份
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
  docker-compose.yml \
  .env.production \
  nginx/ \
  k8s/
```

### 災難恢復

```bash
# 1. 恢復資料庫
psql -h localhost -U autovideo -d autovideo < backup_20250127.sql

# 2. 恢復文件
tar -xzf files_backup_20250127.tar.gz -C /

# 3. 重啟服務
docker-compose restart
# 或
kubectl rollout restart deployment/auth-service -n auto-video
```

## 🧪 測試與驗證

### 運行測試套件

```bash
# 前端測試
cd frontend
npm run test
npm run test:e2e

# 後端測試
./scripts/run-tests.sh --all
./scripts/run-tests.sh --backend
./scripts/run-tests.sh --frontend

# 個別服務測試
cd services/auth-service
pytest tests/
```

### 效能測試

```bash
# API 負載測試
ab -n 1000 -c 10 https://your-domain.com/api/health

# 前端效能測試
npm run lighthouse
```

## 🔧 故障排除

### 常見問題

#### 1. 服務無法啟動
```bash
# 檢查端口佔用
netstat -tulpn | grep :8080

# 檢查 Docker 資源
docker system df
docker system prune

# 檢查日誌
docker-compose logs service-name
```

#### 2. 資料庫連接失敗
```bash
# 檢查資料庫狀態
docker-compose exec postgres pg_isready

# 檢查連接配置
echo $DATABASE_URL

# 重設資料庫密碼
docker-compose exec postgres psql -U postgres -c "ALTER USER autovideo PASSWORD 'new-password';"
```

#### 3. SSL 憑證問題
```bash
# 檢查憑證有效性
openssl x509 -in /etc/letsencrypt/live/your-domain.com/cert.pem -text -noout

# 強制更新憑證
certbot renew --force-renewal

# 檢查 Nginx 配置
nginx -t
```

### 效能優化

#### 1. 資料庫優化
```sql
-- 分析查詢效能
EXPLAIN ANALYZE SELECT * FROM projects WHERE user_id = 1;

-- 創建索引
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_videos_created_at ON videos(created_at);
```

#### 2. Redis 快取優化
```bash
# 檢查 Redis 記憶體使用
redis-cli info memory

# 設定快取策略
redis-cli config set maxmemory-policy allkeys-lru
```

#### 3. Docker 容器優化
```yaml
# docker-compose.yml 資源限制
services:
  api-gateway:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## 📈 擴展與升級

### 水平擴展

```bash
# Docker Compose 擴展服務實例
docker-compose up -d --scale api-gateway=3 --scale auth-service=2

# Kubernetes 水平自動擴展
kubectl autoscale deployment api-gateway --min=2 --max=10 --cpu-percent=70 -n auto-video
```

### 垂直擴展

```yaml
# 增加容器資源
services:
  ai-service:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### 滾動更新

```bash
# Docker Compose 滾動更新
docker-compose pull
docker-compose up -d --no-deps --build service-name

# Kubernetes 滾動更新
kubectl set image deployment/api-gateway api-gateway=auto-video/api-gateway:v1.1.0 -n auto-video
kubectl rollout status deployment/api-gateway -n auto-video
```

## 📞 支援與聯絡

### 技術支援
- Email: tech-support@auto-video-system.com
- GitHub Issues: <repository-url>/issues
- 文檔: <documentation-url>

### 緊急聯絡
- 系統管理員: admin@auto-video-system.com
- 運維團隊: ops@auto-video-system.com
- 24/7 支援熱線: +1-xxx-xxx-xxxx

---

## 📝 更新日誌

### v1.0.0 (2025-01-27)
- ✅ 完整的微服務架構實現
- ✅ AI 影片生成功能
- ✅ 用戶認證與授權
- ✅ 監控與告警系統
- ✅ 備份與災難恢復
- ✅ 安全加固與 SSL/TLS
- ✅ CI/CD 流程

### 已知問題
- 前端 TypeScript 類型定義需要完善
- 部分 A11y 警告需要修復
- 效能優化待進一步調整

### 未來規劃
- 多語言支援
- 更多 AI 模型整合
- 移動端應用
- 企業級單點登入 (SSO)

---

**部署成功！** 🎉

您的 Auto Video 系統現在已經準備好為用戶提供 AI 驅動的影片生成服務。記得定期檢查監控指標、更新系統和進行備份測試。