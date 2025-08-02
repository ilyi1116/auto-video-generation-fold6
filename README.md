# Auto Video Generation System

## 項目結構

```
auto-video-generation-system/
├── backend/           # 後端應用程式
├── frontend/          # 前端應用程式
├── scripts/           # 部署與維護腳本
├── docs/              # 文件
└── tests/             # 測試
```

## 快速開始

### 開發環境

```bash
# 1. 啟動開發環境
./scripts/deploy/dev.sh

# 2. 執行測試
./scripts/test/run_tests.py
```

### 生產部署

```bash
# 使用 Docker
./scripts/deploy/docker.sh

# 使用 Kubernetes
./scripts/deploy/k8s.sh
```

## 配置

使用 `env.development` 和 `env.production` 進行環境配置。

## 測試

```bash
# 執行所有測試
python scripts/test/run_tests.py
```

## 服務架構

- **API Gateway (8000)**: 統一入口點
- **Auth Service (8001)**: 用戶認證
- **Video Service (8004)**: 影片處理
- **AI Service (8005)**: AI 模型管理
- **Social Service (8006)**: 社群媒體整合
- **Trend Service (8007)**: 趨勢分析
- **Scheduler Service (8008)**: 任務排程

## 技術棧

### 後端
- FastAPI
- PostgreSQL
- Redis
- Celery

### 前端
- React/TypeScript
- Material-UI

### 部署
- Docker
- Kubernetes

## 文檔

- [開發者指南](docs/DEVELOPER_GUIDE.md)
- [架構文檔](docs/ARCHITECTURE.md)
- [API 參考](docs/API_REFERENCE.md)
- [部署指南](docs/DEPLOYMENT.md)

## 貢獻

1. Fork 專案
2. 創建功能分支
3. 提交變更
4. 發起 Pull Request

## 授權

MIT License
