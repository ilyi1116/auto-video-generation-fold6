# 開發流程指南 (Development Guide)

## 🚀 快速開始

### 系統要求
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (生產環境)
- Git

### 第一次設置
```bash
# 1. 克隆專案
git clone <repository-url>
cd myProject

# 2. 安裝依賴和設置 hooks
make install
make setup-hooks

# 3. 啟動開發環境
make dev
```

## 📋 常用開發指令

### Makefile 指令
```bash
# 🔧 開發環境
make dev              # 啟動完整開發環境
make dev-up           # 僅啟動 Docker 服務
make dev-down         # 停止所有服務
make logs             # 查看服務日誌
make health           # 檢查服務健康狀態

# 🧪 測試
make test             # 運行所有測試
make test-python      # 僅 Python 測試
make test-frontend    # 僅前端測試
make test-coverage    # 生成覆蓋率報告

# 🎨 程式碼品質
make format           # 格式化程式碼
make lint             # 運行 linting 檢查
make pre-commit       # 手動執行 pre-commit 檢查

# 🔒 安全性
make security         # 運行安全掃描
make audit           # 完整安全審計

# 🛠️ 實用工具
make validate         # 驗證配置檔案
make clean            # 清理暫存檔案
make info             # 顯示專案資訊
```

### 直接腳本
```bash
# 啟動開發環境
./scripts/start-dev.sh

# 健康檢查
python3 scripts/check-service-health.py

# 配置驗證
python3 scripts/validate-configs.py
```

## 🏗️ 專案架構

### 目錄結構
```
myProject/
├── src/                        # 主要應用程式碼
│   ├── services/              # 微服務 (17個)
│   │   ├── api-gateway/       # API 閘道器
│   │   ├── auth-service/      # 認證服務
│   │   ├── ai-service/        # AI 服務
│   │   └── ...                # 其他服務
│   ├── frontend/              # SvelteKit 前端
│   └── shared/                # 共享庫
│       ├── config.py          # 統一配置
│       ├── security.py        # 安全中間件
│       ├── service_discovery.py # 服務發現
│       └── service_client.py  # 服務通訊
├── config/                    # 配置管理
│   └── environments/          # 環境配置
├── scripts/                   # 工具腳本
├── tests/                     # 測試
├── infra/                     # 基礎設施
├── Makefile                   # 開發指令
├── .pre-commit-config.yaml    # Pre-commit 配置
└── pyproject.toml            # Python 依賴
```

### 微服務列表
| 服務 | 端口 | 描述 |
|------|------|------|
| API Gateway | 8000 | 統一入口點 |
| Auth Service | 8001 | 用戶認證 |
| Data Service | 8002 | 資料處理 |
| Inference Service | 8003 | 推論服務 |
| Video Service | 8004 | 影片處理 |
| AI Service | 8005 | AI 功能 |
| Social Service | 8006 | 社交媒體 |
| Trend Service | 8007 | 趨勢分析 |
| Scheduler Service | 8008 | 任務排程 |
| Storage Service | 8009 | 存儲管理 |

## 🔧 開發工作流程

### 1. 代碼開發
```bash
# 創建新分支
git checkout -b feature/new-feature

# 開發程式碼...

# 格式化程式碼
make format

# 運行測試
make test

# 檢查程式碼品質
make lint
```

### 2. Pre-commit Hooks
每次提交時自動執行：
- **Python**: Black formatting, isort, flake8, mypy, bandit
- **Frontend**: ESLint, Prettier, TypeScript check
- **通用**: YAML/JSON 檢查, 大文件檢查, 尾隨空格清理
- **Docker**: Hadolint Dockerfile 檢查
- **安全**: 依賴安全掃描

### 3. 提交流程
```bash
# Pre-commit hooks 會自動運行
git add .
git commit -m "feat: add new feature"

# 如果 hooks 失敗，修復問題後重新提交
make format        # 修復格式問題
make lint          # 檢查其他問題
git add .
git commit -m "feat: add new feature"
```

### 4. 測試策略
- **單元測試**: 每個服務的核心邏輯
- **集成測試**: 服務間交互
- **端到端測試**: 完整用戶流程
- **覆蓋率目標**: Python ≥80%, Frontend ≥80%

## 🔒 安全最佳實踐

### 開發環境安全
- 使用環境變數管理敏感配置
- JWT 認證和授權
- API 限流和安全頭部
- 輸入驗證和清理
- 安全依賴掃描

### 生產環境安全
- SSL/TLS 加密
- 數據庫連接加密
- 備份加密
- 審計日誌
- 定期安全掃描

## 📊 監控和可觀測性

### 健康檢查
```bash
# 檢查所有服務
make health

# 或直接使用腳本
python3 scripts/check-service-health.py
```

### 監控端點
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- API 文檔: http://localhost:8000/docs

### 日誌管理
- 結構化日誌 (JSON 格式)
- 集中式日誌收集
- 分級日誌 (DEBUG, INFO, WARNING, ERROR)
- 審計日誌分離

## 🚀 部署流程

### 開發環境
```bash
make deploy-dev
```

### 生產環境
```bash
make build-prod
make deploy-prod
```

### 配置管理
- `development.env`: 開發環境
- `testing.env`: 測試環境
- `production.env`: 生產環境
- `production-advanced.env`: 企業級生產配置

## 🛠️ 故障排除

### 常見問題

#### 服務啟動失敗
```bash
# 檢查 Docker 狀態
docker-compose ps

# 查看日誌
make logs

# 檢查配置
make validate
```

#### 測試失敗
```bash
# 檢查測試環境
make test-python
make test-frontend

# 檢查覆蓋率
make test-coverage
```

#### Pre-commit Hook 失敗
```bash
# 格式化程式碼
make format

# 檢查語法錯誤
make lint

# 手動運行 hooks
make pre-commit
```

### 日誌位置
- 應用日誌: `/app/logs/app.log`
- 審計日誌: `/app/logs/audit.log`
- 健康檢查報告: `health-check-report.json`
- 安全報告: `bandit-report.json`, `safety-report.json`

## 📚 額外資源

### API 文檔
- **主要 API**: http://localhost:8000/docs
- **認證服務**: http://localhost:8001/docs
- **AI 服務**: http://localhost:8005/docs

### 開發工具
- **VS Code**: 推薦安裝 Python, Svelte, Docker 擴展
- **Postman**: API 測試集合 (docs/api/postman/)
- **DBeaver**: 資料庫管理工具

### 學習資源
- FastAPI: https://fastapi.tiangolo.com/
- SvelteKit: https://kit.svelte.dev/
- Docker: https://docs.docker.com/
- 微服務架構: https://microservices.io/

## 🤝 貢獻指南

### 代碼規範
- 使用 Black 格式化 Python 代碼
- 使用 Prettier 格式化前端代碼
- 變數和函數使用描述性名稱
- 添加適當的類型註解
- 編寫清晰的文檔字符串

### 提交訊息格式
```
type(scope): description

feat: 新功能
fix: 錯誤修復
docs: 文檔更新
style: 格式調整
refactor: 重構
test: 測試相關
chore: 雜項任務
```

### Pull Request 流程
1. Fork 專案
2. 創建功能分支
3. 開發並測試
4. 確保所有檢查通過
5. 提交 PR 並描述變更
6. 等待代碼審查

---

## 📞 支援

如果遇到問題：
1. 檢查此文檔的故障排除部分
2. 搜索現有的 Issues
3. 創建新的 Issue 並提供詳細資訊
4. 聯繫開發團隊

**Happy Coding! 🎉**