#!/bin/bash

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"

source venv/bin/activate

# 設置環境變數
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 啟動後端服務
log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_info "啟動後端服務..."

# 檢查是否有主要的後端入口文件
if [[ -f "main.py" ]]; then
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
elif [[ -f "app/main.py" ]]; then
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
elif [[ -f "services/api-gateway/main.py" ]]; then
    cd services/api-gateway
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "找不到後端入口文件，請檢查專案結構"
    exit 1
fi
