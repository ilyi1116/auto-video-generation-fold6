#!/bin/bash

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

# 停止前端
if [[ -f "$PROJECT_ROOT/logs/pids/frontend.pid" ]]; then
    FRONTEND_PID=$(cat "$PROJECT_ROOT/logs/pids/frontend.pid")
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        log_info "停止前端服務 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm "$PROJECT_ROOT/logs/pids/frontend.pid"
        log_success "前端服務已停止"
    fi
fi

# 停止後端
if [[ -f "$PROJECT_ROOT/logs/pids/backend.pid" ]]; then
    BACKEND_PID=$(cat "$PROJECT_ROOT/logs/pids/backend.pid")
    if kill -0 $BACKEND_PID 2>/dev/null; then
        log_info "停止後端服務 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        rm "$PROJECT_ROOT/logs/pids/backend.pid"
        log_success "後端服務已停止"
    fi
fi

log_success "系統已完全停止"
