#!/bin/bash

# MVP 停止腳本 - 停止所有運行的服務
# Auto Video Generation MVP Stop Script

echo "🛑 Stopping Auto Video Generation MVP services..."

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 停止服務函數
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            rm "$pid_file"
            log_success "$service_name 已停止 (PID: $pid)"
        else
            log_warning "$service_name PID檔案存在但進程已結束"
            rm "$pid_file"
        fi
    else
        log_info "$service_name 未在運行或PID檔案不存在"
    fi
}

# 透過端口停止服務
stop_by_port() {
    local port=$1
    local service_name=$2
    
    local pid=$(lsof -ti :$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        kill "$pid" 2>/dev/null
        log_success "$service_name (端口$port) 已停止 (PID: $pid)"
    fi
}

echo "======================================"
echo "🛑 停止 MVP 服務"
echo "======================================"

# 停止記錄的服務
stop_service "API Gateway" ".api_gateway.pid"
stop_service "AI Service" ".ai_service.pid"  
stop_service "前端服務" ".frontend.pid"

# 額外通過端口停止服務（防止遺漏）
log_info "檢查端口並停止遺漏的服務..."
stop_by_port 8000 "API Gateway"
stop_by_port 8005 "AI Service"
stop_by_port 3000 "前端服務"

# 停止可能的Python/Node進程
log_info "清理相關進程..."
pkill -f "uvicorn.*main:app" 2>/dev/null && log_success "清理 uvicorn 進程"
pkill -f "npm run dev" 2>/dev/null && log_success "清理 npm dev 進程"
pkill -f "vite.*--port 3000" 2>/dev/null && log_success "清理 vite 進程"

echo ""
log_success "🎉 所有MVP服務已停止"

# 清理臨時檔案
if ls *.pid &> /dev/null; then
    rm *.pid
    log_info "清理殘留的PID檔案"
fi

echo "======================================"