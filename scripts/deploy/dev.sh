#!/bin/bash

# 開發環境快速部署腳本
set -e

echo "Starting development environment setup..."

# 安裝依賴
cd backend && pip install -r requirements.txt

# 執行數據庫遷移
cd ../scripts/config && python validate.py

# 啟動服務
cd ../backend && uvicorn api_gateway.main:app --host 0.0.0.0 --port 8000 --reload &

echo "Development environment ready!" 