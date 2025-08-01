# 🎬 Auto Video - AI 驅動的聲音克隆與影片生成系統

<div align="center">

![Auto Video Logo](https://img.shields.io/badge/Auto%20Video-AI%20Video%20Platform-blueviolet?style=for-the-badge&logo=video&logoColor=white)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-v3.11+-blue.svg)](https://www.python.org/downloads/)
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

- **Python**: 3.11+
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
chmod +x auto_generate_video_fold6/scripts/dev-setup.sh
./auto_generate_video_fold6/scripts/dev-setup.sh

# 3. 啟動開發環境
./auto_generate_video_fold6/scripts/start-dev.sh
```

### 手動設置（詳細步驟）

<details>
<summary>點擊展開詳細設置步驟</summary>

#### 1. 環境準備

```bash
# 創建並激活 Python 虛擬環境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# 安裝 Python 依賴
pip install -e .
```

#### 2. 前端設置

```bash
cd auto_generate_video_fold6/frontend
npm install
npm run build
cd ../..
```

#### 3. 環境變數配置

```bash
# 複製環境變數範本並修改
cp auto_generate_video_fold6/.env.example auto_generate_video_fold6/.env

# 編輯 .env 文件，填入必要的 API 金鑰
nano auto_generate_video_fold6/.env
```

#### 4. 資料庫初始化

```bash
# 啟動資料庫服務
cd auto_generate_video_fold6
docker-compose up -d postgres redis

# 執行資料庫遷移
python scripts/init-db.sql
```

#### 5. 啟動服務

```bash
# 啟動所有服務
docker-compose up -d

# 或使用開發模式
./scripts/start-dev.sh
```

</details>

## 📁 專案結構

```
auto-video-generation-fold6/
├── 📁 auto_generate_video_fold6/      # 主要應用程式目錄
│   ├── 🌐 frontend/                   # SvelteKit 前端應用
│   ├── 🔧 services/                   # 微服務實現
│   │   ├── 🔐 api-gateway/           # API 閘道器 (8000)
│   │   ├── 👤 auth-service/          # 認證服務 (8001)
│   │   ├── 💾 data-service/          # 資料服務 (8002)
│   │   ├── 🤖 inference-service/     # AI 推論服務 (8003)
│   │   ├── 🎬 video-service/         # 影片處理服務 (8004)
│   │   ├── 🧠 ai-service/            # AI 模型管理 (8005)
│   │   ├── 📱 social-service/        # 社群媒體整合 (8006)
│   │   ├── 📊 trend-service/         # 趋势分析 (8007)
│   │   └── ⏰ scheduler-service/     # 任務排程 (8008)
│   ├── 🗂️ config/                    # 配置文件
│   ├── 📊 monitoring/                # 監控配置
│   ├── 🛠️ scripts/                   # 維護腳本
│   ├── 🧪 tests/                     # 測試文件
│   ├── 📚 docs/                      # 技術文檔
│   └── 🐳 docker/                    # 容器編排文件
├── 📄 docs/                          # 專案文檔 (連結到子目錄)
├── 🔧 scripts/                       # 頂層腳本 (向下相容)
└── 📋 pyproject.toml                 # Python 專案配置
```

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

### 快速存取

- **API 文檔**: http://localhost:8000/docs
- **前端應用**: http://localhost:3000
- **Grafana 監控**: http://localhost:3001
- **Prometheus 指標**: http://localhost:9090

## 🧪 開發工具

### 代碼品質工具

```bash
# 代碼格式化與檢查
cd auto_generate_video_fold6
python scripts/fix_flake8.py

# 執行測試
pytest tests/ -v --cov=.

# 配置驗證
python scripts/config-validator.py
```

## 🚀 部署指南

### 開發環境

```bash
# 使用 Docker Compose
cd auto_generate_video_fold6
docker-compose -f docker/docker-compose.dev.yml up -d
```

### 生產環境

```bash
# 生產部署
cd auto_generate_video_fold6
docker-compose -f docker/docker-compose.prod.yml up -d

# 執行健康檢查
./scripts/health-check.sh
```

## 📚 文檔連結

- [📖 開發者指南](auto_generate_video_fold6/docs/DEVELOPER_GUIDE.md)
- [🏗️ 架構文檔](auto_generate_video_fold6/docs/ARCHITECTURE.md)
- [🔌 API 文檔](auto_generate_video_fold6/docs/API_REFERENCE.md)
- [🚀 部署指南](auto_generate_video_fold6/docs/DEPLOYMENT.md)
- [🔧 故障排除](auto_generate_video_fold6/docs/TROUBLESHOOTING.md)

## 🔒 安全性

### 安全功能

- 🔐 **JWT 認證**: 無狀態身份驗證
- 🛡️ **CORS 保護**: 跨域請求安全
- 🔒 **資料加密**: 敏感資料加密存儲
- 🚨 **安全標頭**: 完整的安全標頭設置
- 🔍 **漏洞掃描**: 自動化安全掃描

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

## 📄 版權聲明

本專案採用 [MIT 授權條款](LICENSE)。

---

<div align="center">

**🌟 如果這個專案對您有幫助，請給我們一個 Star！**

[⭐ Star this project](https://github.com/your-org/auto-video) | [🐛 Report Bug](https://github.com/your-org/auto-video/issues) | [💡 Request Feature](https://github.com/your-org/auto-video/issues)

</div>