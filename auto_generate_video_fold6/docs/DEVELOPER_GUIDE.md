# 開發者指南

## 快速開始

### 環境設置

1. 克隆專案
```bash
git clone <repository-url>
cd auto-video-generation-system
```

2. 設置環境變量
```bash
cp env.development .env.development
```

3. 安裝依賴
```bash
cd backend
pip install -r requirements.txt
```

### 開發環境啟動

```bash
# 啟動開發環境
./scripts/deploy/dev.sh

# 執行測試
./scripts/test/run_tests.py
```

### 代碼規範

- 使用 Black 進行代碼格式化
- 使用 Flake8 進行代碼檢查
- 遵循 PEP 8 規範

```bash
# 格式化代碼
./scripts/lint/format.py

# 檢查代碼
./scripts/lint/check.py
```

## 專案結構

```
backend/
├── api_gateway/          # API 閘道器
├── auth_service/         # 認證服務
├── video_service/        # 影片處理服務
├── ai_service/          # AI 模型管理
├── social_service/      # 社群媒體整合
├── trend_service/       # 趨勢分析
├── scheduler_service/   # 任務排程
└── shared/             # 共享組件
```

## API 開發

### 創建新的 API 端點

1. 在對應服務的 `routers/` 目錄下創建路由文件
2. 在 `models/` 目錄下定義數據模型
3. 在 `services/` 目錄下實現業務邏輯

### 測試

```bash
# 執行單元測試
pytest tests/backend/

# 執行整合測試
pytest tests/integration/

# 生成覆蓋率報告
./scripts/test/coverage.py
```

## 部署

### 開發環境
```bash
./scripts/deploy/dev.sh
```

### Docker 環境
```bash
./scripts/deploy/docker.sh
```

### Kubernetes 環境
```bash
./scripts/deploy/k8s.sh
```

## 故障排除

### 常見問題

1. **服務無法啟動**
   - 檢查環境變量配置
   - 確認依賴已正確安裝
   - 查看日誌文件

2. **數據庫連接失敗**
   - 確認數據庫服務正在運行
   - 檢查連接字符串配置
   - 驗證數據庫權限

3. **測試失敗**
   - 確認測試環境配置正確
   - 檢查測試數據是否完整
   - 查看測試日誌

### 日誌查看

```bash
# Docker 日誌
docker-compose logs -f

# Kubernetes 日誌
kubectl logs -f deployment/api-gateway
```