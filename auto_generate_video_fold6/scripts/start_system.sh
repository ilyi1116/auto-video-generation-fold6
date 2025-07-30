#!/bin/bash

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# 創建 PID 文件目錄
mkdir -p "$PROJECT_ROOT/logs/pids"

# 啟動後端
log_info "啟動後端服務..."
bash "$PROJECT_ROOT/scripts/start_backend.sh" > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$PROJECT_ROOT/logs/pids/backend.pid"

# 等待後端啟動
sleep 5

# 檢查後端是否正常啟動
if kill -0 $BACKEND_PID 2>/dev/null; then
    log_success "後端服務已啟動 (PID: $BACKEND_PID)"
else
    log_error "後端服務啟動失敗"
    exit 1
fi

# 啟動前端
log_info "啟動前端服務..."
bash "$PROJECT_ROOT/scripts/start_frontend.sh" > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$PROJECT_ROOT/logs/pids/frontend.pid"

# 等待前端啟動
sleep 3

if kill -0 $FRONTEND_PID 2>/dev/null; then
    log_success "前端服務已啟動 (PID: $FRONTEND_PID)"
else
    log_error "前端服務啟動失敗"
    exit 1
fi

log_success "系統啟動完成！"
echo ""
echo "服務地址："
echo "  前端: http://localhost:3000"
echo "  後端: http://localhost:8000"
echo ""
echo "日誌文件："
echo "  後端: $PROJECT_ROOT/logs/backend.log"
echo "  前端: $PROJECT_ROOT/logs/frontend.log"
echo ""
echo "停止服務: bash $PROJECT_ROOT/scripts/stop_system.sh"
