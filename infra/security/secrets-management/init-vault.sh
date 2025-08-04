#!/bin/bash

# HashiCorp Vault 初始化腳本
# Auto Video System 密鑰管理系統

set -e

VAULT_ADDR="http://localhost:8200"
VAULT_CONFIG_DIR="/data/data/com.termux/files/home/myProject/auto_generate_video_fold6/security/secrets-management"
PROJECT_DIR="/data/data/com.termux/files/home/myProject/auto_generate_video_fold6"

echo "🔐 正在初始化 HashiCorp Vault..."

# 檢查 Vault 是否運行
if ! curl -s "$VAULT_ADDR/v1/sys/health" > /dev/null; then
    echo "❌ Vault 未運行，請先啟動 Vault 服務"
    echo "   docker run -d --name vault --cap-add=IPC_LOCK -p 8200:8200 -v $VAULT_CONFIG_DIR:/vault/config vault:latest"
    exit 1
fi

export VAULT_ADDR="$VAULT_ADDR"

# 檢查 Vault 是否已初始化
if vault status | grep -q "Initialized.*true"; then
    echo "✅ Vault 已經初始化"
    read -p "是否要重新配置 policies 和 secrets？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
else
    # 初始化 Vault
    echo "🔧 初始化 Vault..."
    vault operator init -key-shares=5 -key-threshold=3 > "$VAULT_CONFIG_DIR/vault-keys.txt"
    
    echo "✅ Vault 初始化完成"
    echo "🔑 Root token 和 unseal keys 已保存到: $VAULT_CONFIG_DIR/vault-keys.txt"
    echo "⚠️  請妥善保管這些密鑰！"
    
    # 解封 Vault
    echo "🔓 解封 Vault..."
    UNSEAL_KEY_1=$(grep "Unseal Key 1:" "$VAULT_CONFIG_DIR/vault-keys.txt" | cut -d: -f2 | tr -d ' ')
    UNSEAL_KEY_2=$(grep "Unseal Key 2:" "$VAULT_CONFIG_DIR/vault-keys.txt" | cut -d: -f2 | tr -d ' ')
    UNSEAL_KEY_3=$(grep "Unseal Key 3:" "$VAULT_CONFIG_DIR/vault-keys.txt" | cut -d: -f2 | tr -d ' ')
    
    vault operator unseal "$UNSEAL_KEY_1"
    vault operator unseal "$UNSEAL_KEY_2"
    vault operator unseal "$UNSEAL_KEY_3"
    
    # 取得 root token
    ROOT_TOKEN=$(grep "Initial Root Token:" "$VAULT_CONFIG_DIR/vault-keys.txt" | cut -d: -f2 | tr -d ' ')
    vault auth "$ROOT_TOKEN"
fi

# 如果有 root token，使用它
if [ -f "$VAULT_CONFIG_DIR/vault-keys.txt" ]; then
    ROOT_TOKEN=$(grep "Initial Root Token:" "$VAULT_CONFIG_DIR/vault-keys.txt" | cut -d: -f2 | tr -d ' ')
    vault auth "$ROOT_TOKEN" || echo "⚠️  無法使用 root token，請手動登入"
fi

echo ""
echo "📋 配置 Vault policies 和 secrets..."

# 1. 創建 policy 檔案
echo "📝 創建 Auto Video System policy..."
cat > "$VAULT_CONFIG_DIR/autovideo-policy.hcl" << 'EOF'
# Auto Video System Policy
path "secret/data/autovideo/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "secret/metadata/autovideo/*" {
  capabilities = ["list"]
}

path "database/creds/autovideo-role" {
  capabilities = ["read"]
}

path "aws/creds/autovideo-s3" {
  capabilities = ["read"]
}

path "auth/token/lookup-self" {
  capabilities = ["read"]
}

path "auth/token/renew-self" {
  capabilities = ["update"]
}
EOF

vault policy write autovideo-policy "$VAULT_CONFIG_DIR/autovideo-policy.hcl"

# 2. 啟用必要的 secrets engines
echo "🔧 啟用 secrets engines..."

# KV v2 for application secrets
vault secrets enable -path=secret kv-v2

# Database secrets engine
vault secrets enable database

# AWS secrets engine
vault secrets enable aws

# 3. 配置數據庫連接
echo "🗃️ 配置數據庫連接..."
vault write database/config/postgres \
    plugin_name=postgresql-database-plugin \
    connection_url="postgresql://{{username}}:{{password}}@postgres:5432/postgres?sslmode=disable" \
    allowed_roles="autovideo-role" \
    username="postgres" \
    password="$(grep POSTGRES_PASSWORD $PROJECT_DIR/.env | cut -d= -f2)"

# 配置數據庫角色
vault write database/roles/autovideo-role \
    db_name=postgres \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    default_ttl="1h" \
    max_ttl="24h"

# 4. 儲存應用程式 secrets
echo "🔐 儲存應用程式 secrets..."

# JWT secrets
vault kv put secret/autovideo/auth \
    jwt_secret="$(openssl rand -base64 32)" \
    jwt_algorithm="HS256" \
    jwt_expiration="86400"

# API keys
vault kv put secret/autovideo/external-apis \
    gemini_api_key="$(grep GEMINI_API_KEY $PROJECT_DIR/.env | cut -d= -f2)" \
    openai_api_key="$(grep OPENAI_API_KEY $PROJECT_DIR/.env | cut -d= -f2)" \
    suno_api_key="$(grep SUNO_API_KEY $PROJECT_DIR/.env | cut -d= -f2)" \
    tiktok_client_id="$(grep TIKTOK_CLIENT_ID $PROJECT_DIR/.env | cut -d= -f2)" \
    tiktok_client_secret="$(grep TIKTOK_CLIENT_SECRET $PROJECT_DIR/.env | cut -d= -f2)" \
    youtube_client_id="$(grep YOUTUBE_CLIENT_ID $PROJECT_DIR/.env | cut -d= -f2)" \
    youtube_client_secret="$(grep YOUTUBE_CLIENT_SECRET $PROJECT_DIR/.env | cut -d= -f2)"

# Redis configuration
vault kv put secret/autovideo/redis \
    host="redis" \
    port="6379" \
    password="$(grep REDIS_PASSWORD $PROJECT_DIR/.env | cut -d= -f2)"

# S3/MinIO configuration
vault kv put secret/autovideo/storage \
    s3_access_key="$(grep AWS_ACCESS_KEY_ID $PROJECT_DIR/.env | cut -d= -f2)" \
    s3_secret_key="$(grep AWS_SECRET_ACCESS_KEY $PROJECT_DIR/.env | cut -d= -f2)" \
    s3_bucket="$(grep S3_BUCKET $PROJECT_DIR/.env | cut -d= -f2)" \
    s3_region="$(grep AWS_REGION $PROJECT_DIR/.env | cut -d= -f2)"

# 5. 創建應用程式 token
echo "🎫 創建應用程式 token..."
AUTOVIDEO_TOKEN=$(vault write -field=token auth/token/create \
    policies="autovideo-policy" \
    ttl=768h \
    renewable=true \
    display_name="autovideo-system")

echo "$AUTOVIDEO_TOKEN" > "$VAULT_CONFIG_DIR/autovideo-token.txt"

# 6. 創建管理腳本
echo "📜 創建管理腳本..."
cat > "$VAULT_CONFIG_DIR/renew-token.sh" << 'EOF'
#!/bin/bash
# Token 續期腳本

VAULT_ADDR="http://localhost:8200"
TOKEN_FILE="/vault/config/autovideo-token.txt"

if [ -f "$TOKEN_FILE" ]; then
    export VAULT_TOKEN=$(cat "$TOKEN_FILE")
    vault auth "$VAULT_TOKEN"
    vault token renew
    echo "✅ Token 已續期"
else
    echo "❌ Token 檔案不存在"
    exit 1
fi
EOF

chmod +x "$VAULT_CONFIG_DIR/renew-token.sh"

# 7. 創建備份腳本
cat > "$VAULT_CONFIG_DIR/backup-vault.sh" << 'EOF'
#!/bin/bash
# Vault 備份腳本

VAULT_ADDR="http://localhost:8200"
BACKUP_DIR="/vault/backups/$(date +%Y%m%d_%H%M%S)"
TOKEN_FILE="/vault/config/autovideo-token.txt"

mkdir -p "$BACKUP_DIR"

if [ -f "$TOKEN_FILE" ]; then
    export VAULT_TOKEN=$(cat "$TOKEN_FILE")
    
    # 備份所有 secrets
    vault kv get -format=json secret/autovideo/auth > "$BACKUP_DIR/auth.json"
    vault kv get -format=json secret/autovideo/external-apis > "$BACKUP_DIR/external-apis.json"
    vault kv get -format=json secret/autovideo/redis > "$BACKUP_DIR/redis.json"
    vault kv get -format=json secret/autovideo/storage > "$BACKUP_DIR/storage.json"
    
    # 備份 policies
    vault policy read autovideo-policy > "$BACKUP_DIR/autovideo-policy.hcl"
    
    echo "✅ Vault 備份完成: $BACKUP_DIR"
else
    echo "❌ Token 檔案不存在"
    exit 1
fi
EOF

chmod +x "$VAULT_CONFIG_DIR/backup-vault.sh"

echo ""
echo "✅ Vault 初始化和配置完成！"
echo ""
echo "📊 配置摘要："
echo "   🏠 Vault UI: $VAULT_ADDR/ui"
echo "   🎫 應用程式 Token: $VAULT_CONFIG_DIR/autovideo-token.txt"
echo "   🔑 Root Keys: $VAULT_CONFIG_DIR/vault-keys.txt"
echo "   📋 Policy: autovideo-policy"
echo ""
echo "🔧 管理指令："
echo "   - 續期 token: $VAULT_CONFIG_DIR/renew-token.sh"
echo "   - 備份 secrets: $VAULT_CONFIG_DIR/backup-vault.sh"
echo "   - 檢查狀態: vault status"
echo ""
echo "📝 使用範例："
echo "   # 讀取 secret"
echo "   vault kv get secret/autovideo/auth"
echo ""
echo "   # 更新 secret"
echo "   vault kv put secret/autovideo/auth jwt_secret=新密鑰"
echo ""
echo "⚠️  安全提醒："
echo "   - 定期備份 Vault 數據"
echo "   - 定期輪換 secrets"
echo "   - 監控 Vault 存取日誌"
echo "   - 妥善保管 unseal keys"
echo ""