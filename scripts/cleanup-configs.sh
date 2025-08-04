#!/bin/bash

# cleanup-configs.sh - 配置檔案清理和統一化腳本
# 用途：清理重複的環境配置檔案並建立統一的配置管理

set -e

# 顏色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日誌函數
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 檢查當前環境配置檔案
analyze_current_configs() {
    log_info "分析當前的配置檔案..."
    
    echo "發現的 .env 檔案："
    find . -name ".env*" -type f | sort
    
    echo
    echo "配置檔案大小："
    find . -name ".env*" -type f -exec ls -lh {} \; | awk '{print $5, $9}'
}

# 建立統一配置模板
create_unified_template() {
    log_info "建立統一配置模板..."
    
    # 確保目錄存在
    mkdir -p config/environments
    
    # 分析並合併各種 .env 檔案的內容
    local temp_file=$(mktemp)
    
    # 收集所有獨特的配置鍵
    {
        # 從根目錄的 .env 檔案
        [ -f ".env" ] && cat ".env"
        [ -f ".env.development" ] && cat ".env.development"
        [ -f ".env.production" ] && cat ".env.production"
        [ -f ".env.example" ] && cat ".env.example"
        [ -f ".env.template" ] && cat ".env.template"
        
        # 從 auto_generate_video_fold6 的 .env 檔案
        [ -f "auto_generate_video_fold6/.env" ] && cat "auto_generate_video_fold6/.env"
        [ -f "auto_generate_video_fold6/.env.development" ] && cat "auto_generate_video_fold6/.env.development"
        [ -f "auto_generate_video_fold6/.env.production" ] && cat "auto_generate_video_fold6/.env.production"
        [ -f "auto_generate_video_fold6/.env.example" ] && cat "auto_generate_video_fold6/.env.example"
        [ -f "auto_generate_video_fold6/.env.testing" ] && cat "auto_generate_video_fold6/.env.testing"
        
        # 從服務目錄的 .env 檔案
        find services/ -name ".env*" -type f -exec cat {} \; 2>/dev/null || true
        find auto_generate_video_fold6/services/ -name ".env*" -type f -exec cat {} \; 2>/dev/null || true
    } | grep -E '^[A-Z_].*=' | sort -u > "$temp_file"
    
    # 建立新的 .env.example
    cat > ".env.example.unified" << 'EOF'
# ==============================================
# Auto Video Generation System - 環境配置
# ==============================================
# 這是統一的環境配置模板
# 複製此檔案為 .env 並修改相應的值

# ==============================================
# 🌍 基本環境設定
# ==============================================
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=info
TZ=Asia/Taipei

# ==============================================
# 🔒 安全設定
# ==============================================
# JWT 密鑰 (生產環境請使用強密碼)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 加密密鑰
ENCRYPTION_KEY=your-encryption-key-32-characters

# ==============================================
# 🗄️ 資料庫設定
# ==============================================
# PostgreSQL 主資料庫
DATABASE_URL=postgresql://postgres:password@localhost:5432/autovideo
DB_HOST=localhost
DB_PORT=5432
DB_NAME=autovideo
DB_USER=postgres
DB_PASSWORD=password
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis 快取
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# ==============================================
# 🤖 AI 服務 API 設定
# ==============================================
# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=4000

# Anthropic Claude
ANTHROPIC_API_KEY=your-anthropic-api-key

# Google Gemini
GOOGLE_API_KEY=your-google-api-key

# Stability AI
STABILITY_API_KEY=your-stability-ai-key

# ElevenLabs 語音合成
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# ==============================================
# 📱 社群媒體 API 設定  
# ==============================================
# TikTok
TIKTOK_CLIENT_ID=your-tiktok-client-id
TIKTOK_CLIENT_SECRET=your-tiktok-client-secret

# YouTube
YOUTUBE_CLIENT_ID=your-youtube-client-id
YOUTUBE_CLIENT_SECRET=your-youtube-client-secret

# Instagram
INSTAGRAM_CLIENT_ID=your-instagram-client-id
INSTAGRAM_CLIENT_SECRET=your-instagram-client-secret

# ==============================================
# 📁 檔案儲存設定
# ==============================================
# 本地儲存
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=100MB

# S3 相容儲存 (MinIO/AWS S3)
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=autovideo
S3_REGION=us-east-1

# ==============================================
# 🔄 任務佇列設定 (Celery)
# ==============================================
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json

# ==============================================
# 📊 監控與日誌設定
# ==============================================
# Prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# Jaeger 追蹤
JAEGER_ENABLED=false
JAEGER_ENDPOINT=http://localhost:14268/api/traces

# 結構化日誌
STRUCTURED_LOGGING=true
LOG_FORMAT=json

# ==============================================
# 🌐 網路設定
# ==============================================
# API 設定
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=true

# CORS 設定
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
CORS_CREDENTIALS=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# ==============================================
# 🐳 Docker 設定
# ==============================================
COMPOSE_PROJECT_NAME=autovideo
DOCKER_BUILDKIT=1

# ==============================================
# 🧪 測試設定
# ==============================================
TEST_DATABASE_URL=postgresql://postgres:password@localhost:5432/autovideo_test
TEST_REDIS_URL=redis://localhost:6379/15

# ==============================================
# 💰 付費服務設定
# ==============================================
# Stripe
STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

EOF

    # 添加從現有檔案中提取的唯一配置
    if [ -s "$temp_file" ]; then
        echo "" >> ".env.example.unified"
        echo "# ===============================================" >> ".env.example.unified"
        echo "# 📋 其他現有配置" >> ".env.example.unified"
        echo "# ===============================================" >> ".env.example.unified"
        
        # 過濾掉已經包含的配置鍵
        grep -v -E '^(ENVIRONMENT|DEBUG|LOG_LEVEL|TZ|JWT_|ENCRYPTION_KEY|DATABASE_URL|DB_|REDIS_|OPENAI_|ANTHROPIC_|GOOGLE_|STABILITY_|ELEVENLABS_|TIKTOK_|YOUTUBE_|INSTAGRAM_|UPLOAD_DIR|MAX_FILE_SIZE|S3_|CELERY_|PROMETHEUS_|JAEGER_|STRUCTURED_LOGGING|LOG_FORMAT|API_|CORS_|RATE_LIMIT_|COMPOSE_PROJECT_NAME|DOCKER_BUILDKIT|TEST_|STRIPE_)' "$temp_file" >> ".env.example.unified" || true
    fi
    
    rm -f "$temp_file"
    log_success "統一配置模板已建立：.env.example.unified"
}

# 建立環境特定配置
create_environment_configs() {
    log_info "建立環境特定配置..."
    
    # 開發環境配置
    cat > "config/environments/development.env" << 'EOF'
# 開發環境配置
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug

# 本地開發用的簡單設定
DATABASE_URL=postgresql://postgres:password@localhost:5432/autovideo_dev
REDIS_URL=redis://localhost:6379/0

# 本地檔案儲存
UPLOAD_DIR=./uploads/dev
S3_ENDPOINT=http://localhost:9000

# API 設定
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
API_WORKERS=1

# CORS 設定 (開發環境寬鬆設定)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080
CORS_CREDENTIALS=true

# 監控關閉（開發環境）
PROMETHEUS_ENABLED=false
JAEGER_ENABLED=false
EOF

    # 測試環境配置
    cat > "config/environments/testing.env" << 'EOF'
# 測試環境配置
ENVIRONMENT=testing
DEBUG=false
LOG_LEVEL=warning

# 測試資料庫
DATABASE_URL=postgresql://postgres:password@localhost:5432/autovideo_test
REDIS_URL=redis://localhost:6379/15

# 測試用的檔案儲存
UPLOAD_DIR=./uploads/test
S3_ENDPOINT=http://localhost:9000

# API 設定
API_HOST=0.0.0.0
API_PORT=8001
API_RELOAD=false
API_WORKERS=1

# 快速測試設定
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=5
RATE_LIMIT_ENABLED=false

# 監控關閉
PROMETHEUS_ENABLED=false
JAEGER_ENABLED=false
EOF

    # 生產環境配置模板
    cat > "config/environments/production.env.template" << 'EOF'
# 生產環境配置模板
# 注意：這個檔案包含敏感資訊，不應該提交到版本控制

ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# 生產資料庫（請使用強密碼）
DATABASE_URL=postgresql://username:password@db-host:5432/autovideo_prod
REDIS_URL=redis://redis-host:6379/0

# 生產級檔案儲存
S3_ENDPOINT=https://s3.amazonaws.com
S3_ACCESS_KEY=YOUR_PRODUCTION_ACCESS_KEY
S3_SECRET_KEY=YOUR_PRODUCTION_SECRET_KEY
S3_BUCKET_NAME=autovideo-prod

# API 設定
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
API_WORKERS=4

# 安全設定（請使用強密鑰）
JWT_SECRET_KEY=YOUR_SUPER_STRONG_JWT_SECRET_KEY_AT_LEAST_32_CHARACTERS
ENCRYPTION_KEY=YOUR_32_CHARACTER_ENCRYPTION_KEY

# CORS 設定（僅允許生產域名）
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
CORS_CREDENTIALS=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# 監控啟用
PROMETHEUS_ENABLED=true
JAEGER_ENABLED=true
STRUCTURED_LOGGING=true
LOG_FORMAT=json

# 付費服務（生產金鑰）
STRIPE_PUBLIC_KEY=pk_live_your_stripe_public_key
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_production_webhook_secret
EOF

    log_success "環境特定配置已建立"
}

# 建立配置載入器
create_config_loader() {
    log_info "建立配置載入器..."
    
    cat > "config/load_env.py" << 'EOF'
"""
環境配置載入器
用於根據環境變數載入對應的配置檔案
"""

import os
from pathlib import Path
from typing import Optional

def load_environment_config(env: Optional[str] = None) -> str:
    """
    載入環境特定的配置檔案
    
    Args:
        env: 環境名稱 (development, testing, production)
             如果為 None，則從 ENVIRONMENT 環境變數讀取
    
    Returns:
        配置檔案路径
    """
    if env is None:
        env = os.getenv('ENVIRONMENT', 'development')
    
    config_dir = Path(__file__).parent / 'environments'
    config_file = config_dir / f'{env}.env'
    
    if not config_file.exists():
        # 如果找不到特定環境配置，使用開發環境配置
        config_file = config_dir / 'development.env'
        print(f"Warning: {env}.env not found, using development.env")
    
    return str(config_file)

def load_dotenv_from_environment():
    """
    根據當前環境載入對應的 .env 檔案
    """
    try:
        from dotenv import load_dotenv
        config_file = load_environment_config()
        load_dotenv(config_file)
        print(f"Loaded configuration from: {config_file}")
    except ImportError:
        print("Warning: python-dotenv not installed")
    except Exception as e:
        print(f"Error loading environment config: {e}")

if __name__ == "__main__":
    # 測試配置載入
    config_file = load_environment_config()
    print(f"Current environment config: {config_file}")
EOF

    log_success "配置載入器已建立：config/load_env.py"
}

# 建立 Docker 環境配置
create_docker_env_config() {
    log_info "建立 Docker 環境配置..."
    
    cat > "docker-compose.env" << 'EOF'
# Docker Compose 環境變數
# 這個檔案用於 docker-compose.yml 中的變數替換

# 專案名稱
COMPOSE_PROJECT_NAME=autovideo

# 環境設定
ENVIRONMENT=development

# 版本標籤
VERSION=latest

# 連接埠設定
API_GATEWAY_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432
REDIS_PORT=6379
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001

# 資料庫設定
POSTGRES_DB=autovideo
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Redis 設定
REDIS_PASSWORD=

# MinIO 設定
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# 檔案路徑
UPLOAD_VOLUME=./uploads
DATA_VOLUME=./data
LOGS_VOLUME=./logs
EOF

    log_success "Docker 環境配置已建立：docker-compose.env"
}

# 清理重複的配置檔案
cleanup_duplicate_configs() {
    log_info "清理重複的配置檔案..."
    
    # 建立備份目錄
    local backup_dir="config_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # 備份現有的 .env 檔案
    find . -name ".env*" -type f -exec cp {} "$backup_dir/" \; 2>/dev/null || true
    
    log_info "原始配置檔案已備份到：$backup_dir"
    
    # 列出將要刪除的檔案（供用戶確認）
    echo "將要清理的重複配置檔案："
    find . -name ".env*" -type f | grep -v "\.example" | grep -v "config/environments" | head -20
    
    echo
    read -p "是否清理這些重複的配置檔案？(y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 清理根目錄的重複配置檔案（保留 .env.example）
        rm -f .env .env.development .env.production .env.test .env.testing .env.template
        
        # 清理 auto_generate_video_fold6 的配置檔案
        rm -f auto_generate_video_fold6/.env*
        
        # 清理服務目錄中的 .env 檔案（但保留 .env.example）
        find services/ -name ".env" -type f -delete 2>/dev/null || true
        find auto_generate_video_fold6/services/ -name ".env" -type f -delete 2>/dev/null || true
        
        log_success "重複配置檔案清理完成"
    else
        log_info "跳過清理步驟"
    fi
    
    echo "$backup_dir" > .config_backup_path
}

# 更新 Docker Compose 檔案以使用新配置
update_docker_compose() {
    log_info "更新 Docker Compose 以使用新的配置結構..."
    
    # 備份現有的 docker-compose.yml
    [ -f "docker-compose.yml" ] && cp "docker-compose.yml" "docker-compose.yml.backup"
    
    # 檢查是否存在 auto_generate_video_fold6 的 docker-compose.yml
    if [ -f "auto_generate_video_fold6/docker-compose.yml" ]; then
        cp "auto_generate_video_fold6/docker-compose.yml" "docker-compose.yml.updated"
        
        # 更新配置檔案路徑（使用 sed 替換路徑）
        sed -i 's|auto_generate_video_fold6/||g' "docker-compose.yml.updated" 2>/dev/null || true
        sed -i 's|\.env|docker-compose.env|g' "docker-compose.yml.updated" 2>/dev/null || true
        
        log_success "Docker Compose 配置已更新：docker-compose.yml.updated"
    fi
}

# 生成配置管理文檔
generate_config_docs() {
    log_info "生成配置管理文檔..."
    
    cat > "config/README.md" << 'EOF'
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
EOF

    log_success "配置管理文檔已生成：config/README.md"
}

# 生成清理報告
generate_cleanup_report() {
    local report_file="config_cleanup_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# 配置檔案清理報告

## 清理時間
$(date)

## 清理前狀態
發現的重複配置檔案：
$(find . -name ".env*" -type f | sort)

## 新的配置結構

### 統一配置模板
- ✅ \`.env.example.unified\` - 統一的配置模板（包含所有可能的配置選項）

### 環境特定配置
- ✅ \`config/environments/development.env\` - 開發環境配置
- ✅ \`config/environments/testing.env\` - 測試環境配置  
- ✅ \`config/environments/production.env.template\` - 生產環境模板

### Docker 配置
- ✅ \`docker-compose.env\` - Docker Compose 專用環境變數

### 配置管理工具
- ✅ \`config/load_env.py\` - Python 配置載入器
- ✅ \`config/README.md\` - 配置管理文檔

## 已清理的檔案
- 根目錄重複的 .env 檔案
- auto_generate_video_fold6/ 中的 .env 檔案
- 各服務目錄中的重複 .env 檔案

## 備份位置
原始配置檔案備份：$(cat .config_backup_path 2>/dev/null || echo "未建立備份")

## 下一步行動

### 立即行動
1. 檢查新的配置結構
2. 根據需要編輯環境特定配置
3. 測試 Docker 環境是否正常
4. 更新應用程序以使用新的配置載入方式

### 應用程序更新
在你的 Python 應用中添加：
\`\`\`python
from config.load_env import load_dotenv_from_environment
load_dotenv_from_environment()
\`\`\`

### Docker 使用
\`\`\`bash
# 使用新的配置檔案
docker-compose --env-file docker-compose.env up
\`\`\`

## 注意事項
- 🔐 記得在生產環境中設定真實的 API 密鑰和密碼
- 📝 將實際的 .env 檔案加入 .gitignore
- 🔄 定期檢查和更新配置模板
EOF

    log_success "清理報告已生成：$report_file"
}

# 主函數
main() {
    log_info "開始配置檔案清理和統一化..."
    log_info "這個過程將會："
    log_info "1. 分析現有的配置檔案"
    log_info "2. 建立統一的配置模板"
    log_info "3. 建立環境特定的配置"
    log_info "4. 建立配置管理工具"
    log_info "5. 清理重複的配置檔案"
    
    echo
    read -p "是否繼續？(y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "配置清理已取消"
        exit 0
    fi
    
    # 執行清理步驟
    analyze_current_configs
    create_unified_template
    create_environment_configs
    create_config_loader
    create_docker_env_config
    cleanup_duplicate_configs
    update_docker_compose
    generate_config_docs
    generate_cleanup_report
    
    log_success "配置檔案清理和統一化完成！"
    log_info "請查看清理報告了解詳細資訊"
    log_warning "重要：請測試新的配置結構並更新應用程序"
}

# 執行主函數
main "$@"