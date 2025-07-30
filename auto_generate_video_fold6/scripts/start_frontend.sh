#!/bin/bash

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT/frontend"

log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_info "啟動前端服務..."

# 檢查是否已構建
if [[ ! -d "build" ]] && [[ ! -d ".svelte-kit" ]]; then
    log_info "未找到構建文件，執行構建..."
    npm run build
fi

# 啟動預覽服務器
npm run preview -- --host 0.0.0.0 --port 3000
