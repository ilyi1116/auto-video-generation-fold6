# =============================================================================
# 🔐 HashiCorp Vault Kubernetes 整合配置
# =============================================================================
# 
# 此配置文件用於設置 HashiCorp Vault 與 Kubernetes 的整合
# 包含認證後端、密鑰引擎、策略配置等
#
# 使用方式:
# 1. vault policy write autovideo-prod-policy vault-kubernetes-config.hcl
# 2. vault auth enable kubernetes
# 3. vault write auth/kubernetes/config ...
#
# 創建日期: 2025-08-05
# 維護者: DevOps & Security Team
# =============================================================================

# =============================================================================
# AutoVideo 生產環境密鑰存取策略
# =============================================================================

# JWT 密鑰存取權限
path "secret/data/autovideo/prod/jwt/*" {
  capabilities = ["read"]
}

# 資料庫密鑰存取權限
path "secret/data/autovideo/prod/database/*" {
  capabilities = ["read"]
}

# AI API 密鑰存取權限
path "secret/data/autovideo/prod/ai-apis/*" {
  capabilities = ["read"]
}

# 應用程式核心密鑰存取權限
path "secret/data/autovideo/prod/app-core/*" {
  capabilities = ["read"]
}

# 支付服務密鑰存取權限
path "secret/data/autovideo/prod/payment/*" {
  capabilities = ["read"]
}

# 監控服務密鑰存取權限
path "secret/data/autovideo/prod/monitoring/*" {
  capabilities = ["read"]
}

# 動態資料庫憑證存取權限
path "database/creds/autovideo-prod-*" {
  capabilities = ["read"]
}

# PKI 憑證存取權限
path "pki/issue/autovideo-prod" {
  capabilities = ["create", "update"]
}

# Token 自檢權限
path "auth/token/lookup-self" {
  capabilities = ["read"]
}

# Token 續期權限
path "auth/token/renew-self" {
  capabilities = ["update"]
}

# =============================================================================
# Vault Kubernetes 認證配置腳本
# =============================================================================

# 此腳本用於初始化 Vault Kubernetes 認證
# 執行方式: bash setup-vault-k8s-auth.sh

#!/bin/bash
# setup-vault-k8s-auth.sh

set -euo pipefail

# 配置變數
VAULT_ADDR="${VAULT_ADDR:-https://vault.company.com:8200}"
KUBERNETES_HOST="${KUBERNETES_HOST:-https://kubernetes.default.svc:443}"
NAMESPACE="autovideo-prod"
SERVICE_ACCOUNT="vault-auth"

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. 創建 Kubernetes 服務帳戶
log_info "創建 Kubernetes 服務帳戶..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ${SERVICE_ACCOUNT}
  namespace: ${NAMESPACE}
  labels:
    app: vault-auth
    environment: production
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: vault-auth-delegator
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:auth-delegator
subjects:
- kind: ServiceAccount
  name: ${SERVICE_ACCOUNT}
  namespace: ${NAMESPACE}
EOF

# 2. 獲取服務帳戶 Token 和 CA 憑證
log_info "獲取服務帳戶 Token 和憑證..."
SECRET_NAME=$(kubectl get serviceaccount ${SERVICE_ACCOUNT} -n ${NAMESPACE} -o jsonpath='{.secrets[0].name}')
SA_JWT_TOKEN=$(kubectl get secret ${SECRET_NAME} -n ${NAMESPACE} -o jsonpath='{.data.token}' | base64 -d)
SA_CA_CRT=$(kubectl get secret ${SECRET_NAME} -n ${NAMESPACE} -o jsonpath='{.data.ca\.crt}' | base64 -d)

# 3. 啟用 Kubernetes 認證方法
log_info "啟用 Vault Kubernetes 認證方法..."
vault auth enable -path=kubernetes kubernetes || log_info "Kubernetes 認證方法已存在"

# 4. 配置 Kubernetes 認證
log_info "配置 Kubernetes 認證..."
vault write auth/kubernetes/config \
    token_reviewer_jwt="${SA_JWT_TOKEN}" \
    kubernetes_host="${KUBERNETES_HOST}" \
    kubernetes_ca_cert="${SA_CA_CRT}"

# 5. 創建生產環境策略
log_info "創建生產環境存取策略..."
vault policy write autovideo-prod-policy - <<EOF
# JWT 密鑰存取權限
path "secret/data/autovideo/prod/jwt/*" {
  capabilities = ["read"]
}

# 資料庫密鑰存取權限  
path "secret/data/autovideo/prod/database/*" {
  capabilities = ["read"]
}

# AI API 密鑰存取權限
path "secret/data/autovideo/prod/ai-apis/*" {
  capabilities = ["read"]
}

# 應用程式核心密鑰存取權限
path "secret/data/autovideo/prod/app-core/*" {
  capabilities = ["read"]
}

# 支付服務密鑰存取權限
path "secret/data/autovideo/prod/payment/*" {
  capabilities = ["read"]
}

# 監控服務密鑰存取權限
path "secret/data/autovideo/prod/monitoring/*" {
  capabilities = ["read"]
}

# 動態資料庫憑證存取權限
path "database/creds/autovideo-prod-*" {
  capabilities = ["read"]
}

# Token 管理權限
path "auth/token/lookup-self" {
  capabilities = ["read"]
}

path "auth/token/renew-self" {
  capabilities = ["update"]
}
EOF

# 6. 創建 Kubernetes 角色
log_info "創建 Kubernetes 認證角色..."
vault write auth/kubernetes/role/autovideo-prod-role \
    bound_service_account_names="autovideo-prod,api-gateway,auth-service,ai-service" \
    bound_service_account_namespaces="${NAMESPACE}" \
    policies="autovideo-prod-policy" \
    ttl=1h \
    max_ttl=4h

# 7. 創建預備環境策略和角色
log_info "創建預備環境存取策略..."
vault policy write autovideo-staging-policy - <<EOF
# 預備環境有更寬鬆的權限，包含寫入權限
path "secret/data/autovideo/staging/*" {
  capabilities = ["read", "create", "update"]
}

path "database/creds/autovideo-staging-*" {
  capabilities = ["read"]
}

path "auth/token/lookup-self" {
  capabilities = ["read"]
}

path "auth/token/renew-self" {
  capabilities = ["update"]
}
EOF

vault write auth/kubernetes/role/autovideo-staging-role \
    bound_service_account_names="autovideo-staging" \
    bound_service_account_namespaces="autovideo-staging" \
    policies="autovideo-staging-policy" \
    ttl=2h \
    max_ttl=8h

log_success "Vault Kubernetes 認證配置完成！"

# =============================================================================
# Vault Agent 配置範本
# =============================================================================

# vault-agent-config.hcl
pid_file = "/var/run/vault-agent.pid"

vault {
  address = "https://vault.company.com:8200"
  retry {
    num_retries = 3
  }
}

auto_auth {
  method "kubernetes" {
    mount_path = "auth/kubernetes"
    config = {
      role = "autovideo-prod-role"
    }
  }

  sink "file" {
    config = {
      path = "/var/run/secrets/vault-token"
      mode = 0640
    }
  }
}

# JWT 私鑰範本
template {
  source      = "/etc/vault/templates/jwt-private.pem.tpl"
  destination = "/etc/secrets/jwt-private.pem"
  perms       = 0600
  command     = "pkill -HUP api-gateway"
}

# JWT 公鑰範本
template {
  source      = "/etc/vault/templates/jwt-public.pem.tpl" 
  destination = "/etc/secrets/jwt-public.pem"
  perms       = 0644
  command     = "pkill -HUP api-gateway"
}

# 資料庫連接字串範本
template {
  source      = "/etc/vault/templates/database.env.tpl"
  destination = "/etc/secrets/database.env"
  perms       = 0600
  command     = "pkill -HUP api-gateway"
}

# 應用程式配置範本
template {
  source      = "/etc/vault/templates/app-config.env.tpl"
  destination = "/etc/secrets/app-config.env"
  perms       = 0600
  command     = "pkill -HUP api-gateway"
}

# =============================================================================
# Vault 範本文件
# =============================================================================

# /etc/vault/templates/jwt-private.pem.tpl
{{- with secret "secret/data/autovideo/prod/jwt" -}}
{{ .Data.data.private_key }}
{{- end -}}

# /etc/vault/templates/jwt-public.pem.tpl  
{{- with secret "secret/data/autovideo/prod/jwt" -}}
{{ .Data.data.public_key }}
{{- end -}}

# /etc/vault/templates/database.env.tpl
{{- with secret "secret/data/autovideo/prod/database" -}}
POSTGRES_PASSWORD={{ .Data.data.postgres_password }}
REDIS_PASSWORD={{ .Data.data.redis_password }}
POSTGRES_URL={{ .Data.data.postgres_url }}
REDIS_URL={{ .Data.data.redis_url }}
{{- end -}}

# /etc/vault/templates/app-config.env.tpl
{{- with secret "secret/data/autovideo/prod/app-core" -}}
APP_SECRET_KEY={{ .Data.data.app_secret_key }}
SESSION_SECRET={{ .Data.data.session_secret }}
ENCRYPTION_KEY={{ .Data.data.encryption_key }}
COOKIE_SECRET={{ .Data.data.cookie_secret }}
CSRF_SECRET={{ .Data.data.csrf_secret }}
{{- end -}}

{{- with secret "secret/data/autovideo/prod/ai-apis" -}}
OPENAI_API_KEY={{ .Data.data.openai_api_key }}
GEMINI_API_KEY={{ .Data.data.gemini_api_key }}
ANTHROPIC_API_KEY={{ .Data.data.anthropic_api_key }}
{{- end -}}

# =============================================================================
# 動態資料庫憑證配置
# =============================================================================

# 啟用資料庫密鑰引擎
vault secrets enable -path=database database

# 配置 PostgreSQL 連接
vault write database/config/autovideo-prod-db \
    plugin_name=postgresql-database-plugin \
    connection_url="postgresql://{{username}}:{{password}}@postgres-primary:5432/autovideo_prod?sslmode=require" \
    username="vault_admin" \
    password="REPLACE_WITH_VAULT_ADMIN_PASSWORD" \
    allowed_roles="autovideo-prod-read,autovideo-prod-write"

# 創建唯讀角色
vault write database/roles/autovideo-prod-read \
    db_name=autovideo-prod-db \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    default_ttl="1h" \
    max_ttl="24h"

# 創建讀寫角色
vault write database/roles/autovideo-prod-write \
    db_name=autovideo-prod-db \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    default_ttl="1h" \
    max_ttl="8h"

# =============================================================================
# PKI 憑證管理配置
# =============================================================================

# 啟用 PKI 密鑰引擎
vault secrets enable -path=pki pki

# 設置 PKI TTL
vault secrets tune -max-lease-ttl=87600h pki

# 生成根 CA
vault write -field=certificate pki/root/generate/internal \
    common_name="AutoVideo Production CA" \
    ttl=87600h > autovideo_ca.crt

# 配置 CA 和 CRL URLs
vault write pki/config/urls \
    issuing_certificates="https://vault.company.com:8200/v1/pki/ca" \
    crl_distribution_points="https://vault.company.com:8200/v1/pki/crl"

# 創建角色用於簽發服務憑證
vault write pki/roles/autovideo-prod \
    allowed_domains="autovideo.com,autovideo-prod.svc.cluster.local" \
    allow_subdomains=true \
    max_ttl="720h" \
    key_bits=2048 \
    key_type=rsa

# =============================================================================
# 結束配置檔案
# =============================================================================