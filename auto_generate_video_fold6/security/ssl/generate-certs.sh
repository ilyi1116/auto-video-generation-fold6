#!/bin/bash

# SSL 證書生成腳本
# Auto Video System Self-Signed Certificate Generator

set -e

DOMAIN="autovideo.local"
CERT_DIR="/data/data/com.termux/files/home/myProject/auto_generate_video_fold6/security/ssl"
NGINX_SSL_DIR="/etc/nginx/ssl"

echo "🔐 正在生成 SSL 證書..."

# 創建證書目錄
mkdir -p "$CERT_DIR"
mkdir -p "$NGINX_SSL_DIR" 2>/dev/null || true

# 生成私鑰
echo "📝 生成私鑰..."
openssl genrsa -out "$CERT_DIR/autovideo.key" 2048

# 生成證書簽名請求配置
cat > "$CERT_DIR/cert.conf" << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=TW
ST=Taiwan
L=Taipei
O=Auto Video System
OU=Development
CN=$DOMAIN

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = admin.$DOMAIN
DNS.3 = api.$DOMAIN
DNS.4 = localhost
IP.1 = 127.0.0.1
IP.2 = 10.0.0.1
EOF

# 生成證書簽名請求
echo "📄 生成證書簽名請求..."
openssl req -new -key "$CERT_DIR/autovideo.key" -out "$CERT_DIR/autovideo.csr" -config "$CERT_DIR/cert.conf"

# 生成自簽證書
echo "🔏 生成自簽證書..."
openssl x509 -req -in "$CERT_DIR/autovideo.csr" -signkey "$CERT_DIR/autovideo.key" \
    -out "$CERT_DIR/autovideo.crt" -days 365 -extensions v3_req -extfile "$CERT_DIR/cert.conf"

# 生成 DH 參數（增強安全性）
echo "🔑 生成 DH 參數..."
openssl dhparam -out "$CERT_DIR/dhparam.pem" 2048

# 設定正確的權限
chmod 600 "$CERT_DIR/autovideo.key"
chmod 644 "$CERT_DIR/autovideo.crt"
chmod 644 "$CERT_DIR/dhparam.pem"

# 複製到 Nginx 目錄（如果可以）
if [ -w "/etc/nginx/ssl" ] 2>/dev/null; then
    cp "$CERT_DIR/autovideo.crt" "$NGINX_SSL_DIR/"
    cp "$CERT_DIR/autovideo.key" "$NGINX_SSL_DIR/"
    cp "$CERT_DIR/dhparam.pem" "$NGINX_SSL_DIR/"
    echo "✅ 證書已複製到 Nginx SSL 目錄"
fi

# 驗證證書
echo "🔍 驗證證書..."
openssl x509 -in "$CERT_DIR/autovideo.crt" -text -noout | grep -A 1 "Subject:"
openssl x509 -in "$CERT_DIR/autovideo.crt" -text -noout | grep -A 3 "X509v3 Subject Alternative Name:"

echo ""
echo "✅ SSL 證書生成完成！"
echo ""
echo "📁 證書位置："
echo "   - 證書: $CERT_DIR/autovideo.crt"
echo "   - 私鑰: $CERT_DIR/autovideo.key"
echo "   - DH 參數: $CERT_DIR/dhparam.pem"
echo ""
echo "🔧 使用說明："
echo "   1. 將以下內容添加到 /etc/hosts："
echo "      127.0.0.1 autovideo.local"
echo "      127.0.0.1 admin.autovideo.local"
echo "      127.0.0.1 api.autovideo.local"
echo ""
echo "   2. 在瀏覽器中接受自簽證書"
echo "   3. 訪問 https://autovideo.local"
echo ""
echo "⚠️  注意：這是自簽證書，僅用於開發環境"
echo "   生產環境請使用 Let's Encrypt 或購買正式證書"
echo ""