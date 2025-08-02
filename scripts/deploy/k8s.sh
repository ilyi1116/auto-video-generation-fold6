#!/bin/bash

# Kubernetes 部署腳本
set -e

echo "Starting Kubernetes deployment..."

# 檢查必要工具
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed"
    exit 1
fi

# 創建命名空間
kubectl create namespace video-system 2>/dev/null || true

# 部署應用程式
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

echo "Kubernetes deployment completed successfully!" 