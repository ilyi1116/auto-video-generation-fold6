# Trend Analysis Service

## 📋 服務概述

趨勢分析、關鍵字挖掘和競爭對手分析服務

## 🚀 快速開始

### 開發環境啟動

```bash
# 1. 安裝依賴
cd src/services/trend-service
pip install -e .

# 2. 設置環境變量
cp .env.example .env
# 編輯 .env 文件配置必要參數

# 3. 啟動服務
uvicorn app.main:app --reload --port 8007
```

### Docker 啟動

```bash
# 構建鏡像
docker build -t trend-service .

# 運行容器
docker run -p 8007:8007 --env-file .env trend-service
```

## 🏗️ 技術架構

### 技術棧
- **FastAPI**
- **Data Analytics**
- **External APIs**

### 服務依賴
- database
- external-apis

### 端口配置
- **服務端口**: 8007
- **健康檢查**: `GET /health`
- **指標端點**: `GET /metrics` 

## 📚 API 文檔

### 主要端點
- `/trends/analyze`
- `/trends/keywords`
- `/trends/competitors`

### API 文檔訪問
- **Swagger UI**: http://localhost:8007/docs
- **ReDoc**: http://localhost:8007/redoc
- **OpenAPI JSON**: http://localhost:8007/openapi.json

## 🧪 測試

### 運行測試
```bash
# 單元測試
pytest tests/ -v

# 測試覆蓋率
pytest tests/ --cov=app --cov-report=html

# 集成測試
pytest tests/integration/ -v
```

### 測試數據
測試數據位於 `tests/fixtures/` 目錄中。

## 📦 部署

### 環境變量
參考 `.env.example` 文件，主要配置項：

```bash
# 基礎配置
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# 服務配置
SERVICE_PORT=8007
SERVICE_NAME=trend-service

# 數據庫配置（如適用）
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0

# 安全配置
JWT_SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### 健康檢查
```bash
curl http://localhost:8007/health
```

預期響應：
```json
{"status": "healthy", "service": "trend-service", "version": "1.0.0"}
```

## 🔧 開發指南

### 代碼結構
```
trend-service/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 應用入口
│   ├── config.py        # 配置管理
│   ├── routers/         # API 路由
│   ├── services/        # 業務邏輯
│   ├── models/          # 數據模型
│   └── schemas/         # Pydantic 模式
├── tests/               # 測試文件
├── Dockerfile          # Docker 配置
└── README.md           # 本文檔
```

### 添加新功能
1. 在 `app/routers/` 中添加新的路由模組
2. 在 `app/services/` 中實現業務邏輯
3. 在 `app/schemas/` 中定義數據模式
4. 在 `tests/` 中添加相應測試
5. 更新 API 文檔

### 代碼規範
- 使用 Black 進行代碼格式化
- 使用 Flake8 進行靜態檢查
- 使用 mypy 進行類型檢查
- 保持測試覆蓋率 > 80%

## 🐛 故障排除

### 常見問題

#### 服務無法啟動
```bash
# 檢查端口是否被占用
lsof -i :8007

# 檢查環境變量
env | grep -E "(DATABASE|REDIS|JWT)"

# 查看日誌
docker logs trend-service
```

#### 依賴服務連接失敗
```bash
# 檢查網絡連接
curl http://dependency-service:port/health

# 檢查 Docker 網絡
docker network ls
docker network inspect myproject_default
```

### 日誌查看
```bash
# 本地開發
tail -f logs/trend-service.log

# Docker 環境
docker logs -f trend-service

# Kubernetes 環境
kubectl logs -f deployment/trend-service
```

## 📈 監控與可觀測性

### 指標
- **健康狀態**: `/health` 端點
- **性能指標**: `/metrics` 端點（Prometheus 格式）
- **自定義指標**: 業務相關指標

### 日誌
- **結構化日誌**: JSON 格式輸出
- **日誌級別**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **追蹤標識**: Request ID 追蹤

### 分佈式追蹤
- **OpenTelemetry**: 分佈式追蹤支持
- **Jaeger**: 追蹤可視化
- **服務映射**: 依賴關係可視化

## 🔗 相關文檔

- [架構設計文檔](../../docs/architecture.md)
- [API 設計規範](../../docs/api-guidelines.md)
- [部署指南](../../docs/deployment.md)
- [監控配置](../../docs/monitoring.md)

## 📞 支持

如有問題或需要支持，請：

1. 查看 [故障排除](#-故障排除) 部分
2. 檢查 [GitHub Issues](https://github.com/yourorg/project/issues)
3. 聯繫開發團隊

---

**版本**: 1.0.0  
**最後更新**: 2025-08-04  
**維護者**: 開發團隊
