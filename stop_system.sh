#!/bin/bash

# Auto Video Generation System - 系統停止腳本
# 安全地停止所有服務

echo "🛑 Stopping Auto Video Generation System..."

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

# 停止服務函數
stop_service() {
    local pid=$1
    local name=$2
    local timeout=10
    
    if [ -n "$pid" ] && kill -0 $pid 2>/dev/null; then
        log_info "Stopping $name (PID: $pid)..."
        
        # 嘗試優雅停止
        kill -TERM $pid 2>/dev/null
        
        # 等待進程結束
        local count=0
        while kill -0 $pid 2>/dev/null && [ $count -lt $timeout ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # 如果還沒停止，強制終止
        if kill -0 $pid 2>/dev/null; then
            log_warning "$name did not stop gracefully, force killing..."
            kill -KILL $pid 2>/dev/null
            sleep 1
        fi
        
        if ! kill -0 $pid 2>/dev/null; then
            log_success "$name stopped successfully"
            return 0
        else
            log_error "Failed to stop $name"
            return 1
        fi
    else
        log_info "$name is not running"
        return 0
    fi
}

# 停止通過端口識別的服務
stop_service_by_port() {
    local port=$1
    local name=$2
    
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pids" ]; then
        log_info "Found $name running on port $port"
        for pid in $pids; do
            stop_service $pid "$name (port $port)"
        done
    else
        log_info "No service running on port $port"
    fi
}

# 從PID文件讀取並停止服務
stop_from_pid_file() {
    local pid_file=$1
    local name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if stop_service "$pid" "$name"; then
            rm -f "$pid_file"
        fi
    else
        log_info "PID file $pid_file not found"
    fi
}

# 主要停止流程
log_info "Starting graceful shutdown..."

# 1. 從PID文件停止服務
stop_from_pid_file ".frontend.pid" "Frontend"
stop_from_pid_file ".ai_service.pid" "AI Service" 
stop_from_pid_file ".api_gateway.pid" "API Gateway"

# 2. 從系統PID文件停止服務  
if [ -f ".system_pids" ]; then
    source .system_pids 2>/dev/null
    
    stop_service "$FRONTEND_PID" "Frontend"
    stop_service "$AI_SERVICE_PID" "AI Service"
    stop_service "$API_GATEWAY_PID" "API Gateway"
    
    rm -f .system_pids
fi

# 3. 通過端口停止任何剩餘服務
log_info "Checking for remaining services on known ports..."
stop_service_by_port 8000 "API Gateway"
stop_service_by_port 8005 "AI Service"
stop_service_by_port 5173 "Frontend"

# 4. 停止任何npm dev進程
log_info "Stopping any remaining npm processes..."
pkill -f "npm run dev" 2>/dev/null && log_success "Stopped npm dev processes" || log_info "No npm dev processes found"

# 5. 停止Python進程（小心不要誤殺其他Python進程）
log_info "Stopping Python services..."
pkill -f "api_gateway_simple.py" 2>/dev/null && log_success "Stopped API Gateway Python process" || log_info "No API Gateway Python process found"
pkill -f "main_simple.py" 2>/dev/null && log_success "Stopped AI Service Python process" || log_info "No AI Service Python process found"

# 6. 清理PID文件
log_info "Cleaning up PID files..."
rm -f .*.pid .system_pids 2>/dev/null
log_success "PID files cleaned"

# 7. 驗證所有服務已停止
log_info "Verifying all services are stopped..."

services_stopped=true

# 檢查端口
for port in 8000 8005 5173; do
    if lsof -i :$port > /dev/null 2>&1; then
        log_warning "Port $port is still in use"
        services_stopped=false
    fi
done

if [ "$services_stopped" = true ]; then
    log_success "All services stopped successfully"
else
    log_warning "Some services may still be running"
    echo ""
    log_info "Active processes on known ports:"
    for port in 8000 8005 5173; do
        local processes=$(lsof -i :$port 2>/dev/null)
        if [ -n "$processes" ]; then
            echo "Port $port:"
            echo "$processes"
            echo ""
        fi
    done
fi

echo ""
echo "🏁 System shutdown complete!"
echo ""
echo "📊 Final Status:"
echo "   🛠️  API Gateway (8000): $(lsof -i :8000 > /dev/null 2>&1 && echo "❌ Still running" || echo "✅ Stopped")"
echo "   🤖 AI Service (8005): $(lsof -i :8005 > /dev/null 2>&1 && echo "❌ Still running" || echo "✅ Stopped")"
echo "   🌐 Frontend (5173): $(lsof -i :5173 > /dev/null 2>&1 && echo "❌ Still running" || echo "✅ Stopped")"

echo ""
echo "🚀 To start the system again:"
echo "   ./start_system.sh"
echo ""
echo "📁 Log files preserved in logs/ directory"

# 如果有服務仍在運行，提供手動清理選項
if [ "$services_stopped" != true ]; then
    echo ""
    echo "⚠️  If some services are still running, you can:"
    echo "   1. Wait a few seconds and run this script again"
    echo "   2. Manually kill processes: kill -9 <PID>"
    echo "   3. Restart your terminal/computer if necessary"
fi