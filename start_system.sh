#!/bin/bash

# Auto Video Generation System - 快速啟動腳本
# 快速啟動所有核心服務

echo "🚀 Starting Auto Video Generation System..."
echo "=" * 50

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# 檢查端口是否被占用
check_port() {
    local port=$1
    local service=$2
    if lsof -i :$port > /dev/null 2>&1; then
        log_warning "$service port $port is already in use"
        return 1
    fi
    return 0
}

# 等待服務啟動
wait_for_service() {
    local url=$1
    local service=$2
    local max_attempts=30
    local attempt=1
    
    log_info "Waiting for $service to start..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            log_success "$service is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    log_error "$service failed to start after ${max_attempts}s"
    return 1
}

# 創建必要目錄
log_info "Creating necessary directories..."
mkdir -p uploads/dev
mkdir -p logs
log_success "Directories created"

# 檢查環境文件
if [ ! -f ".env.local" ]; then
    log_warning ".env.local not found, creating default..."
    cat > .env.local << 'EOF'
# 開發環境配置
ENVIRONMENT=development
DATABASE_URL=sqlite:///./auto_video_dev.db

# AI API Keys (請填入真實的API Key)
OPENAI_API_KEY=your-openai-api-key-here
DEEPSEEK_API_KEY=your-deepseek-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here

# JWT密鑰 (生產環境請使用更安全的密鑰)
JWT_SECRET_KEY=development-jwt-secret-key-change-in-production-32chars

# 服務端口配置
API_GATEWAY_PORT=8000
AI_SERVICE_PORT=8005
FRONTEND_PORT=5173
EOF
    log_success "Default .env.local created"
fi

# 載入環境變數
export $(grep -v '^#' .env.local | xargs) 2>/dev/null

log_info "Starting services..."

# 1. 啟動 API Gateway
log_info "Starting API Gateway (port 8000)..."
if check_port 8000 "API Gateway"; then
    python3 api_gateway_simple.py > logs/api_gateway.log 2>&1 &
    API_GATEWAY_PID=$!
    echo $API_GATEWAY_PID > .api_gateway.pid
    
    if wait_for_service "http://localhost:8000/health" "API Gateway"; then
        log_success "API Gateway started successfully"
    else
        log_error "API Gateway failed to start"
        exit 1
    fi
else
    log_warning "API Gateway may already be running"
fi

# 2. 啟動 AI Service
log_info "Starting AI Service (port 8005)..."
if check_port 8005 "AI Service"; then
    cd src/services/ai-service
    python3 main_simple.py > ../../../logs/ai_service.log 2>&1 &
    AI_SERVICE_PID=$!
    echo $AI_SERVICE_PID > ../../../.ai_service.pid
    cd ../../..
    
    if wait_for_service "http://localhost:8005/health" "AI Service"; then
        log_success "AI Service started successfully"
    else
        log_error "AI Service failed to start"
        exit 1
    fi
else
    log_warning "AI Service may already be running"
fi

# 3. 啟動 Frontend
log_info "Starting Frontend (port 5173)..."
if check_port 5173 "Frontend"; then
    cd src/frontend
    npm run dev > ../../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../../.frontend.pid
    cd ../..
    
    # Frontend 需要更長時間啟動
    sleep 3
    if wait_for_service "http://localhost:5173" "Frontend"; then
        log_success "Frontend started successfully"
    else
        log_error "Frontend failed to start"
        exit 1
    fi
else
    log_warning "Frontend may already be running"
fi

echo ""
echo "🎉 System startup complete!"
echo "=" * 50
echo ""
echo "📱 服務地址:"
echo "   🌐 前端應用: http://localhost:5173"
echo "   🛠️  API Gateway: http://localhost:8000"
echo "   🤖 AI Service: http://localhost:8005"
echo "   📖 API 文檔: http://localhost:8000/docs"
echo ""
echo "🔍 健康檢查:"
echo "   API Gateway: http://localhost:8000/health"
echo "   AI Service: http://localhost:8005/health"
echo ""
echo "📋 管理指令:"
echo "   停止系統: ./stop_system.sh"
echo "   查看日誌: tail -f logs/*.log"
echo "   系統狀態: ./status_system.sh"
echo ""
echo "🔑 AI API Keys 狀態:"
OPENAI_STATUS=$([ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "your-openai-api-key-here" ] && echo "✅ 已配置" || echo "❌ 未配置")
DEEPSEEK_STATUS=$([ -n "$DEEPSEEK_API_KEY" ] && [ "$DEEPSEEK_API_KEY" != "your-deepseek-api-key-here" ] && echo "✅ 已配置" || echo "❌ 未配置")
GEMINI_STATUS=$([ -n "$GEMINI_API_KEY" ] && [ "$GEMINI_API_KEY" != "your-gemini-api-key-here" ] && echo "✅ 已配置" || echo "❌ 未配置")

echo "   OpenAI: $OPENAI_STATUS"
echo "   DeepSeek: $DEEPSEEK_STATUS" 
echo "   Gemini: $GEMINI_STATUS"

if [[ "$OPENAI_STATUS" == "❌"* && "$DEEPSEEK_STATUS" == "❌"* && "$GEMINI_STATUS" == "❌"* ]]; then
    echo ""
    echo "⚠️  注意: 所有 AI API Keys 都未配置"
    echo "   系統將使用模板回應，功能受限"
    echo "   請在 .env.local 中配置真實的 API Keys"
fi

echo ""
echo "🚀 系統已就緒！可以開始使用 Auto Video Generation Platform"

# 保存PID以便管理
cat > .system_pids << EOF
API_GATEWAY_PID=$API_GATEWAY_PID
AI_SERVICE_PID=$AI_SERVICE_PID  
FRONTEND_PID=$FRONTEND_PID
EOF

# 設置信號處理
trap 'echo ""; log_info "Shutting down system..."; ./stop_system.sh; exit 0' INT TERM

# 保持腳本運行
echo ""
log_info "System is running. Press Ctrl+C to stop all services."
echo "You can also run './stop_system.sh' in another terminal to stop the system."

# 等待用戶中斷
while true; do
    sleep 1
done