#!/bin/bash

# MVP 啟動腳本 - 啟動核心服務進行開發測試
# Auto Video Generation MVP Startup Script

echo "🚀 Starting Auto Video Generation MVP..."

# 設置環境變數
export $(grep -v '^#' .env.local | xargs)

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

# 檢查Python版本
check_python() {
    log_info "檢查 Python 版本..."
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version | cut -d' ' -f2)
        log_success "Python版本: $python_version"
    else
        log_error "Python3 未找到，請先安裝 Python 3.9+"
        exit 1
    fi
}

# 檢查Node.js版本
check_node() {
    log_info "檢查 Node.js 版本..."
    if command -v node &> /dev/null; then
        node_version=$(node --version)
        log_success "Node.js版本: $node_version"
    else
        log_error "Node.js 未找到，請先安裝 Node.js 18+"
        exit 1
    fi
}

# 安裝Python依賴
install_python_deps() {
    log_info "安裝 Python 依賴..."
    if [ -f "pyproject.toml" ]; then
        pip3 install -e . --quiet
        log_success "Python 依賴安裝完成"
    else
        log_warning "pyproject.toml 不存在，跳過Python依賴安裝"
    fi
}

# 安裝前端依賴  
install_frontend_deps() {
    log_info "安裝前端依賴..."
    if [ -d "src/frontend" ]; then
        cd src/frontend
        npm install --silent
        log_success "前端依賴安裝完成"
        cd ../..
    else
        log_warning "前端目錄不存在，跳過前端依賴安裝"
    fi
}

# 創建必要目錄
create_directories() {
    log_info "創建必要目錄..."
    mkdir -p uploads/dev
    mkdir -p logs
    mkdir -p static
    log_success "目錄創建完成"
}

# 初始化資料庫
init_database() {
    log_info "初始化資料庫..."
    python3 -c "
import sys
sys.path.insert(0, 'src')
from shared.database.connection import create_tables_sync
try:
    create_tables_sync()
    print('✅ 資料庫初始化成功')
except Exception as e:
    print(f'⚠️ 資料庫初始化失敗: {e}')
    print('使用SQLite作為開發資料庫')
" 2>/dev/null || log_warning "資料庫初始化跳過（將在首次API調用時自動創建）"
}

# 啟動API Gateway
start_api_gateway() {
    log_info "啟動 API Gateway (端口8000)..."
    cd src/services/api-gateway
    python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
    API_GATEWAY_PID=$!
    echo $API_GATEWAY_PID > ../../../.api_gateway.pid
    cd ../../..
    sleep 2
    
    # 檢查服務是否啟動成功
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "API Gateway 啟動成功 - http://localhost:8000"
        log_info "API 文檔: http://localhost:8000/docs"
    else
        log_error "API Gateway 啟動失敗"
    fi
}

# 啟動AI Service
start_ai_service() {
    log_info "啟動 AI Service (端口8005)..."
    cd src/services/ai-service
    python3 -m uvicorn main_simple:app --host 0.0.0.0 --port 8005 --reload &
    AI_SERVICE_PID=$!
    echo $AI_SERVICE_PID > ../../../.ai_service.pid
    cd ../../..
    sleep 2
    
    # 檢查服務是否啟動成功
    if curl -s http://localhost:8005/health > /dev/null; then
        log_success "AI Service 啟動成功 - http://localhost:8005"
    else
        log_error "AI Service 啟動失敗"
    fi
}

# 啟動前端服務
start_frontend() {
    log_info "啟動前端服務 (端口3000)..."
    cd src/frontend
    npm run dev -- --host 0.0.0.0 --port 3000 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../../.frontend.pid
    cd ../..
    sleep 3
    
    log_success "前端服務啟動成功 - http://localhost:3000"
}

# 主要啟動流程
main() {
    echo "======================================"
    echo "🎬 Auto Video Generation MVP Starter"
    echo "======================================"
    
    # 環境檢查
    check_python
    check_node
    
    # 安裝依賴
    install_python_deps
    install_frontend_deps
    
    # 準備環境
    create_directories
    init_database
    
    # 啟動服務
    start_api_gateway
    start_ai_service  
    start_frontend
    
    echo ""
    echo "======================================"
    log_success "🎉 MVP 服務啟動完成！"
    echo "======================================"
    echo ""
    echo "📱 服務地址:"
    echo "   • 前端應用: http://localhost:3000"
    echo "   • API Gateway: http://localhost:8000"
    echo "   • AI Service: http://localhost:8005" 
    echo "   • API 文檔: http://localhost:8000/docs"
    echo ""
    echo "📋 下一步:"
    echo "   1. 在 .env.local 中配置真實的API金鑰"
    echo "   2. 訪問 http://localhost:3000 開始使用"
    echo "   3. 查看 API 文檔了解可用功能"
    echo ""
    echo "🛑 停止服務: ./stop_mvp.sh"
    echo "======================================"
    
    # 等待用戶中斷
    log_info "服務正在運行... 按 Ctrl+C 停止所有服務"
    
    # 捕獲中斷信號
    trap 'kill_services' INT
    
    # 保持腳本運行
    while true; do
        sleep 1
    done
}

# 停止服務函數
kill_services() {
    echo ""
    log_info "正在停止服務..."
    
    # 停止所有服務
    if [ -f ".api_gateway.pid" ]; then
        kill $(cat .api_gateway.pid) 2>/dev/null
        rm .api_gateway.pid
        log_success "API Gateway 已停止"
    fi
    
    if [ -f ".ai_service.pid" ]; then
        kill $(cat .ai_service.pid) 2>/dev/null
        rm .ai_service.pid
        log_success "AI Service 已停止"
    fi
    
    if [ -f ".frontend.pid" ]; then
        kill $(cat .frontend.pid) 2>/dev/null
        rm .frontend.pid
        log_success "前端服務已停止"
    fi
    
    log_success "所有服務已停止"
    exit 0
}

# 執行主函數
main "$@"