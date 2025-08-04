#!/bin/bash

# Docker 環境驗證腳本
set -e

echo "🐳 驗證 Docker 環境配置..."

# 檢查 Docker Compose 檔案語法
echo "📋 檢查 docker-compose.yml 語法..."
if command -v docker-compose &> /dev/null; then
    docker-compose config > /dev/null
    echo "✅ docker-compose.yml 語法正確"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    docker compose config > /dev/null
    echo "✅ docker-compose.yml 語法正確"
else
    echo "⚠️  Docker 未安裝，跳過運行時檢查"
    echo "📋 檢查 Dockerfile 是否存在..."
fi

# 檢查所有服務的 Dockerfile
SERVICES=(
    "api-gateway"
    "auth-service" 
    "data-service"
    "ai-service"
    "video-service"
    "storage-service"
    "scheduler-service"
    "social-service"
    "trend-service"
    "inference-service"
    "training-worker"
)

echo "📦 檢查各服務 Dockerfile..."
for service in "${SERVICES[@]}"; do
    dockerfile_path="services/$service/Dockerfile"
    if [ -f "$dockerfile_path" ]; then
        echo "✅ $service: Dockerfile 存在"
    else
        echo "❌ $service: Dockerfile 缺失"
    fi
done

# 檢查環境變數檔案
echo "🔧 檢查環境變數配置..."
if [ -f ".env" ]; then
    echo "✅ .env 檔案存在"
    
    # 檢查關鍵環境變數
    required_vars=(
        "POSTGRES_USER"
        "POSTGRES_PASSWORD" 
        "POSTGRES_DB"
        "JWT_SECRET_KEY"
        "REDIS_URL"
        "S3_ACCESS_KEY_ID"
        "S3_SECRET_ACCESS_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if grep -q "^$var=" .env; then
            echo "✅ $var 已設定"
        else
            echo "❌ $var 未設定"
        fi
    done
else
    echo "❌ .env 檔案缺失"
fi

# 檢查資料庫遷移腳本
echo "🗄️ 檢查資料庫初始化腳本..."
init_scripts=(
    "scripts/init-db.sql"
    "scripts/video_schema.sql"
)

for script in "${init_scripts[@]}"; do
    if [ -f "$script" ]; then
        echo "✅ $script 存在"
    else
        echo "❌ $script 缺失"
    fi
done

# 檢查 requirements.txt 檔案
echo "📦 檢查 Python 依賴檔案..."
for service in "${SERVICES[@]}"; do
    requirements_path="services/$service/requirements.txt"
    if [ -f "$requirements_path" ]; then
        echo "✅ $service: requirements.txt 存在"
    else
        echo "❌ $service: requirements.txt 缺失"
    fi
done

# 檢查測試檔案
echo "🧪 檢查測試檔案..."
for service in "${SERVICES[@]}"; do
    test_dir="services/$service/tests"
    if [ -d "$test_dir" ]; then
        test_count=$(find "$test_dir" -name "test_*.py" | wc -l)
        if [ "$test_count" -gt 0 ]; then
            echo "✅ $service: 有 $test_count 個測試檔案"
        else
            echo "⚠️  $service: tests 目錄存在但無測試檔案"
        fi
    else
        echo "❌ $service: 無 tests 目錄"
    fi
done

# 檢查前端配置
echo "🌐 檢查前端配置..."
if [ -f "frontend/package.json" ]; then
    echo "✅ frontend/package.json 存在"
    
    if [ -f "frontend/svelte.config.js" ]; then
        echo "✅ Svelte 配置存在"
    else
        echo "❌ Svelte 配置缺失"
    fi
    
    if [ -f "frontend/vite.config.js" ]; then
        echo "✅ Vite 配置存在"
    else
        echo "❌ Vite 配置缺失"
    fi
else
    echo "❌ frontend/package.json 缺失"
fi

echo ""
echo "🎯 Docker 環境驗證完成！"
echo "💡 如需運行完整系統，請使用："
echo "   docker-compose up --build"
echo ""
echo "🔍 如需檢查服務健康狀態，請使用："
echo "   docker-compose ps"
echo "   curl http://localhost:8000/health  # API Gateway"
echo "   curl http://localhost:8001/health  # Auth Service"
echo "   curl http://localhost:8008/health  # Scheduler Service"