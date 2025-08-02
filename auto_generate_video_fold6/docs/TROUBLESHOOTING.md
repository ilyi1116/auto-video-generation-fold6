# 故障排除指南

## 概述

本指南提供 Auto Video Generation System 常見問題的解決方案。

## 常見問題

### 1. 服務無法啟動

#### 症狀
- 服務啟動失敗
- 端口被佔用
- 依賴服務未啟動

#### 解決方案
```bash
# 檢查服務狀態
docker-compose ps

# 查看詳細日誌
docker-compose logs service-name

# 檢查端口佔用
netstat -tulpn | grep :8000

# 重啟服務
docker-compose restart service-name
```

### 2. 數據庫連接失敗

#### 症狀
- 數據庫連接錯誤
- 認證失敗
- 連接超時

#### 解決方案
```bash
# 檢查數據庫狀態
docker-compose ps postgres

# 測試連接
docker-compose exec postgres psql -U user -d video_system -c "SELECT 1;"

# 檢查配置
python scripts/config/validate.py

# 重新初始化數據庫
docker-compose down
docker volume rm postgres_data
docker-compose up -d postgres
```

### 3. Redis 連接問題

#### 症狀
- Redis 連接失敗
- 緩存不工作
- 會話丟失

#### 解決方案
```bash
# 檢查 Redis 狀態
docker-compose ps redis

# 測試 Redis 連接
docker-compose exec redis redis-cli ping

# 檢查 Redis 配置
docker-compose exec redis redis-cli CONFIG GET maxmemory
```

### 4. API 響應緩慢

#### 症狀
- API 響應時間長
- 請求超時
- 系統負載高

#### 解決方案
```bash
# 檢查系統資源
htop
free -h
df -h

# 檢查服務性能
docker stats

# 優化配置
# 增加記憶體限制
# 啟用緩存
# 優化數據庫查詢
```

### 5. 認證問題

#### 症狀
- JWT 令牌無效
- 登入失敗
- 權限錯誤

#### 解決方案
```bash
# 檢查 JWT 配置
echo $JWT_SECRET_KEY

# 重新生成 JWT 密鑰
openssl rand -hex 32

# 清除過期令牌
docker-compose exec redis redis-cli FLUSHDB
```

## 日誌分析

### 查看日誌
```bash
# 實時日誌
docker-compose logs -f

# 特定服務日誌
docker-compose logs -f api-gateway

# 錯誤日誌
docker-compose logs | grep ERROR

# 日誌文件
tail -f logs/app.log
```

### 日誌級別
```python
# 設置日誌級別
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 性能診斷

### 系統監控
```bash
# CPU 使用率
top -p $(pgrep -f uvicorn)

# 記憶體使用
free -h

# 磁碟 I/O
iostat -x 1

# 網路連接
netstat -tulpn
```

### 應用性能
```bash
# 響應時間測試
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/health"

# 壓力測試
ab -n 1000 -c 10 http://localhost:8000/health

# 性能分析
python -m cProfile -o profile.stats app.py
```

## 數據庫問題

### PostgreSQL 問題
```bash
# 檢查連接數
docker-compose exec postgres psql -U user -d video_system -c "SELECT count(*) FROM pg_stat_activity;"

# 檢查慢查詢
docker-compose exec postgres psql -U user -d video_system -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# 重建索引
docker-compose exec postgres psql -U user -d video_system -c "REINDEX DATABASE video_system;"
```

### Redis 問題
```bash
# 檢查記憶體使用
docker-compose exec redis redis-cli INFO memory

# 清理過期鍵
docker-compose exec redis redis-cli FLUSHDB

# 檢查連接數
docker-compose exec redis redis-cli INFO clients
```

## 網路問題

### 端口衝突
```bash
# 檢查端口使用
lsof -i :8000

# 殺死佔用進程
sudo kill -9 $(lsof -t -i:8000)

# 更改端口
# 修改 docker-compose.yml 中的端口映射
```

### DNS 解析
```bash
# 測試 DNS 解析
nslookup api.video-system.com

# 檢查 hosts 文件
cat /etc/hosts

# 清除 DNS 緩存
sudo systemctl restart systemd-resolved
```

## 安全問題

### SSL 證書問題
```bash
# 檢查證書有效性
openssl x509 -in ssl/certificate.crt -text -noout

# 重新生成證書
./scripts/ssl/generate-certs.sh

# 檢查 SSL 配置
openssl s_client -connect localhost:443 -servername localhost
```

### 防火牆問題
```bash
# 檢查防火牆狀態
sudo ufw status

# 開放端口
sudo ufw allow 8000

# 檢查 iptables
sudo iptables -L
```

## 部署問題

### Docker 問題
```bash
# 清理 Docker 資源
docker system prune -a

# 重建映像
docker-compose build --no-cache

# 檢查 Docker 日誌
docker logs container-name
```

### Kubernetes 問題
```bash
# 檢查 Pod 狀態
kubectl get pods -n video-system

# 查看 Pod 日誌
kubectl logs pod-name -n video-system

# 檢查服務狀態
kubectl get services -n video-system

# 重新部署
kubectl rollout restart deployment/api-gateway -n video-system
```

## 開發環境問題

### 依賴問題
```bash
# 重新安裝依賴
pip install -r requirements.txt --force-reinstall

# 清理 Python 緩存
find . -type d -name "__pycache__" -exec rm -rf {} +

# 更新 pip
pip install --upgrade pip
```

### 虛擬環境問題
```bash
# 重新創建虛擬環境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 監控和告警

### 設置監控
```bash
# 啟動監控服務
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# 檢查監控狀態
curl http://localhost:9090/-/healthy
curl http://localhost:3001/api/health
```

### 告警配置
```bash
# 檢查告警規則
cat monitoring/alert_rules.yml

# 測試告警
curl -X POST http://localhost:9093/api/v1/alerts
```

## 備份和恢復

### 數據備份
```bash
# 創建備份
./scripts/backup/create-backup.sh

# 檢查備份完整性
./scripts/backup/verify-backup.sh backup-file.sql
```

### 系統恢復
```bash
# 從備份恢復
./scripts/backup/restore-backup.sh backup-file.sql

# 檢查恢復狀態
curl http://localhost:8000/health
```

## 聯繫支援

### 收集診斷信息
```bash
# 系統信息
uname -a
docker version
docker-compose version

# 服務狀態
docker-compose ps
docker-compose logs

# 配置信息
cat .env
cat docker-compose.yml
```

### 提交問題報告
1. 收集錯誤日誌
2. 記錄重現步驟
3. 提供系統環境信息
4. 提交到 GitHub Issues

## 預防措施

### 定期維護
```bash
# 每日檢查
./scripts/helpers/checks.sh

# 每週清理
docker system prune -f
find logs/ -name "*.log" -mtime +7 -delete

# 每月備份
./scripts/backup/scheduled-backup.sh
```

### 性能優化
```bash
# 監控性能指標
./scripts/monitoring/performance-check.sh

# 優化配置
./scripts/optimization/tune-system.sh
```

## 文檔連結

- [開發者指南](DEVELOPER_GUIDE.md)
- [架構文檔](ARCHITECTURE.md)
- [API 參考](API_REFERENCE.md)
- [部署指南](DEPLOYMENT.md)