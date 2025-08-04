# 配置管理系統

## 📁 目錄結構

```
config/
├── environments/           # 環境特定配置
│   ├── development.env    # 開發環境
│   ├── testing.env       # 測試環境
│   └── production.env.template  # 生產環境模板
├── load_env.py           # 配置載入器
└── README.md            # 本文檔
```

## 🚀 使用方式

### 1. 開發環境設定

```bash
# 複製並編輯開發環境配置
cp config/environments/development.env .env
# 編輯 .env 文件以符合你的本地環境
```

### 2. Docker 環境

```bash
# 使用預設的 Docker 環境配置
docker-compose --env-file docker-compose.env up
```

### 3. 生產環境部署

```bash
# 複製生產環境模板
cp config/environments/production.env.template config/environments/production.env
# 編輯 production.env 並填入真實的生產環境配置
# 注意：不要將生產環境配置提交到版本控制
```

## 🔧 配置載入

### Python 應用中使用

```python
from config.load_env import load_dotenv_from_environment

# 自動根據 ENVIRONMENT 環境變數載入對應配置
load_dotenv_from_environment()
```

### 手動指定環境

```python
import os
from dotenv import load_dotenv
from config.load_env import load_environment_config

# 載入測試環境配置
config_file = load_environment_config('testing')
load_dotenv(config_file)
```

## 📋 配置類別

### 🌍 基本環境設定
- `ENVIRONMENT`: 環境類型 (development/testing/production)
- `DEBUG`: 除錯模式
- `LOG_LEVEL`: 日誌級別

### 🔒 安全設定
- `JWT_SECRET_KEY`: JWT 簽名密鑰
- `ENCRYPTION_KEY`: 資料加密密鑰

### 🗄️ 資料庫設定
- `DATABASE_URL`: PostgreSQL 連接字串
- `REDIS_URL`: Redis 連接字串

### 🤖 AI 服務 API
- `OPENAI_API_KEY`: OpenAI API
- `ANTHROPIC_API_KEY`: Anthropic Claude API
- 等等...

### 📱 社群媒體 API
- `TIKTOK_CLIENT_ID/SECRET`: TikTok API
- `YOUTUBE_CLIENT_ID/SECRET`: YouTube API
- 等等...

## 🛡️ 安全最佳實踐

1. **不要提交敏感配置到版本控制**
   - 只提交 `.env.example` 和 `.env.template` 檔案
   - 將實際的 `.env` 檔案加入 `.gitignore`

2. **使用強密鑰**
   - JWT 密鑰至少 32 字元
   - 加密密鑰必須是 32 字元

3. **環境隔離**
   - 開發、測試、生產使用不同的配置
   - 生產環境配置存放在安全的地方

4. **定期輪換密鑰**
   - API 密鑰定期更新
   - 資料庫密碼定期更換

## 🚨 故障排除

### 配置檔案找不到
```bash
# 檢查配置檔案是否存在
ls -la config/environments/

# 檢查環境變數
echo $ENVIRONMENT
```

### 配置載入失敗
```bash
# 檢查 Python 依賴
pip install python-dotenv

# 測試配置載入
python config/load_env.py
```

### Docker 配置問題
```bash
# 檢查 Docker 環境變數
docker-compose config

# 重新構建容器
docker-compose up --build
```
