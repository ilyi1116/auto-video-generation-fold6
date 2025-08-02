#!/bin/bash

# =============================================================================
# 🔐 生產環境密鑰生成腳本
# =============================================================================
# 
# 此腳本生成生產環境所需的所有密鑰和配置
# 使用方式: ./scripts/generate_production_keys.sh
#
# 生成日期: 2025-08-02
# 最後更新: Claude Code Assistant
# =============================================================================

set -euo pipefail

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查依賴
check_dependencies() {
    log_info "檢查系統依賴..."
    
    for cmd in openssl head base64; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "缺少必要命令: $cmd"
            exit 1
        fi
    done
    
    log_success "所有依賴檢查通過"
}

# 創建密鑰目錄
create_key_directories() {
    log_info "創建密鑰目錄..."
    
    mkdir -p keys/production
    mkdir -p keys/staging
    mkdir -p keys/development
    
    # 設置目錄權限
    chmod 700 keys/
    chmod 700 keys/production/
    chmod 700 keys/staging/
    chmod 700 keys/development/
    
    log_success "密鑰目錄創建完成"
}

# 生成 RSA 密鑰對 (JWT)
generate_rsa_keys() {
    log_info "生成 RSA 密鑰對 (JWT RS256)..."
    
    # 生產環境
    openssl genrsa -out keys/production/jwt-private.pem 2048
    openssl rsa -in keys/production/jwt-private.pem -pubout -out keys/production/jwt-public.pem
    
    # 設置權限
    chmod 600 keys/production/jwt-private.pem
    chmod 644 keys/production/jwt-public.pem
    
    # 預備環境
    openssl genrsa -out keys/staging/jwt-private.pem 2048
    openssl rsa -in keys/staging/jwt-private.pem -pubout -out keys/staging/jwt-public.pem
    
    chmod 600 keys/staging/jwt-private.pem
    chmod 644 keys/staging/jwt-public.pem
    
    log_success "RSA 密鑰對生成完成"
}

# 生成隨機密鑰
generate_random_keys() {
    log_info "生成隨機密鑰..."
    
    # 生產環境密鑰文件
    cat > keys/production/secrets.env << EOF
# =============================================================================
# 🔐 生產環境密鑰 - $(date)
# =============================================================================
# 警告：此文件包含敏感資訊，請妥善保管！

# JWT 密鑰 (RSA)
JWT_SECRET_KEY="\$(cat keys/production/jwt-private.pem)"
JWT_PUBLIC_KEY="\$(cat keys/production/jwt-public.pem)"

# 資料庫密碼 (32位)
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

# 應用程式密鑰
APP_SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/")
SESSION_SECRET=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
ENCRYPTION_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

# API 密鑰佔位符 (需要手動設置實際值)
OPENAI_API_KEY=sk-your-openai-key-here
GEMINI_API_KEY=your-gemini-key-here
SUNO_API_KEY=your-suno-key-here
STABLE_DIFFUSION_API_KEY=your-sd-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here

# AWS 憑證 (需要手動設置)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key

# Stripe 支付 (需要手動設置)
STRIPE_SECRET_KEY=sk_live_your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# SMTP 配置 (需要手動設置)
SMTP_PASSWORD=your-smtp-password

# Sentry DSN (需要手動設置)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# =============================================================================
EOF
    
    # 設置權限
    chmod 600 keys/production/secrets.env
    
    log_success "隨機密鑰生成完成"
}

# 生成預備環境密鑰
generate_staging_keys() {
    log_info "生成預備環境密鑰..."
    
    cat > keys/staging/secrets.env << EOF
# =============================================================================
# 🔐 預備環境密鑰 - $(date)
# =============================================================================

# JWT 密鑰 (RSA)
JWT_SECRET_KEY="\$(cat keys/staging/jwt-private.pem)"
JWT_PUBLIC_KEY="\$(cat keys/staging/jwt-public.pem)"

# 資料庫密碼
POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
REDIS_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)

# 應用程式密鑰
APP_SECRET_KEY=$(openssl rand -base64 48 | tr -d "=+/")
SESSION_SECRET=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
ENCRYPTION_KEY=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)

# 測試 API 密鑰 (使用測試環境)
OPENAI_API_KEY=sk-test-your-openai-test-key
STRIPE_SECRET_KEY=sk_test_your-stripe-test-key

# =============================================================================
EOF
    
    chmod 600 keys/staging/secrets.env
    
    log_success "預備環境密鑰生成完成"
}

# 創建密鑰使用說明
create_key_documentation() {
    log_info "創建密鑰使用說明..."
    
    cat > keys/README.md << 'EOF'
# 🔐 密鑰管理指南

## 目錄結構
```
keys/
├── production/          # 生產環境密鑰
│   ├── jwt-private.pem  # JWT RSA 私鑰
│   ├── jwt-public.pem   # JWT RSA 公鑰
│   └── secrets.env      # 生產環境密鑰文件
├── staging/             # 預備環境密鑰
│   ├── jwt-private.pem  # JWT RSA 私鑰
│   ├── jwt-public.pem   # JWT RSA 公鑰
│   └── secrets.env      # 預備環境密鑰文件
└── development/         # 開發環境密鑰
```

## 🚀 使用方式

### 1. 載入生產環境密鑰
```bash
# 方式一：直接載入
source keys/production/secrets.env

# 方式二：透過 Docker Compose
docker-compose --env-file keys/production/secrets.env up
```

### 2. 設置 JWT 密鑰
```bash
# 設置環境變數
export JWT_SECRET_KEY="$(cat keys/production/jwt-private.pem)"
export JWT_PUBLIC_KEY="$(cat keys/production/jwt-public.pem)"
```

### 3. Kubernetes 密鑰設置
```bash
# 創建 JWT 密鑰 Secret
kubectl create secret generic jwt-keys \
    --from-file=private-key=keys/production/jwt-private.pem \
    --from-file=public-key=keys/production/jwt-public.pem

# 創建應用密鑰 Secret
kubectl create secret generic app-secrets \
    --from-env-file=keys/production/secrets.env
```

## 🔒 安全最佳實踐

### 1. 權限設置
```bash
# 確保密鑰文件權限正確
chmod 600 keys/production/*.pem
chmod 600 keys/production/secrets.env
```

### 2. 版本控制
- ❌ 絕對不要將 keys/ 目錄提交到 Git
- ✅ 確保 .gitignore 包含 keys/ 目錄
- ✅ 使用密鑰管理服務 (AWS Secrets Manager, HashiCorp Vault)

### 3. 密鑰輪換
```bash
# 每 90 天輪換一次密鑰
./scripts/generate_production_keys.sh

# 更新部署環境
kubectl delete secret jwt-keys app-secrets
kubectl create secret generic jwt-keys --from-file=...
```

## 🔧 故障排除

### JWT 密鑰問題
```bash
# 驗證私鑰格式
openssl rsa -in keys/production/jwt-private.pem -text -noout

# 驗證公鑰格式
openssl rsa -pubin -in keys/production/jwt-public.pem -text -noout

# 驗證密鑰配對
diff <(openssl rsa -in keys/production/jwt-private.pem -pubout) keys/production/jwt-public.pem
```

### 環境變數檢查
```bash
# 檢查必要的環境變數
printenv | grep -E "(JWT|POSTGRES|REDIS|OPENAI)" | sort
```

## 📞 支援聯絡

如有密鑰管理相關問題，請聯絡：
- 安全團隊: security@autovideo.com
- DevOps 團隊: devops@autovideo.com
EOF
    
    log_success "密鑰使用說明創建完成"
}

# 創建 .gitignore 規則
update_gitignore() {
    log_info "更新 .gitignore..."
    
    if ! grep -q "^keys/" .gitignore 2>/dev/null; then
        echo "" >> .gitignore
        echo "# 🔐 密鑰文件 - 絕對不要提交" >> .gitignore
        echo "keys/" >> .gitignore
        echo "*.pem" >> .gitignore
        echo "secrets.env" >> .gitignore
        echo ".env.production.local" >> .gitignore
        log_success ".gitignore 更新完成"
    else
        log_info ".gitignore 已包含密鑰排除規則"
    fi
}

# 顯示總結
show_summary() {
    echo ""
    echo "==============================================="
    log_success "🎉 生產環境密鑰生成完成！"
    echo "==============================================="
    echo ""
    echo "📁 生成的文件："
    echo "   • keys/production/jwt-private.pem"
    echo "   • keys/production/jwt-public.pem"  
    echo "   • keys/production/secrets.env"
    echo "   • keys/staging/jwt-private.pem"
    echo "   • keys/staging/jwt-public.pem"
    echo "   • keys/staging/secrets.env"
    echo "   • keys/README.md"
    echo ""
    echo "🔧 下一步："
    echo "   1. 編輯 keys/production/secrets.env"
    echo "   2. 設置實際的 API 密鑰值"
    echo "   3. 部署到密鑰管理服務"
    echo "   4. 更新 CI/CD 管道配置"
    echo ""
    log_warning "⚠️  請務必妥善保管這些密鑰文件！"
    echo ""
}

# 主函數
main() {
    echo "==============================================="
    echo "🔐 生產環境密鑰生成器"
    echo "==============================================="
    echo ""
    
    check_dependencies
    create_key_directories
    generate_rsa_keys
    generate_random_keys
    generate_staging_keys
    create_key_documentation
    update_gitignore
    show_summary
}

# 執行主函數
main "$@"