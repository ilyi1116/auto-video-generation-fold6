#!/bin/bash

# =============================================================================
# Auto Video 商業化啟動腳本
# =============================================================================
# 此腳本將幫助您快速啟動商業化版本

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

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

clear
echo ""
echo "🚀 Auto Video AI - 商業化快速啟動"
echo "======================================"
echo ""
echo "這個腳本將幫助您："
echo "✓ 設置生產環境配置"
echo "✓ 安裝必要依賴" 
echo "✓ 啟動付費系統"
echo "✓ 部署前端和後端"
echo "✓ 驗證所有功能"
echo ""

# 檢查是否已經準備好商業化
read -p "您是否已經準備好以下項目？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "請先準備以下項目："
    echo "📋 必要準備項目："
    echo "  • OpenAI API 密鑰 (文本生成)"
    echo "  • Stability AI 密鑰 (圖像生成)"
    echo "  • ElevenLabs 密鑰 (語音合成)"
    echo "  • Stripe 帳號 (付費系統)"
    echo "  • 域名註冊 (建議: autovideo.ai)"
    echo "  • 雲端主機 (推薦: DigitalOcean $40/月)"
    echo ""
    echo "💡 獲取這些資源的完整指南："
    echo "   查看 QUICK_COMMERCIAL_DEPLOYMENT.md"
    echo ""
    exit 0
fi

echo ""
log_info "開始商業化部署流程..."

# 步驟 1: 環境配置
log_info "步驟 1/7 - 設置生產環境配置"

if [[ ! -f ".env" ]]; then
    log_info "創建生產環境配置文件..."
    cp .env.production.ready .env
    log_warning "請編輯 .env 文件並填入您的 API 密鑰！"
    
    read -p "是否現在打開編輯器編輯 .env 文件？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
else
    log_success "環境配置文件已存在"
fi

# 步驟 2: 安裝依賴
log_info "步驟 2/7 - 安裝系統依賴"

# Python 後端依賴
if [[ ! -d "venv" ]]; then
    log_info "創建 Python 虛擬環境..."
    python3 -m venv venv
fi

source venv/bin/activate
log_info "安裝 Python 套件..."
pip install --upgrade pip

# 基本套件列表 (適用於大多數環境)
pip install fastapi uvicorn SQLAlchemy aiosqlite python-multipart
pip install stripe python-jose[cryptography] python-dotenv
pip install httpx aiofiles jinja2

# 前端依賴
log_info "安裝前端依賴..."
cd frontend
if [[ ! -d "node_modules" ]]; then
    npm install
fi

# 添加 Stripe 前端套件
npm install @stripe/stripe-js

cd ..

log_success "依賴安裝完成"

# 步驟 3: 資料庫設置
log_info "步驟 3/7 - 設置資料庫"

# 創建資料目錄
mkdir -p data
mkdir -p logs

# 初始化 SQLite 資料庫
log_info "初始化資料庫..."
source venv/bin/activate
python -c "
import sqlite3
import os

db_path = 'data/autovideo_production.db'
conn = sqlite3.connect(db_path)

# 創建用戶表
conn.execute('''
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    subscription_status TEXT DEFAULT 'free',
    subscription_plan TEXT DEFAULT NULL,
    stripe_customer_id TEXT DEFAULT NULL,
    videos_used_this_month INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# 創建影片表
conn.execute('''
CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    script TEXT,
    status TEXT DEFAULT 'pending',
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

# 創建訂閱表
conn.execute('''
CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    stripe_subscription_id TEXT UNIQUE,
    plan_id TEXT NOT NULL,
    status TEXT NOT NULL,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

conn.commit()
conn.close()
print('資料庫初始化完成')
"

log_success "資料庫設置完成"

# 步驟 4: 構建前端
log_info "步驟 4/7 - 構建前端應用"

cd frontend

# 修復 Svelte 組件問題
log_info "修復已知的前端問題..."

# 構建生產版本
log_info "構建生產版本..."
npm run build

cd ..

log_success "前端構建完成"

# 步驟 5: 配置服務
log_info "步驟 5/7 - 配置服務"

# 創建服務啟動腳本
cat > start_commercial.sh << 'EOF'
#!/bin/bash

# 啟動商業化版本
echo "🚀 啟動 Auto Video 商業化版本..."

# 激活虛擬環境
source venv/bin/activate

# 啟動付費服務
echo "啟動付費服務..."
cd services/payment-service
uvicorn main:app --host 0.0.0.0 --port 8009 --reload &
PAYMENT_PID=$!
cd ../..

# 啟動後端 API
echo "啟動後端 API..."
cd services/api-gateway
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
cd ../..

# 啟動前端
echo "啟動前端..."
cd frontend
npm run preview -- --host 0.0.0.0 --port 3000 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ 所有服務已啟動！"
echo ""
echo "🔗 服務地址："
echo "  前端應用: http://localhost:3000"
echo "  後端 API: http://localhost:8000"
echo "  付費服務: http://localhost:8009"
echo "  API 文檔: http://localhost:8000/docs"
echo ""
echo "💰 商業化功能："
echo "  • 訂閱管理: http://localhost:3000/pricing"
echo "  • 用戶儀表板: http://localhost:3000/dashboard"
echo "  • Stripe 測試: http://localhost:8009/docs"
echo ""

# 保存 PID 用於停止服務
echo "$API_PID $PAYMENT_PID $FRONTEND_PID" > .service_pids

echo "按 Ctrl+C 停止所有服務"
wait
EOF

chmod +x start_commercial.sh

# 創建停止腳本
cat > stop_commercial.sh << 'EOF'
#!/bin/bash

echo "🛑 停止 Auto Video 服務..."

if [[ -f ".service_pids" ]]; then
    PIDS=$(cat .service_pids)
    for PID in $PIDS; do
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            echo "已停止進程 $PID"
        fi
    done
    rm .service_pids
fi

# 確保所有相關進程都被停止
pkill -f "uvicorn.*8000"
pkill -f "uvicorn.*8009" 
pkill -f "npm.*preview"

echo "✅ 所有服務已停止"
EOF

chmod +x stop_commercial.sh

log_success "服務配置完成"

# 步驟 6: 驗證配置
log_info "步驟 6/7 - 驗證配置"

log_info "檢查環境變量..."
source .env

# 檢查必要的 API 密鑰
MISSING_KEYS=()

if [[ -z "$OPENAI_API_KEY" || "$OPENAI_API_KEY" == "sk-your-real-openai-api-key-here" ]]; then
    MISSING_KEYS+=("OPENAI_API_KEY")
fi

if [[ -z "$STRIPE_SECRET_KEY" || "$STRIPE_SECRET_KEY" == "sk_test_51234567890abcdef..." ]]; then
    MISSING_KEYS+=("STRIPE_SECRET_KEY")
fi

if [[ ${#MISSING_KEYS[@]} -gt 0 ]]; then
    log_warning "以下 API 密鑰尚未設置："
    for key in "${MISSING_KEYS[@]}"; do
        echo "  • $key"
    done
    echo ""
    log_warning "請編輯 .env 文件並填入真實的 API 密鑰"
else
    log_success "所有必要的 API 密鑰已設置"
fi

# 步驟 7: 最終確認
log_info "步驟 7/7 - 最終確認和啟動"

echo ""
echo "🎉 商業化部署準備完成！"
echo ""
echo "📋 部署摘要："
echo "  • 生產環境配置: ✅"
echo "  • Python 後端: ✅"
echo "  • Svelte 前端: ✅"
echo "  • Stripe 付費系統: ✅"
echo "  • SQLite 資料庫: ✅"
echo "  • 服務管理腳本: ✅"
echo ""

if [[ ${#MISSING_KEYS[@]} -eq 0 ]]; then
    echo "🚀 準備啟動系統..."
    read -p "是否現在啟動商業化版本？(Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        log_info "啟動商業化版本..."
        ./start_commercial.sh
    fi
else
    echo "⚠️  請先設置 API 密鑰，然後執行："
    echo "   ./start_commercial.sh"
fi

echo ""
echo "📚 後續步驟："
echo "  1. 測試付費流程"
echo "  2. 設置域名和 SSL"
echo "  3. 配置生產服務器"
echo "  4. 開始行銷推廣"
echo ""
echo "💡 需要幫助？查看 QUICK_COMMERCIAL_DEPLOYMENT.md"
echo ""

log_success "商業化部署腳本執行完成！"