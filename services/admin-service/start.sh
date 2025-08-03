#!/bin/bash

# 後台管理系統啟動腳本

set -e

echo "🚀 啟動後台管理系統..."

# 檢查環境配置
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，從 .env.example 複製..."
    cp .env.example .env
    echo "❗ 請編輯 .env 文件設置正確的配置"
fi

# 創建必要目錄
mkdir -p logs
mkdir -p backups
mkdir -p temp

# 檢查 Docker 是否安裝
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝，請先安裝 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安裝，請先安裝 Docker Compose"
    exit 1
fi

# 建構和啟動服務
echo "🔨 建構 Docker 映像..."
docker-compose build

echo "🗄️  啟動資料庫服務..."
docker-compose up -d postgres redis

# 等待資料庫啟動
echo "⏳ 等待資料庫啟動..."
sleep 10

# 運行資料庫遷移
echo "🔄 運行資料庫遷移..."
docker-compose run --rm admin-api python -c "
from database import init_db
init_db()
print('資料庫初始化完成')
"

# 創建初始管理員用戶
echo "👤 創建初始管理員用戶..."
docker-compose run --rm admin-api python -c "
from database import SessionLocal
from crud import crud_admin_user
from schemas import AdminUserCreate

db = SessionLocal()
try:
    # 檢查是否已有管理員用戶
    existing_user = crud_admin_user.get_by_username(db, 'admin')
    if not existing_user:
        admin_user = AdminUserCreate(
            username='admin',
            email='admin@localhost',
            password='admin123',
            full_name='系統管理員',
            role='super_admin',
            is_superuser=True
        )
        user = crud_admin_user.create_admin_user(db, user_in=admin_user)
        print(f'創建管理員用戶: {user.username}')
        print('預設密碼: admin123 (請登錄後立即修改)')
    else:
        print('管理員用戶已存在')
finally:
    db.close()
"

# 啟動所有服務
echo "🚀 啟動所有服務..."
docker-compose up -d

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 15

# 檢查服務狀態
echo "🔍 檢查服務狀態..."
docker-compose ps

# 檢查 API 健康狀態
echo "🏥 檢查 API 健康狀態..."
if curl -f http://localhost:8080/admin/health &> /dev/null; then
    echo "✅ API 服務運行正常"
else
    echo "❌ API 服務可能未正常啟動"
    echo "📋 查看日誌:"
    docker-compose logs admin-api
fi

echo ""
echo "🎉 後台管理系統啟動完成！"
echo ""
echo "📱 服務地址:"
echo "   - API 文檔: http://localhost:8080/docs"
echo "   - 管理介面: http://localhost:8080/admin"
echo "   - Celery 監控: http://localhost:5555"
echo ""
echo "🔑 預設登錄信息:"
echo "   - 用戶名: admin"
echo "   - 密碼: admin123"
echo ""
echo "⚠️  請立即修改預設密碼！"
echo ""
echo "📚 常用命令:"
echo "   - 查看日誌: docker-compose logs -f [service-name]"
echo "   - 停止服務: docker-compose down"
echo "   - 重啟服務: docker-compose restart [service-name]"
echo ""