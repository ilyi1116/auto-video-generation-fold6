#!/bin/bash

# Auto Video System 自動備份腳本
# 包含資料庫、檔案、配置和監控數據的完整備份

set -e

# 配置變數
BACKUP_BASE_DIR="/data/data/com.termux/files/home/myProject/auto_generate_video_fold6/backups"
PROJECT_DIR="/data/data/com.termux/files/home/myProject/auto_generate_video_fold6"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$BACKUP_BASE_DIR/$TIMESTAMP"
RETENTION_DAYS=30

# 載入環境變數
if [ -f "$PROJECT_DIR/.env" ]; then
    source "$PROJECT_DIR/.env"
else
    echo "❌ .env 檔案不存在"
    exit 1
fi

echo "🗄️ Auto Video System 備份開始..."
echo "📅 時間戳: $TIMESTAMP"
echo "📂 備份目錄: $BACKUP_DIR"

# 創建備份目錄
mkdir -p "$BACKUP_DIR"/{database,files,config,monitoring,logs}

# 1. 資料庫備份
echo ""
echo "🗃️ 1. 正在備份資料庫..."

# PostgreSQL 備份
if docker ps | grep -q postgres; then
    echo "   📊 備份 PostgreSQL..."
    docker exec postgres pg_dumpall -U postgres > "$BACKUP_DIR/database/postgres_full_backup.sql"
    
    # 個別資料庫備份
    for db in autovideo_auth autovideo_data autovideo_inference autovideo_video; do
        if docker exec postgres psql -U postgres -lqt | cut -d \| -f 1 | grep -qw $db; then
            echo "   📋 備份資料庫: $db"
            docker exec postgres pg_dump -U postgres $db > "$BACKUP_DIR/database/${db}_backup.sql"
        fi
    done
    echo "   ✅ PostgreSQL 備份完成"
else
    echo "   ⚠️  PostgreSQL 容器未運行"
fi

# Redis 備份
if docker ps | grep -q redis; then
    echo "   🔴 備份 Redis..."
    docker exec redis redis-cli BGSAVE
    sleep 5
    docker cp redis:/data/dump.rdb "$BACKUP_DIR/database/redis_dump.rdb"
    echo "   ✅ Redis 備份完成"
else
    echo "   ⚠️  Redis 容器未運行"
fi

# 2. 檔案系統備份
echo ""
echo "📁 2. 正在備份檔案系統..."

# 用戶上傳檔案
if [ -d "$PROJECT_DIR/uploads" ]; then
    echo "   📤 備份用戶上傳檔案..."
    tar -czf "$BACKUP_DIR/files/uploads.tar.gz" -C "$PROJECT_DIR" uploads/
    echo "   ✅ 上傳檔案備份完成"
fi

# AI 模型檔案
if [ -d "$PROJECT_DIR/models" ]; then
    echo "   🤖 備份 AI 模型檔案..."
    tar -czf "$BACKUP_DIR/files/models.tar.gz" -C "$PROJECT_DIR" models/
    echo "   ✅ 模型檔案備份完成"
fi

# 生成的影片檔案
if [ -d "$PROJECT_DIR/generated_videos" ]; then
    echo "   🎬 備份生成的影片..."
    tar -czf "$BACKUP_DIR/files/generated_videos.tar.gz" -C "$PROJECT_DIR" generated_videos/
    echo "   ✅ 影片檔案備份完成"
fi

# 3. 配置檔案備份
echo ""
echo "⚙️ 3. 正在備份配置檔案..."

# 複製所有配置檔案
cp "$PROJECT_DIR/.env" "$BACKUP_DIR/config/"
cp "$PROJECT_DIR/docker-compose.yml" "$BACKUP_DIR/config/" 2>/dev/null || true
cp "$PROJECT_DIR/docker-compose.monitoring.yml" "$BACKUP_DIR/config/" 2>/dev/null || true

# 備份各服務配置
for service in api-gateway auth-service data-service inference-service video-service ai-service social-service trend-service scheduler-service; do
    if [ -d "$PROJECT_DIR/services/$service" ]; then
        echo "   📋 備份 $service 配置..."
        tar -czf "$BACKUP_DIR/config/${service}_config.tar.gz" -C "$PROJECT_DIR/services" "$service/"
    fi
done

# 備份監控配置
if [ -d "$PROJECT_DIR/monitoring" ]; then
    echo "   📊 備份監控配置..."
    tar -czf "$BACKUP_DIR/config/monitoring_config.tar.gz" -C "$PROJECT_DIR" monitoring/
fi

# 備份安全配置
if [ -d "$PROJECT_DIR/security" ]; then
    echo "   🔐 備份安全配置..."
    tar -czf "$BACKUP_DIR/config/security_config.tar.gz" -C "$PROJECT_DIR" security/
fi

echo "   ✅ 配置檔案備份完成"

# 4. 監控數據備份
echo ""
echo "📈 4. 正在備份監控數據..."

# Prometheus 數據
if docker ps | grep -q prometheus; then
    echo "   📊 備份 Prometheus 數據..."
    docker exec prometheus tar -czf /tmp/prometheus_data.tar.gz -C /prometheus .
    docker cp prometheus:/tmp/prometheus_data.tar.gz "$BACKUP_DIR/monitoring/"
    docker exec prometheus rm /tmp/prometheus_data.tar.gz
    echo "   ✅ Prometheus 數據備份完成"
fi

# Grafana 數據
if docker ps | grep -q grafana; then
    echo "   📊 備份 Grafana 數據..."
    docker exec grafana tar -czf /tmp/grafana_data.tar.gz -C /var/lib/grafana .
    docker cp grafana:/tmp/grafana_data.tar.gz "$BACKUP_DIR/monitoring/"
    docker exec grafana rm /tmp/grafana_data.tar.gz
    echo "   ✅ Grafana 數據備份完成"
fi

# 5. 日誌備份
echo ""
echo "📄 5. 正在備份日誌檔案..."

# 容器日誌
echo "   📋 備份容器日誌..."
for container in $(docker ps --format "{{.Names}}" | grep -E "(api-gateway|auth-service|data-service|inference-service|video-service|ai-service|social-service|trend-service|scheduler-service)"); do
    docker logs "$container" > "$BACKUP_DIR/logs/${container}.log" 2>&1 || true
done

# 系統日誌（如果有權限）
if [ -d "/var/log" ] && [ -r "/var/log" ]; then
    echo "   📋 備份系統日誌..."
    tar -czf "$BACKUP_DIR/logs/system_logs.tar.gz" -C /var/log . 2>/dev/null || true
fi

echo "   ✅ 日誌備份完成"

# 6. 創建備份摘要
echo ""
echo "📝 6. 創建備份摘要..."

cat > "$BACKUP_DIR/backup_info.txt" << EOF
Auto Video System 備份摘要
========================

備份時間: $(date)
備份版本: $TIMESTAMP
系統版本: $(git rev-parse HEAD 2>/dev/null || echo "未知")

備份內容:
- 資料庫: PostgreSQL, Redis
- 檔案: 用戶上傳, AI 模型, 生成影片
- 配置: 所有微服務配置檔案
- 監控: Prometheus, Grafana 數據
- 日誌: 容器和系統日誌

備份大小:
$(du -sh "$BACKUP_DIR" | cut -f1)

檔案清單:
$(find "$BACKUP_DIR" -type f -exec ls -lh {} \; | awk '{print $9, $5}')
EOF

# 7. 創建檢查碼
echo ""
echo "🔍 7. 創建完整性檢查..."
find "$BACKUP_DIR" -type f -exec sha256sum {} \; > "$BACKUP_DIR/checksums.sha256"

# 8. 壓縮整個備份
echo ""
echo "📦 8. 壓縮備份檔案..."
tar -czf "$BACKUP_BASE_DIR/autovideo_backup_$TIMESTAMP.tar.gz" -C "$BACKUP_BASE_DIR" "$TIMESTAMP/"

# 計算壓縮檔案大小
BACKUP_SIZE=$(du -sh "$BACKUP_BASE_DIR/autovideo_backup_$TIMESTAMP.tar.gz" | cut -f1)

# 9. 清理舊備份
echo ""
echo "🧹 9. 清理舊備份..."
find "$BACKUP_BASE_DIR" -name "autovideo_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
find "$BACKUP_BASE_DIR" -maxdepth 1 -type d -name "20*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true

# 刪除未壓縮的備份目錄
rm -rf "$BACKUP_DIR"

echo ""
echo "✅ 備份完成！"
echo ""
echo "📊 備份摘要："
echo "   📦 壓縮檔案: autovideo_backup_$TIMESTAMP.tar.gz"
echo "   📏 檔案大小: $BACKUP_SIZE"
echo "   📂 儲存位置: $BACKUP_BASE_DIR/"
echo ""
echo "🔧 還原說明："
echo "   1. 解壓縮: tar -xzf autovideo_backup_$TIMESTAMP.tar.gz"
echo "   2. 執行還原腳本: ./scripts/restore-system.sh $TIMESTAMP"
echo ""
echo "📋 建議："
echo "   - 定期將備份檔案複製到異地儲存"
echo "   - 定期測試備份還原流程"
echo "   - 監控備份檔案的完整性"
echo ""