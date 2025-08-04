#!/bin/bash

# 啟動監控系統腳本
# Auto Video System Monitoring Stack

set -e

echo "🚀 正在啟動 Auto Video 監控系統..."

# 檢查 Docker 和 Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝，請先安裝 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安裝，請先安裝 Docker Compose"
    exit 1
fi

# 創建監控網路（如果不存在）
echo "📡 創建監控網路..."
docker network create auto-video-network 2>/dev/null || echo "✅ 網路已存在"

# 檢查環境變數檔案
if [ ! -f .env ]; then
    echo "❌ .env 檔案不存在，請先創建環境變數檔案"
    exit 1
fi

# 載入環境變數
source .env

# 創建監控資料目錄
echo "📂 創建監控資料目錄..."
mkdir -p monitoring/prometheus/data
mkdir -p monitoring/grafana/data
mkdir -p monitoring/alertmanager/data

# 設定正確的權限
echo "🔐 設定檔案權限..."
sudo chown -R 472:472 monitoring/grafana/ 2>/dev/null || true
sudo chown -R 65534:65534 monitoring/prometheus/ 2>/dev/null || true
sudo chown -R 65534:65534 monitoring/alertmanager/ 2>/dev/null || true

# 啟動監控服務
echo "🎯 啟動監控服務..."
docker-compose -f docker-compose.monitoring.yml up -d

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 10

# 檢查服務狀態
echo "🔍 檢查服務狀態..."
docker-compose -f docker-compose.monitoring.yml ps

# 健康檢查
echo "🏥 執行健康檢查..."

# 檢查 Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "✅ Prometheus 運行正常"
else
    echo "❌ Prometheus 可能有問題"
fi

# 檢查 Grafana
if curl -s http://localhost:3001/api/health > /dev/null; then
    echo "✅ Grafana 運行正常"
else
    echo "❌ Grafana 可能有問題"
fi

# 檢查 Alertmanager
if curl -s http://localhost:9093/-/healthy > /dev/null; then
    echo "✅ Alertmanager 運行正常"
else
    echo "❌ Alertmanager 可能有問題"
fi

echo ""
echo "🎉 監控系統啟動完成！"
echo ""
echo "📊 監控面板："
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3001 (admin/admin123)"
echo "   - Alertmanager: http://localhost:9093"
echo ""
echo "📈 系統指標："
echo "   - Node Exporter: http://localhost:9100"
echo "   - cAdvisor: http://localhost:8081"
echo "   - Redis Exporter: http://localhost:9121"
echo "   - PostgreSQL Exporter: http://localhost:9187"
echo ""
echo "📝 使用說明："
echo "   - 預設 Grafana 帳號: admin / admin123"
echo "   - 停止監控: ./scripts/stop-monitoring.sh"
echo "   - 查看日誌: docker-compose -f docker-compose.monitoring.yml logs"
echo ""