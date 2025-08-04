#!/bin/bash

# Auto Video System 系統還原腳本
# 從備份檔案還原完整系統

set -e

BACKUP_BASE_DIR="/data/data/com.termux/files/home/myProject/auto_generate_video_fold6/backups"
PROJECT_DIR="/data/data/com.termux/files/home/myProject/auto_generate_video_fold6"

# 檢查參數
if [ $# -eq 0 ]; then
    echo "❌ 使用方法: $0 <備份時間戳>"
    echo ""
    echo "可用的備份："
    ls -la "$BACKUP_BASE_DIR"/autovideo_backup_*.tar.gz 2>/dev/null | awk '{print "   " $9}' || echo "   無可用備份"
    exit 1
fi

BACKUP_TIMESTAMP="$1"
BACKUP_FILE="$BACKUP_BASE_DIR/autovideo_backup_$BACKUP_TIMESTAMP.tar.gz"
RESTORE_DIR="$BACKUP_BASE_DIR/restore_$BACKUP_TIMESTAMP"

echo "🔄 Auto Video System 系統還原開始..."
echo "📅 備份時間戳: $BACKUP_TIMESTAMP"
echo "📦 備份檔案: $BACKUP_FILE"

# 檢查備份檔案
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ 備份檔案不存在: $BACKUP_FILE"
    exit 1
fi

# 創建還原目錄
mkdir -p "$RESTORE_DIR"

# 1. 解壓縮備份檔案
echo ""
echo "📦 1. 解壓縮備份檔案..."
tar -xzf "$BACKUP_FILE" -C "$BACKUP_BASE_DIR"
EXTRACT_DIR="$BACKUP_BASE_DIR/$BACKUP_TIMESTAMP"

if [ ! -d "$EXTRACT_DIR" ]; then
    echo "❌ 解壓縮失敗或目錄結構不正確"
    exit 1
fi

# 2. 驗證備份完整性
echo ""
echo "🔍 2. 驗證備份完整性..."
if [ -f "$EXTRACT_DIR/checksums.sha256" ]; then
    cd "$EXTRACT_DIR"
    if sha256sum -c checksums.sha256 --quiet; then
        echo "   ✅ 備份檔案完整性驗證通過"
    else
        echo "   ❌ 備份檔案完整性驗證失敗"
        read -p "是否繼續還原？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    cd - > /dev/null
else
    echo "   ⚠️  未找到檢查碼檔案，跳過完整性驗證"
fi

# 3. 停止現有服務
echo ""
echo "🛑 3. 停止現有服務..."
cd "$PROJECT_DIR"

if [ -f "docker-compose.yml" ]; then
    docker-compose down 2>/dev/null || true
fi

if [ -f "docker-compose.monitoring.yml" ]; then
    docker-compose -f docker-compose.monitoring.yml down 2>/dev/null || true
fi

echo "   ✅ 服務已停止"

# 4. 備份現有數據（安全措施）
echo ""
echo "🛡️ 4. 備份現有數據..."
CURRENT_BACKUP_DIR="$BACKUP_BASE_DIR/pre_restore_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$CURRENT_BACKUP_DIR"

# 備份現有配置
if [ -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env" "$CURRENT_BACKUP_DIR/"
fi

echo "   ✅ 現有數據已備份到: $CURRENT_BACKUP_DIR"

# 5. 還原配置檔案
echo ""
echo "⚙️ 5. 還原配置檔案..."

# 還原環境變數
if [ -f "$EXTRACT_DIR/config/.env" ]; then
    cp "$EXTRACT_DIR/config/.env" "$PROJECT_DIR/"
    echo "   📋 環境變數已還原"
fi

# 還原 Docker Compose 檔案
for compose_file in docker-compose.yml docker-compose.monitoring.yml; do
    if [ -f "$EXTRACT_DIR/config/$compose_file" ]; then
        cp "$EXTRACT_DIR/config/$compose_file" "$PROJECT_DIR/"
        echo "   📋 $compose_file 已還原"
    fi
done

# 還原服務配置
for config_file in "$EXTRACT_DIR/config"/*_config.tar.gz; do
    if [ -f "$config_file" ]; then
        service_name=$(basename "$config_file" _config.tar.gz)
        echo "   📋 還原 $service_name 配置..."
        tar -xzf "$config_file" -C "$PROJECT_DIR/services/"
    fi
done

# 還原監控配置
if [ -f "$EXTRACT_DIR/config/monitoring_config.tar.gz" ]; then
    echo "   📊 還原監控配置..."
    tar -xzf "$EXTRACT_DIR/config/monitoring_config.tar.gz" -C "$PROJECT_DIR/"
fi

# 還原安全配置
if [ -f "$EXTRACT_DIR/config/security_config.tar.gz" ]; then
    echo "   🔐 還原安全配置..."
    tar -xzf "$EXTRACT_DIR/config/security_config.tar.gz" -C "$PROJECT_DIR/"
fi

echo "   ✅ 配置檔案還原完成"

# 6. 啟動基礎服務
echo ""
echo "🚀 6. 啟動基礎服務..."

# 載入環境變數
source "$PROJECT_DIR/.env"

# 啟動資料庫服務
docker-compose up -d postgres redis

echo "   ⏳ 等待資料庫啟動..."
sleep 10

# 檢查資料庫是否可用
until docker exec postgres pg_isready -U postgres; do
    echo "   ⏳ 等待 PostgreSQL..."
    sleep 2
done

until docker exec redis redis-cli ping | grep -q PONG; do
    echo "   ⏳ 等待 Redis..."
    sleep 2
done

echo "   ✅ 基礎服務已啟動"

# 7. 還原資料庫
echo ""
echo "🗃️ 7. 還原資料庫..."

# 還原 PostgreSQL
if [ -f "$EXTRACT_DIR/database/postgres_full_backup.sql" ]; then
    echo "   📊 還原 PostgreSQL..."
    docker exec -i postgres psql -U postgres < "$EXTRACT_DIR/database/postgres_full_backup.sql"
    echo "   ✅ PostgreSQL 還原完成"
fi

# 還原 Redis
if [ -f "$EXTRACT_DIR/database/redis_dump.rdb" ]; then
    echo "   🔴 還原 Redis..."
    docker cp "$EXTRACT_DIR/database/redis_dump.rdb" redis:/data/dump.rdb
    docker restart redis
    sleep 5
    echo "   ✅ Redis 還原完成"
fi

# 8. 還原檔案系統
echo ""
echo "📁 8. 還原檔案系統..."

# 還原用戶上傳檔案
if [ -f "$EXTRACT_DIR/files/uploads.tar.gz" ]; then
    echo "   📤 還原用戶上傳檔案..."
    tar -xzf "$EXTRACT_DIR/files/uploads.tar.gz" -C "$PROJECT_DIR/"
    echo "   ✅ 上傳檔案已還原"
fi

# 還原 AI 模型檔案
if [ -f "$EXTRACT_DIR/files/models.tar.gz" ]; then
    echo "   🤖 還原 AI 模型檔案..."
    tar -xzf "$EXTRACT_DIR/files/models.tar.gz" -C "$PROJECT_DIR/"
    echo "   ✅ 模型檔案已還原"
fi

# 還原生成的影片檔案
if [ -f "$EXTRACT_DIR/files/generated_videos.tar.gz" ]; then
    echo "   🎬 還原生成的影片..."
    tar -xzf "$EXTRACT_DIR/files/generated_videos.tar.gz" -C "$PROJECT_DIR/"
    echo "   ✅ 影片檔案已還原"
fi

# 9. 啟動所有服務
echo ""
echo "🚀 9. 啟動所有服務..."

# 啟動主要服務
docker-compose up -d

echo "   ⏳ 等待服務啟動..."
sleep 15

# 啟動監控服務
if [ -f "docker-compose.monitoring.yml" ]; then
    docker-compose -f docker-compose.monitoring.yml up -d
    sleep 10
fi

# 10. 還原監控數據
echo ""
echo "📈 10. 還原監控數據..."

# 還原 Prometheus 數據
if [ -f "$EXTRACT_DIR/monitoring/prometheus_data.tar.gz" ] && docker ps | grep -q prometheus; then
    echo "   📊 還原 Prometheus 數據..."
    docker exec prometheus rm -rf /prometheus/* 2>/dev/null || true
    docker cp "$EXTRACT_DIR/monitoring/prometheus_data.tar.gz" prometheus:/tmp/
    docker exec prometheus tar -xzf /tmp/prometheus_data.tar.gz -C /prometheus/
    docker exec prometheus rm /tmp/prometheus_data.tar.gz
    docker restart prometheus
    echo "   ✅ Prometheus 數據已還原"
fi

# 還原 Grafana 數據
if [ -f "$EXTRACT_DIR/monitoring/grafana_data.tar.gz" ] && docker ps | grep -q grafana; then
    echo "   📊 還原 Grafana 數據..."
    docker exec grafana rm -rf /var/lib/grafana/* 2>/dev/null || true
    docker cp "$EXTRACT_DIR/monitoring/grafana_data.tar.gz" grafana:/tmp/
    docker exec grafana tar -xzf /tmp/grafana_data.tar.gz -C /var/lib/grafana/
    docker exec grafana rm /tmp/grafana_data.tar.gz
    docker exec grafana chown -R grafana:grafana /var/lib/grafana/
    docker restart grafana
    echo "   ✅ Grafana 數據已還原"
fi

# 11. 健康檢查
echo ""
echo "🏥 11. 執行健康檢查..."

sleep 10

# 檢查服務狀態
echo "   🔍 檢查服務狀態..."
docker-compose ps

# 檢查 API 健康狀態
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ API Gateway 健康"
else
    echo "   ⚠️  API Gateway 可能需要更多時間啟動"
fi

# 12. 清理
echo ""
echo "🧹 12. 清理臨時檔案..."
rm -rf "$EXTRACT_DIR"

echo ""
echo "✅ 系統還原完成！"
echo ""
echo "📊 還原摘要："
echo "   📅 還原時間: $(date)"
echo "   📦 源備份: $BACKUP_TIMESTAMP"
echo "   🛡️  安全備份: $CURRENT_BACKUP_DIR"
echo ""
echo "🔧 後續步驟："
echo "   1. 檢查所有服務是否正常運行"
echo "   2. 驗證數據完整性"
echo "   3. 測試關鍵功能"
echo "   4. 檢查監控面板"
echo ""
echo "📋 檢查清單："
echo "   - 前端: http://localhost:3000"
echo "   - API: http://localhost:8000/health"
echo "   - Grafana: http://localhost:3001"
echo "   - Prometheus: http://localhost:9090"
echo ""