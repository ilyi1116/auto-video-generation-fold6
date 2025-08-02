#!/bin/bash

# Docker 部署腳本
set -e

echo "Starting Docker deployment..."

# 檢查必要工具
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# 建立網路
docker network create app-network 2>/dev/null || true

# 建立並啟動服務
docker-compose up -d

# 等待服務啟動
echo "Waiting for services to start..."
sleep 10

# 健康檢查
docker-compose ps

echo "Docker deployment completed successfully!" 