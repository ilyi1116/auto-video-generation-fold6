#!/bin/bash

# 工具函數腳本

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed"
        return 1
    fi
    return 0
}

# 等待服務啟動
wait_for_service() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=1

    log_info "Waiting for $service to start on port $port..."

    while [ $attempt -le $max_attempts ]; do
        if nc -z localhost $port 2>/dev/null; then
            log_info "$service is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    log_error "$service failed to start"
    return 1
} 