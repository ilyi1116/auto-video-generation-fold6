# 🎬 Auto Video - AI 驅動的聲音克隆與影片生成系統

<div align="center">

![Auto Video Logo](https://img.shields.io/badge/Auto%20Video-AI%20Video%20Platform-blueviolet?style=for-the-badge&logo=video&logoColor=white)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-v3.9+-blue.svg)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/node-v18+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://www.docker.com/)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](https://pytest.org/)

</div>

## 📖 專案概覽

Auto Video 是一個**企業級的 AI 聲音克隆與自動影片生成系統**，採用現代微服務架構，整合多種先進 AI 技術，實現從語音克隆到社群媒體發布的完整自動化流程。

### 🌟 核心功能

- 🎤 **AI 語音克隆** - 高品質個人化語音合成
- 📝 **智能腳本生成** - AI 驅動的內容創作
- 🎨 **自動視覺創建** - 圖像生成與影片組裝
- 📊 **趨勢分析** - 社群媒體趨勢追蹤與分析
- 🚀 **一鍵發布** - 多平台自動化發布系統
- 📈 **效能監控** - 企業級監控與分析

### 🏗️ 技術架構

- **後端**: FastAPI (Python) + 微服務架構
- **前端**: SvelteKit + TypeScript
- **AI 服務**: Google Gemini, Stable Diffusion, ElevenLabs
- **資料庫**: PostgreSQL + Redis
- **監控**: Prometheus + Grafana
- **部署**: Docker + Docker Compose

## 🚀 快速開始

### 系統要求

- **Python**: 3.9+
- **Node.js**: 18+
- **Docker**: 20.10+
- **記憶體**: 至少 8GB RAM
- **儲存**: 至少 50GB 可用空間

### 一鍵環境設置

```bash
# 1. 克隆專案
git clone https://github.com/your-org/auto-video.git
cd auto-video

# 2. 執行自動化設置腳本
chmod +x scripts/dev-setup.sh
./scripts/dev-setup.sh

# 3. 啟動開發環境
./scripts/dev-server.sh
```

### 手動設置（詳細步驟）

<details>
<summary>點擊展開詳細設置步驟</summary>

#### 1. 環境準備

```bash
# 創建並激活 Python 虛擬環境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate.bat  # Windows

# 安裝 Python 依賴
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 2. 前端設置

```bash
cd frontend
npm install
npm run build
cd ..
```

#### 3. 環境變數配置

```bash
# 複製環境變數範本並修改
cp .env.example .env

# 編輯 .env 文件，填入必要的 API 金鑰
nano .env
```

#### 4. 資料庫初始化

```bash
# 啟動資料庫服務
docker-compose up -d postgres redis

# 執行資料庫遷移
alembic upgrade head

# 創建初始管理員用戶
python scripts/create-admin.py
```

#### 5. 啟動服務

```bash
# 啟動所有服務
docker-compose up -d

# 或分別啟動各個服務
python -m uvicorn main:app --reload --port 8000  # API Gateway
cd frontend && npm run dev  # 前端服務
```

</details>

## 📁 專案結構

```
auto-video/
├── 📁 services/                    # 微服務實現
│   ├── 🔐 api-gateway/            # API 閘道器 (8000)
│   ├── 👤 auth-service/           # 認證服務 (8001)
│   ├── 💾 data-service/           # 資料服務 (8002)
│   ├── 🤖 inference-service/      # AI 推論服務 (8003)
│   ├── 🎬 video-service/          # 影片處理服務 (8004)
│   ├── 🧠 ai-service/             # AI 模型管理 (8005)
│   ├── 📱 social-service/         # 社群媒體整合 (8006)
│   ├── 📊 trend-service/          # 趋势分析 (8007)
│   └── ⏰ scheduler-service/      # 任務排程 (8008)
├── 🌐 frontend/                   # SvelteKit 前端應用
├── 🔧 shared/                     # 共享程式庫
│   ├── api/                      # API 標準格式
│   ├── auth/                     # 認證工具
│   ├── database/                 # 資料庫工具
│   ├── error_handling/           # 錯誤處理
│   └── utils/                    # 通用工具
├── 🗂️ config/                     # 配置文件
├── 📊 monitoring/                 # 監控配置
│   ├── prometheus/               # Prometheus 配置
│   ├── grafana/                  # Grafana 儀表板
│   └── alertmanager/             # 告警管理
├── 🛠️ scripts/                    # 維護腳本
├── 🧪 tests/                      # 測試文件
├── 📚 docs/                       # 文檔目錄
└── 🐳 docker-compose*.yml         # 容器編排文件
```

## 🛠️ 開發工具

### 代碼品質工具

```bash
# 代碼格式化
./scripts/quality-check.sh

# 執行測試
./scripts/test.sh

# 測試覆蓋率分析
python scripts/test-coverage-audit.py

# 配置驗證
python scripts/config-validator.py
```

### 監控與除錯

- **API 文檔**: http://localhost:8000/docs
- **前端應用**: http://localhost:3000
- **Grafana 監控**: http://localhost:3001
- **Prometheus 指標**: http://localhost:9090

## 🔧 API 概覽

### 核心 API 端點

| 服務 | 端點 | 描述 |
|------|------|------|
| 🔐 認證 | `/api/v1/auth/*` | 用戶註冊、登入、JWT 管理 |
| 👤 用戶 | `/api/v1/users/*` | 用戶資料管理 |
| 🎬 影片 | `/api/v1/videos/*` | 影片創建、處理、管理 |
| 🤖 AI | `/api/v1/ai/*` | AI 服務接口 |
| 📱 社群 | `/api/v1/social/*` | 社群媒體整合 |
| 📊 分析 | `/api/v1/analytics/*` | 數據分析與報告 |

### API 標準格式

所有 API 回應遵循統一格式：

```json
{
  "status": "success|error|warning|info",
  "message": "操作結果說明",
  "data": { /* 實際數據 */ },
  "errors": [ /* 錯誤詳情 */ ],
  "pagination": { /* 分頁信息 */ },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req-123",
    "execution_time_ms": 150
  }
}
```

## 🧪 測試策略

### 測試類型

- **單元測試**: 個別函數和類的測試
- **整合測試**: 服務間協作測試
- **端對端測試**: 完整用戶流程測試
- **效能測試**: 負載和壓力測試

### 執行測試

```bash
# 執行所有測試
pytest tests/ -v --cov=.

# 特定測試類型
pytest tests/unit/ -v           # 單元測試
pytest tests/integration/ -v    # 整合測試
pytest tests/e2e/ -v           # 端對端測試

# 測試覆蓋率報告
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## 🚀 部署指南

### 開發環境

```bash
# 使用 Docker Compose
docker-compose -f docker-compose.dev.yml up -d
```

### 生產環境

```bash
# 設置環境變數
export ENVIRONMENT=production
export DATABASE_URL=postgresql://...
export REDIS_URL=redis://...

# 部署到生產環境
docker-compose -f docker-compose.prod.yml up -d

# 執行健康檢查
./scripts/health-check.sh
```

### CI/CD 流程

專案使用 GitHub Actions 進行自動化部署：

1. **程式碼檢查**: Linting, 格式化驗證
2. **測試執行**: 單元、整合、端對端測試
3. **安全掃描**: 依賴漏洞掃描
4. **容器構建**: Docker 映像建構和推送
5. **自動部署**: 部署到測試/生產環境

## 📊 監控與日誌

### 監控指標

- **系統指標**: CPU、記憶體、磁碟使用率
- **應用指標**: API 回應時間、錯誤率、吞吐量
- **業務指標**: 影片生成數量、用戶活躍度

### 日誌管理

```bash
# 查看服務日誌
docker-compose logs -f [service-name]

# 結構化日誌查詢
grep "ERROR" logs/app.log | jq '.'

# 即時監控
tail -f logs/app.log | grep "API"
```

## 🔒 安全性

### 安全功能

- 🔐 **JWT 認證**: 無狀態身份驗證
- 🛡️ **CORS 保護**: 跨域請求安全
- 🔒 **資料加密**: 敏感資料加密存儲
- 🚨 **安全標頭**: 完整的安全標頭設置
- 🔍 **漏洞掃描**: 自動化安全掃描

### 安全最佳實踐

- 定期更新依賴項
- 使用強密碼和 API 金鑰
- 限制 API 請求率
- 監控異常活動

## 🤝 貢獻指南

### 開發流程

1. **Fork 專案** 並創建功能分支
2. **編寫程式碼** 並遵循編碼規範
3. **撰寫測試** 確保測試覆蓋率 ≥ 80%
4. **執行品質檢查** 通過所有檢查
5. **提交 Pull Request** 並填寫完整描述

### 編碼規範

- **Python**: 遵循 PEP 8，使用 Black 格式化
- **JavaScript/TypeScript**: 使用 Prettier + ESLint
- **提交消息**: 使用 Conventional Commits 格式

```bash
# 提交消息格式
feat(auth): add OAuth login support
fix(video): resolve rendering timeout issue
docs(api): update endpoint documentation
```

### 代碼審查清單

- [ ] 程式碼符合專案風格指南
- [ ] 包含適當的測試
- [ ] 通過所有 CI/CD 檢查
- [ ] 更新相關文檔
- [ ] 無安全漏洞

## 📚 資源連結

### 官方文檔

- [📖 開發者指南](docs/DEVELOPER_GUIDE.md)
- [🏗️ 架構文檔](docs/ARCHITECTURE.md)
- [🔌 API 文檔](docs/API_REFERENCE.md)
- [🚀 部署指南](docs/DEPLOYMENT.md)
- [🔧 故障排除](docs/TROUBLESHOOTING.md)

### 外部資源

- [FastAPI 文檔](https://fastapi.tiangolo.com/)
- [SvelteKit 指南](https://kit.svelte.dev/docs)
- [Docker 最佳實踐](https://docs.docker.com/develop/best-practices/)
- [Prometheus 監控](https://prometheus.io/docs/)

## 📞 支援與回饋

### 獲取幫助

- **文檔**: 查看 `docs/` 目錄中的詳細文檔
- **Issues**: 在 GitHub Issues 中報告問題
- **討論**: 在 GitHub Discussions 中參與討論

### 常見問題

<details>
<summary>如何重置開發環境？</summary>

```bash
# 清理容器和資料
docker-compose down -v
docker system prune -a

# 重新設置環境
./scripts/dev-setup.sh
```

</details>

<details>
<summary>如何添加新的 AI 服務提供商？</summary>

1. 在 `services/ai-service/providers/` 創建新的提供商實現
2. 更新配置模式和驗證規則
3. 添加相應的測試
4. 更新 API 文檔

</details>

<details>
<summary>如何擴展新的社群媒體平台？</summary>

1. 實現 `services/social-service/platforms/` 中的平台接口
2. 添加平台特定的認證和 API 調用
3. 更新前端平台選擇器
4. 撰寫整合測試

</details>

## 📄 版權聲明

本專案採用 [MIT 授權條款](LICENSE)。

---

<div align="center">

**🌟 如果這個專案對您有幫助，請給我們一個 Star！**

[⭐ Star this project](https://github.com/your-org/auto-video) | [🐛 Report Bug](https://github.com/your-org/auto-video/issues) | [💡 Request Feature](https://github.com/your-org/auto-video/issues)

</div>