# 部署指南

## 概述

本指南涵蓋 Auto Video Generation System 在不同環境中的部署方法。

## 環境要求

### 系統要求
- **CPU**: 至少 4 核心
- **記憶體**: 至少 8GB RAM
- **儲存**: 至少 50GB 可用空間
- **網路**: 穩定的網路連接

### 軟體要求
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.11+
- **Node.js**: 18+ (前端開發)

## 部署方法

### 1. 開發環境部署

```bash
# 快速啟動開發環境
./scripts/deploy/dev.sh

# 或手動設置
cd backend
pip install -r requirements.txt
python scripts/config/setup.py
uvicorn api_gateway.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Docker 部署

```bash
# 使用 Docker Compose 部署
./scripts/deploy/docker.sh

# 或手動部署
docker-compose up -d
```

### 3. Kubernetes 部署

```bash
# 部署到 Kubernetes
./scripts/deploy/k8s.sh

# 或手動部署
kubectl create namespace video-system
kubectl apply -f k8s/
```

## 環境配置

### 開發環境
```bash
# 複製開發環境配置
cp env.development .env.development

# 編輯配置
nano .env.development
```

### 生產環境
```bash
# 複製生產環境配置
cp env.production .env.production

# 編輯配置
nano .env.production
```

## 服務配置

### 數據庫設置
```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/video_system

# SQLite (開發)
DATABASE_URL=sqlite:///./app.db
```

### Redis 設置
```bash
# Redis 連接
REDIS_URL=redis://localhost:6379/0
```

### JWT 設置
```bash
# 生成安全密鑰
openssl rand -hex 32
JWT_SECRET_KEY=your-generated-secret-key
```

## 監控與日誌

### 健康檢查
```bash
# API 健康檢查
curl http://localhost:8000/health

# 服務狀態檢查
./scripts/helpers/checks.sh
```

### 日誌查看
```bash
# Docker 日誌
docker-compose logs -f

# Kubernetes 日誌
kubectl logs -f deployment/api-gateway
```

## 故障排除

### 常見問題

1. **服務無法啟動**
   ```bash
   # 檢查依賴
   ./scripts/helpers/checks.sh
   
   # 檢查端口
   netstat -tulpn | grep :8000
   ```

2. **數據庫連接失敗**
   ```bash
   # 檢查數據庫狀態
   docker-compose ps postgres
   
   # 檢查連接
   python scripts/config/validate.py
   ```

3. **記憶體不足**
   ```bash
   # 檢查系統資源
   free -h
   docker stats
   ```

### 性能優化

1. **調整 Docker 資源限制**
   ```yaml
   # docker-compose.yml
   services:
     api-gateway:
       deploy:
         resources:
           limits:
             memory: 1G
             cpus: '1.0'
   ```

2. **啟用緩存**
   ```bash
   # Redis 緩存
   REDIS_URL=redis://redis:6379/0
   ```

3. **數據庫優化**
   ```sql
   -- PostgreSQL 優化
   ALTER SYSTEM SET shared_buffers = '256MB';
   ALTER SYSTEM SET effective_cache_size = '1GB';
   ```

## 備份與恢復

### 數據備份
```bash
# 數據庫備份
docker-compose exec postgres pg_dump -U user video_system > backup.sql

# 文件備份
tar -czf backup-$(date +%Y%m%d).tar.gz data/
```

### 恢復數據
```bash
# 恢復數據庫
docker-compose exec -T postgres psql -U user video_system < backup.sql

# 恢復文件
tar -xzf backup-20240101.tar.gz
```

## 安全配置

### SSL/TLS 設置
```bash
# 生成 SSL 證書
./scripts/ssl/generate-certs.sh

# 配置 Nginx
cp nginx/nginx.conf /etc/nginx/
```

### 防火牆設置
```bash
# 開放必要端口
sudo ufw allow 8000
sudo ufw allow 443
sudo ufw enable
```

## 擴展部署

### 水平擴展
```bash
# Docker Swarm
docker stack deploy -c docker-compose.yml video-system

# Kubernetes HPA
kubectl apply -f k8s/hpa.yaml
```

### 負載均衡
```bash
# Nginx 負載均衡
cp nginx/load-balancer.conf /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/load-balancer.conf /etc/nginx/sites-enabled/
```

## 更新部署

### 滾動更新
```bash
# Docker Compose
docker-compose pull
docker-compose up -d --no-deps

# Kubernetes
kubectl set image deployment/api-gateway api-gateway=new-image:tag
```

### 藍綠部署
```bash
# 創建新版本
kubectl apply -f k8s/deployment-v2.yaml

# 切換流量
kubectl patch service api-gateway-service -p '{"spec":{"selector":{"version":"v2"}}}'
```

## 監控設置

### Prometheus + Grafana
```bash
# 啟動監控
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```

### 告警設置
```bash
# 配置告警規則
cp monitoring/alert_rules.yml /etc/prometheus/
```

## 文檔連結

- [開發者指南](DEVELOPER_GUIDE.md)
- [架構文檔](ARCHITECTURE.md)
- [API 參考](API_REFERENCE.md)
- [故障排除](TROUBLESHOOTING.md)