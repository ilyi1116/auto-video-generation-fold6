#!/bin/bash

# 服務健康檢查腳本
set -e

echo "🏥 執行服務健康檢查..."

# 服務端點配置
declare -A SERVICES=(
    ["API Gateway"]="http://localhost:8000/health"
    ["Auth Service"]="http://localhost:8001/health"
    ["Data Service"]="http://localhost:8002/health"
    ["Inference Service"]="http://localhost:8003/health"
    ["Video Service"]="http://localhost:8004/health"
    ["AI Service"]="http://localhost:8005/health"
    ["Social Service"]="http://localhost:8006/health"
    ["Trend Service"]="http://localhost:8007/health"
    ["Scheduler Service"]="http://localhost:8008/health"
)

# 基礎設施服務
declare -A INFRASTRUCTURE=(
    ["PostgreSQL"]="localhost:5432"
    ["Redis"]="localhost:6379"
    ["MinIO"]="http://localhost:9000/minio/health/live"
)

# 檢查是否有 curl
if ! command -v curl &> /dev/null; then
    echo "❌ curl 未安裝，無法執行健康檢查"
    exit 1
fi

# 檢查應用服務
echo "🔍 檢查應用服務..."
healthy_services=0
total_services=${#SERVICES[@]}

for service_name in "${!SERVICES[@]}"; do
    url="${SERVICES[$service_name]}"
    echo -n "檢查 $service_name... "
    
    if curl -s -f "$url" -m 5 > /dev/null 2>&1; then
        echo "✅ 健康"
        ((healthy_services++))
    else
        echo "❌ 無回應"
    fi
done

# 檢查基礎設施服務
echo ""
echo "🔍 檢查基礎設施服務..."
healthy_infra=0
total_infra=${#INFRASTRUCTURE[@]}

for service_name in "${!INFRASTRUCTURE[@]}"; do
    endpoint="${INFRASTRUCTURE[$service_name]}"
    echo -n "檢查 $service_name... "
    
    case $service_name in
        "PostgreSQL")
            if nc -z localhost 5432 2>/dev/null; then
                echo "✅ 健康"
                ((healthy_infra++))
            else
                echo "❌ 無法連接"
            fi
            ;;
        "Redis")
            if nc -z localhost 6379 2>/dev/null; then
                echo "✅ 健康"
                ((healthy_infra++))
            else
                echo "❌ 無法連接"
            fi
            ;;
        "MinIO")
            if curl -s -f "$endpoint" -m 5 > /dev/null 2>&1; then
                echo "✅ 健康"
                ((healthy_infra++))
            else
                echo "❌ 無回應"
            fi
            ;;
    esac
done

# 前端檢查
echo ""
echo "🔍 檢查前端服務..."
echo -n "檢查 Frontend (SvelteKit)... "
if curl -s -f "http://localhost:3000" -m 5 > /dev/null 2>&1; then
    echo "✅ 健康"
    frontend_healthy=1
else
    echo "❌ 無回應"
    frontend_healthy=0
fi

# 總結報告
echo ""
echo "📊 健康檢查總結："
echo "🚀 應用服務: $healthy_services/$total_services 健康"
echo "🔧 基礎設施: $healthy_infra/$total_infra 健康"
echo "🌐 前端服務: $frontend_healthy/1 健康"

# 計算整體健康度
total_checks=$((total_services + total_infra + 1))
healthy_checks=$((healthy_services + healthy_infra + frontend_healthy))
health_percentage=$((healthy_checks * 100 / total_checks))

echo ""
echo "🎯 整體系統健康度: $health_percentage%"

if [ $health_percentage -ge 80 ]; then
    echo "💚 系統狀態良好"
    exit_code=0
elif [ $health_percentage -ge 60 ]; then
    echo "⚠️ 系統部分異常"
    exit_code=1
else
    echo "🚨 系統異常，需要檢查"
    exit_code=2
fi

# 提供故障排除建議
if [ $healthy_services -lt $total_services ] || [ $healthy_infra -lt $total_infra ]; then
    echo ""
    echo "🔧 故障排除建議："
    echo "1. 檢查 Docker 容器狀態: docker-compose ps"
    echo "2. 查看服務日誌: docker-compose logs [service-name]"
    echo "3. 重啟異常服務: docker-compose restart [service-name]"
    echo "4. 檢查網路連接: docker network ls"
    echo "5. 檢查資源使用: docker stats"
fi

echo ""
echo "💡 完整啟動命令："
echo "   docker-compose up -d --build"
echo ""
echo "🔍 個別服務檢查："
for service_name in "${!SERVICES[@]}"; do
    echo "   curl ${SERVICES[$service_name]}"
done

exit $exit_code