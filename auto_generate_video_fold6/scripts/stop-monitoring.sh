#!/bin/bash

# 停止監控系統腳本
# Auto Video System Monitoring Stack

set -e

echo "🛑 正在停止 Auto Video 監控系統..."

# 停止監控服務
echo "📴 停止監控服務..."
docker-compose -f docker-compose.monitoring.yml down

# 選擇性清理資料（使用 --volumes 參數）
if [ "$1" = "--clean" ]; then
    echo "🧹 清理監控資料..."
    docker-compose -f docker-compose.monitoring.yml down --volumes
    echo "✅ 監控資料已清理"
fi

# 選擇性移除網路
if [ "$1" = "--clean-all" ]; then
    echo "🧹 清理監控資料和網路..."
    docker-compose -f docker-compose.monitoring.yml down --volumes
    docker network rm auto-video-network 2>/dev/null || echo "⚠️  網路仍被其他容器使用"
    echo "✅ 所有監控資源已清理"
fi

echo ""
echo "✅ 監控系統已停止"
echo ""
echo "使用說明："
echo "  ./scripts/stop-monitoring.sh           # 僅停止服務"
echo "  ./scripts/stop-monitoring.sh --clean   # 停止服務並清理資料"
echo "  ./scripts/stop-monitoring.sh --clean-all # 停止服務、清理資料和網路"
echo ""