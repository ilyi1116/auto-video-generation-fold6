# 後台管理系統

一個功能完整的後台管理系統，支援 AI Provider 設定、爬蟲管理、社交媒體熱門關鍵字追蹤和操作日誌記錄。

## 🌟 主要功能

### 🤖 AI Provider 管理
- 支援多種 AI 服務提供商（OpenAI、Anthropic、Google Gemini 等）
- 安全的 API Key 加密存儲
- 連接測試和狀態監控
- 完整的 CRUD 操作

### 🕷️ 爬蟲管理
- 靈活的爬蟲配置（關鍵字、URL、排程）
- 支援 CSS 選擇器的內容提取
- 智能排程系統
- 爬蟲結果存儲和分析

### 📈 社交媒體趨勢追蹤
- 支援 5 大社交平台（TikTok、YouTube、Instagram、Facebook、Twitter）
- 多時間維度分析（1天、1週、1個月、3個月、6個月）
- 自動化數據收集
- 趨勢分析和報告

### 📋 操作日誌系統
- 結構化日誌記錄
- 安全事件追蹤
- 性能監控
- 審計追蹤

### 🔐 安全性功能
- JWT 認證
- 基於角色的權限控制
- IP 白名單
- 速率限制
- 安全響應頭
- 密碼加密

### ⚙️ 排程任務系統
- 基於 Celery 的分散式任務隊列
- 自動化爬蟲執行
- 定時趨勢收集
- 系統維護任務
- 通知和報告

## 🏗️ 系統架構

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端管理介面  │    │   FastAPI 後端  │    │   PostgreSQL    │
│   (SvelteKit)   │◄──►│      API        │◄──►│     資料庫      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Celery Worker  │◄──►│     Redis       │
                       │   (任務執行)    │    │  (訊息代理)    │
                       └─────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌─────────────────┐
                       │  外部 API 服務  │
                       │ (社交媒體平台)  │
                       └─────────────────┘
```

## 🚀 快速開始

### 1. 環境要求
- Docker & Docker Compose
- 8GB+ RAM
- 20GB+ 磁碟空間

### 2. 安裝部署

```bash
# 克隆項目
git clone <repository-url>
cd admin-service

# 配置環境變量
cp .env.example .env
# 編輯 .env 文件，設置資料庫密碼、API 密鑰等

# 啟動系統
./start.sh
```

### 3. 訪問系統

- **API 文檔**: http://localhost:8080/docs
- **管理介面**: http://localhost:8080/admin  
- **Celery 監控**: http://localhost:5555

**預設登錄信息**:
- 用戶名: `admin`
- 密碼: `admin123`

⚠️ **請立即修改預設密碼！**

## 📚 API 文檔

### 認證
所有 API 端點都需要 JWT Bearer 令牌認證：

```bash
# 登錄獲取令牌
curl -X POST "http://localhost:8080/admin/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 使用令牌訪問 API
curl -X GET "http://localhost:8080/admin/ai-providers" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 主要端點

#### AI Provider 管理
- `GET /admin/ai-providers` - 獲取 AI Provider 列表
- `POST /admin/ai-providers` - 創建 AI Provider
- `PUT /admin/ai-providers/{id}` - 更新 AI Provider
- `DELETE /admin/ai-providers/{id}` - 刪除 AI Provider
- `POST /admin/ai-providers/{id}/test` - 測試連接

#### 爬蟲管理
- `GET /admin/crawler-configs` - 獲取爬蟲配置列表
- `POST /admin/crawler-configs` - 創建爬蟲配置
- `POST /admin/crawler-configs/{id}/run` - 手動運行爬蟲
- `GET /admin/crawler-configs/{id}/results` - 獲取爬蟲結果

#### 社交媒體趨勢
- `GET /admin/trending-keywords` - 獲取熱門關鍵字
- `GET /admin/trending-keywords/top` - 獲取平台熱門關鍵字
- `POST /admin/social-trends/collect` - 手動收集趨勢
- `GET /admin/trending-keywords/stats` - 獲取趨勢統計

#### 系統日誌
- `GET /admin/logs` - 獲取系統日誌
- `GET /admin/logs/stats` - 獲取日誌統計
- `POST /admin/logs/export` - 導出日誌

## 🔧 配置說明

### 環境變量配置

```bash
# 資料庫配置
DATABASE_URL=postgresql://admin:password@localhost:5432/admin_db

# Celery 配置
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# 安全配置
SECRET_KEY=your-secret-key-min-32-chars
ENCRYPTION_KEY=your-encryption-key

# API 密鑰
TWITTER_API_KEY=your-twitter-api-key
YOUTUBE_API_KEY=your-youtube-api-key

# 郵件配置
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ADMIN_EMAILS=admin@yourdomain.com
```

### 權限系統

系統支援三種預設角色：

- **super_admin**: 所有權限
- **admin**: 大部分管理權限
- **readonly**: 僅讀取權限

自定義權限包括：
- `ai_provider:*` - AI Provider 管理
- `crawler:*` - 爬蟲管理  
- `trends:*` - 趨勢管理
- `logs:*` - 日誌管理
- `users:*` - 用戶管理
- `system:*` - 系統管理

## 🛠️ 開發指南

### 本地開發環境

```bash
# 安裝依賴
pip install -r requirements.txt

# 設置環境變量
export DATABASE_URL="sqlite:///./admin.db"
export CELERY_BROKER_URL="redis://localhost:6379/1"

# 運行資料庫遷移
python -c "from database import init_db; init_db()"

# 啟動 API 服務
uvicorn main:app --reload --port 8080

# 啟動 Celery Worker
celery -A celery_app worker --loglevel=info

# 啟動 Celery Beat
celery -A celery_app beat --loglevel=info
```

### 添加新功能

1. **資料庫模型**: 在 `models.py` 中定義新的資料表
2. **API Schema**: 在 `schemas.py` 中定義請求/響應模型
3. **CRUD 操作**: 在 `crud.py` 中實現資料庫操作
4. **API 端點**: 在 `main.py` 中添加新的路由
5. **任務**: 在 `tasks/` 目錄下創建新的 Celery 任務

### 測試

```bash
# 運行單元測試
pytest tests/

# 運行覆蓋率測試
pytest --cov=. tests/

# 運行特定測試
pytest tests/test_ai_providers.py
```

## 📊 監控和維護

### 系統監控

- **健康檢查**: `GET /admin/health`
- **Celery 監控**: http://localhost:5555
- **日誌分析**: 查看 `logs/` 目錄
- **性能指標**: API 響應時間、錯誤率統計

### 日常維護

```bash
# 查看服務狀態
docker-compose ps

# 查看服務日誌
docker-compose logs -f admin-api

# 備份資料庫
docker-compose exec postgres pg_dump admin_db > backup.sql

# 清理舊日誌
curl -X DELETE "http://localhost:8080/admin/logs/cleanup?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 自動化任務

系統包含以下自動化任務：

- **爬蟲檢查**: 每分鐘檢查待執行的爬蟲
- **趨勢收集**: 每小時收集社交媒體趨勢
- **系統監控**: 每5分鐘進行健康檢查
- **日誌清理**: 每天清理舊日誌
- **資料備份**: 每天自動備份資料庫

## 🚨 故障排除

### 常見問題

1. **服務無法啟動**
   ```bash
   # 檢查端口佔用
   netstat -tlnp | grep :8080
   
   # 檢查 Docker 狀態
   docker-compose ps
   docker-compose logs admin-api
   ```

2. **資料庫連接失敗**
   ```bash
   # 檢查資料庫容器
   docker-compose logs postgres
   
   # 手動連接測試
   docker-compose exec postgres psql -U admin -d admin_db
   ```

3. **Celery 任務不執行**
   ```bash
   # 檢查 Celery Worker
   docker-compose logs celery-worker
   
   # 檢查 Redis 連接
   docker-compose exec redis redis-cli ping
   ```

4. **API 權限錯誤**
   - 檢查 JWT 令牌是否有效
   - 確認用戶角色和權限配置
   - 查看安全日誌

### 日誌位置

- **API 日誌**: `logs/admin_system.log`
- **Celery 日誌**: Docker 容器日誌
- **Nginx 日誌**: `/var/log/nginx/`
- **資料庫日誌**: PostgreSQL 容器日誌

## 🔒 安全最佳實踐

1. **立即修改預設密碼**
2. **配置強密碼策略**
3. **設置 IP 白名單**
4. **啟用 HTTPS**
5. **定期更新依賴**
6. **監控安全日誌**
7. **備份加密**

## 📄 授權

本項目採用 MIT 授權條款。詳見 LICENSE 文件。

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

1. Fork 本項目
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📞 支援

如有問題，請：

1. 查看文檔和常見問題
2. 搜索已有 Issue
3. 創建新的 Issue
4. 聯繫維護團隊

---

**快樂編程！** 🎉