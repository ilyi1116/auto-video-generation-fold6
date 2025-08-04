#!/bin/bash
# SSL/TLS 憑證設定與管理腳本

set -euo pipefail

# 配置變數
DOMAIN=${1:-"auto-video-system.com"}
EMAIL=${2:-"admin@auto-video-system.com"}
CERT_DIR="/etc/ssl/certs"
PRIVATE_DIR="/etc/ssl/private"
NGINX_CONF_DIR="/etc/nginx"
BACKUP_DIR="/var/backups/ssl"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# 檢查 root 權限
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "此腳本需要 root 權限執行"
    fi
}

# 安裝依賴
install_dependencies() {
    log "安裝必要依賴..."
    
    # 更新套件列表
    apt-get update
    
    # 安裝 Certbot 和相關工具
    apt-get install -y \
        certbot \
        python3-certbot-nginx \
        openssl \
        curl \
        nginx \
        cron
    
    # 安裝 Cloudflare 工具 (如果使用 Cloudflare DNS)
    pip3 install certbot-dns-cloudflare
    
    log "依賴安裝完成"
}

# 創建目錄結構
create_directories() {
    log "創建 SSL 目錄結構..."
    
    mkdir -p "$CERT_DIR"
    mkdir -p "$PRIVATE_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "/etc/letsencrypt/live"
    mkdir -p "/var/lib/letsencrypt"
    mkdir -p "/var/log/letsencrypt"
    
    # 設定正確權限
    chmod 755 "$CERT_DIR"
    chmod 700 "$PRIVATE_DIR"
    chmod 700 "$BACKUP_DIR"
    
    log "目錄創建完成"
}

# 生成 Diffie-Hellman 參數
generate_dhparam() {
    log "生成 Diffie-Hellman 參數..."
    
    if [[ ! -f "$CERT_DIR/dhparam.pem" ]]; then
        openssl dhparam -out "$CERT_DIR/dhparam.pem" 2048
        chmod 644 "$CERT_DIR/dhparam.pem"
        log "Diffie-Hellman 參數生成完成"
    else
        info "Diffie-Hellman 參數已存在"
    fi
}

# 申請 Let's Encrypt 憑證
obtain_letsencrypt_cert() {
    log "申請 Let's Encrypt SSL 憑證..."
    
    # 停止 Nginx 以釋放 80 端口
    systemctl stop nginx || true
    
    # 使用 standalone 模式申請憑證
    certbot certonly \
        --standalone \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --domains "$DOMAIN" \
        --domains "www.$DOMAIN" \
        --domains "api.$DOMAIN" \
        --non-interactive
    
    if [[ $? -eq 0 ]]; then
        log "Let's Encrypt 憑證申請成功"
    else
        error "Let's Encrypt 憑證申請失敗"
    fi
}

# 使用 DNS 驗證申請憑證 (Cloudflare)
obtain_dns_cert() {
    log "使用 DNS 驗證申請憑證..."
    
    # 檢查 Cloudflare 憑證是否存在
    if [[ ! -f "/etc/cloudflare/credentials.ini" ]]; then
        warn "Cloudflare 憑證檔案不存在，跳過 DNS 驗證"
        return 1
    fi
    
    certbot certonly \
        --dns-cloudflare \
        --dns-cloudflare-credentials /etc/cloudflare/credentials.ini \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --domains "$DOMAIN" \
        --domains "*.$DOMAIN" \
        --non-interactive
    
    if [[ $? -eq 0 ]]; then
        log "DNS 驗證憑證申請成功"
    else
        error "DNS 驗證憑證申請失敗"
    fi
}

# 生成自簽憑證 (開發環境)
generate_self_signed_cert() {
    log "生成自簽 SSL 憑證 (僅用於開發環境)..."
    
    # 創建憑證請求配置
    cat > /tmp/cert.conf <<EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = TW
ST = Taiwan
L = Taipei
O = Auto Video System
OU = IT Department
CN = $DOMAIN

[v3_req]
keyUsage = critical, digitalSignature, keyAgreement
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = www.$DOMAIN
DNS.3 = api.$DOMAIN
DNS.4 = *.local
DNS.5 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

    # 生成私鑰
    openssl genrsa -out "$PRIVATE_DIR/selfsigned.key" 2048
    
    # 生成憑證
    openssl req -new -x509 -key "$PRIVATE_DIR/selfsigned.key" \
        -out "$CERT_DIR/selfsigned.crt" \
        -days 365 \
        -config /tmp/cert.conf
    
    # 設定權限
    chmod 600 "$PRIVATE_DIR/selfsigned.key"
    chmod 644 "$CERT_DIR/selfsigned.crt"
    
    # 創建鏈結
    ln -sf "$CERT_DIR/selfsigned.crt" "$CERT_DIR/fullchain.pem"
    ln -sf "$PRIVATE_DIR/selfsigned.key" "$PRIVATE_DIR/privkey.pem"
    
    # 清理臨時檔案
    rm -f /tmp/cert.conf
    
    log "自簽憑證生成完成"
}

# 配置 Nginx SSL
configure_nginx_ssl() {
    log "配置 Nginx SSL 設定..."
    
    # 備份原始配置
    if [[ -f "$NGINX_CONF_DIR/nginx.conf" ]]; then
        cp "$NGINX_CONF_DIR/nginx.conf" "$BACKUP_DIR/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # 創建 SSL 配置片段
    cat > "$NGINX_CONF_DIR/conf.d/ssl.conf" <<EOF
# SSL 配置
ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
ssl_trusted_certificate /etc/letsencrypt/live/$DOMAIN/chain.pem;

# 包含安全配置
include /etc/nginx/security.conf;
EOF

    # 創建主要網站配置
    cat > "$NGINX_CONF_DIR/sites-available/auto-video-ssl.conf" <<EOF
# Auto Video System SSL 配置

# HTTP 重導向到 HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN api.$DOMAIN;
    
    # Let's Encrypt 驗證
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # 重導向到 HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS 主要網站
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # SSL 配置
    include /etc/nginx/conf.d/ssl.conf;
    
    # 網站根目錄
    root /var/www/auto-video/frontend/dist;
    index index.html;
    
    # SPA 路由支援
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$server_name;
        
        # 安全標頭
        proxy_set_header X-Content-Type-Options nosniff;
        proxy_set_header X-Frame-Options SAMEORIGIN;
        proxy_set_header X-XSS-Protection "1; mode=block";
    }
    
    # WebSocket 支援
    location /ws/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # 靜態檔案快取
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# API 子域名
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.$DOMAIN;
    
    # SSL 配置
    include /etc/nginx/conf.d/ssl.conf;
    
    # API 代理
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$server_name;
        
        # API 專用安全標頭
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }
}
EOF

    # 啟用網站配置
    ln -sf "$NGINX_CONF_DIR/sites-available/auto-video-ssl.conf" "$NGINX_CONF_DIR/sites-enabled/"
    
    # 移除預設配置
    rm -f "$NGINX_CONF_DIR/sites-enabled/default"
    
    log "Nginx SSL 配置完成"
}

# 設定自動更新
setup_auto_renewal() {
    log "設定 SSL 憑證自動更新..."
    
    # 創建更新腳本
    cat > /usr/local/bin/renew_ssl.sh <<EOF
#!/bin/bash
# SSL 憑證自動更新腳本

# 日誌記錄
exec > >(tee -a /var/log/ssl_renewal.log)
exec 2>&1

echo "[$(date)] 開始 SSL 憑證更新檢查"

# 更新憑證
certbot renew --quiet --no-self-upgrade

# 檢查更新結果
if [[ $? -eq 0 ]]; then
    echo "[$(date)] SSL 憑證檢查完成"
    
    # 重新載入 Nginx
    systemctl reload nginx
    echo "[$(date)] Nginx 配置重新載入"
    
    # 備份憑證
    tar -czf "$BACKUP_DIR/ssl_backup_$(date +%Y%m%d).tar.gz" \\
        /etc/letsencrypt/live/ \\
        /etc/letsencrypt/renewal/
    
    echo "[$(date)] SSL 憑證備份完成"
else
    echo "[$(date)] SSL 憑證更新失敗"
    # 發送告警 (如果配置了)
    curl -X POST "http://alertmanager:9093/api/v1/alerts" \\
        -H "Content-Type: application/json" \\
        -d '[{
            "labels": {
                "alertname": "SSLRenewalFailed",
                "severity": "critical",
                "service": "nginx"
            },
            "annotations": {
                "summary": "SSL certificate renewal failed",
                "description": "Failed to renew SSL certificates"
            }
        }]' || true
fi
EOF

    chmod +x /usr/local/bin/renew_ssl.sh
    
    # 設定 cron 任務 (每天檢查兩次)
    cat > /etc/cron.d/ssl-renewal <<EOF
# SSL 憑證自動更新
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# 每天 2:30 和 14:30 檢查更新
30 2,14 * * * root /usr/local/bin/renew_ssl.sh
EOF

    log "SSL 憑證自動更新設定完成"
}

# 安全測試
security_test() {
    log "執行 SSL 安全測試..."
    
    # 檢查憑證有效性
    if openssl x509 -in "$CERT_DIR/fullchain.pem" -text -noout > /dev/null 2>&1; then
        log "SSL 憑證格式正確"
    else
        error "SSL 憑證格式錯誤"
    fi
    
    # 檢查私鑰
    if openssl rsa -in "$PRIVATE_DIR/privkey.pem" -check -noout > /dev/null 2>&1; then
        log "私鑰格式正確"
    else
        error "私鑰格式錯誤"
    fi
    
    # 檢查憑證和私鑰匹配
    cert_hash=$(openssl x509 -noout -modulus -in "$CERT_DIR/fullchain.pem" | openssl md5)
    key_hash=$(openssl rsa -noout -modulus -in "$PRIVATE_DIR/privkey.pem" | openssl md5)
    
    if [[ "$cert_hash" == "$key_hash" ]]; then
        log "憑證和私鑰匹配"
    else
        error "憑證和私鑰不匹配"
    fi
    
    # 測試 Nginx 配置
    if nginx -t; then
        log "Nginx 配置測試通過"
    else
        error "Nginx 配置測試失敗"
    fi
    
    log "SSL 安全測試完成"
}

# 啟動服務
start_services() {
    log "啟動服務..."
    
    # 重新載入 systemd
    systemctl daemon-reload
    
    # 啟動並啟用 Nginx
    systemctl enable nginx
    systemctl restart nginx
    
    # 檢查服務狀態
    if systemctl is-active --quiet nginx; then
        log "Nginx 服務啟動成功"
    else
        error "Nginx 服務啟動失敗"
    fi
    
    # 檢查端口
    if netstat -tulpn | grep -q ":443.*LISTEN"; then
        log "HTTPS 端口 (443) 正在監聽"
    else
        warn "HTTPS 端口 (443) 未在監聽"
    fi
    
    log "服務啟動完成"
}

# 顯示摘要
show_summary() {
    log "SSL 設定摘要"
    echo "=================================="
    echo "域名: $DOMAIN"
    echo "憑證路徑: /etc/letsencrypt/live/$DOMAIN/"
    echo "Nginx 配置: $NGINX_CONF_DIR/sites-enabled/auto-video-ssl.conf"
    echo "自動更新: 已設定 (每天 2:30 和 14:30)"
    echo "安全配置: $NGINX_CONF_DIR/security.conf"
    echo "=================================="
    
    info "SSL/TLS 設定完成！"
    info "請確保 DNS 記錄指向此伺服器"
    info "可使用 SSL Labs 測試: https://www.ssllabs.com/ssltest/"
}

# 主函數
main() {
    log "開始 SSL/TLS 設定程序"
    
    check_root
    install_dependencies
    create_directories
    generate_dhparam
    
    # 選擇憑證類型
    if [[ "${SSL_TYPE:-letsencrypt}" == "selfsigned" ]]; then
        generate_self_signed_cert
    elif [[ "${SSL_TYPE:-letsencrypt}" == "dns" ]]; then
        obtain_dns_cert || obtain_letsencrypt_cert
    else
        obtain_letsencrypt_cert
    fi
    
    configure_nginx_ssl
    setup_auto_renewal
    security_test
    start_services
    show_summary
    
    log "SSL/TLS 設定程序完成"
}

# 執行主函數
main "$@"