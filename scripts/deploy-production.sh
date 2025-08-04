#!/bin/bash

# =============================================================================
# 自動生成短影音系統 - 生產環境部署腳本
# =============================================================================

set -e  # 遇到錯誤立即退出

# 顏色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查必要工具
check_prerequisites() {
    log_info "檢查部署環境..."
    
    # 檢查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝，請先安裝 Docker"
        exit 1
    fi
    
    # 檢查 Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安裝，請先安裝 Docker Compose"
        exit 1
    fi
    
    # 檢查生產環境配置檔案
    if [ ! -f ".env.production" ]; then
        log_error "生產環境配置檔案 .env.production 不存在"
        log_info "請複製 .env.production.template 並填入實際配置"
        exit 1
    fi
    
    log_success "環境檢查完成"
}

# 備份資料庫
backup_database() {
    log_info "備份現有資料庫..."
    
    if docker ps | grep -q "postgres"; then
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        docker exec -t postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > "backups/${BACKUP_FILE}"
        log_success "資料庫備份完成: backups/${BACKUP_FILE}"
    else
        log_warning "未找到執行中的 PostgreSQL 容器，跳過備份"
    fi
}

# 停止現有服務
stop_services() {
    log_info "停止現有服務..."
    
    # 優雅停止服務
    if [ -f "docker-compose.yml" ]; then
        docker-compose down --remove-orphans
    fi
    
    if [ -f "docker-compose.prod.yml" ]; then
        docker-compose -f docker-compose.prod.yml down --remove-orphans
    fi
    
    log_success "服務停止完成"
}

# 拉取最新映像檔
pull_images() {
    log_info "拉取最新映像檔..."
    
    docker-compose -f docker-compose.prod.yml pull
    
    log_success "映像檔更新完成"
}

# 構建服務映像檔
build_services() {
    log_info "構建服務映像檔..."
    
    # 構建所有服務
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    log_success "服務構建完成"
}

# 創建必要的目錄
create_directories() {
    log_info "創建必要的目錄..."
    
    # 創建資料目錄
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p data/minio
    mkdir -p logs
    mkdir -p backups
    mkdir -p certs
    
    # 設定權限
    chmod 755 data/postgres data/redis data/minio
    chmod 700 certs
    
    log_success "目錄創建完成"
}

# 設定 SSL 憑證
setup_ssl() {
    log_info "設定 SSL 憑證..."
    
    if [ ! -f "certs/domain.crt" ] || [ ! -f "certs/domain.key" ]; then
        log_warning "未找到 SSL 憑證，產生自簽憑證用於測試..."
        
        # 產生自簽憑證（僅用於測試）
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout certs/domain.key \
            -out certs/domain.crt \
            -subj "/C=TW/ST=Taiwan/L=Taipei/O=AutoVideo/CN=localhost"
        
        chmod 600 certs/domain.key
        chmod 644 certs/domain.crt
        
        log_warning "已產生自簽憑證，生產環境請使用有效的 SSL 憑證"
    else
        log_success "SSL 憑證已存在"
    fi
}

# 初始化資料庫
init_database() {
    log_info "初始化資料庫..."
    
    # 啟動資料庫服務
    docker-compose -f docker-compose.prod.yml up -d postgres redis
    
    # 等待資料庫啟動
    log_info "等待資料庫啟動..."
    sleep 30
    
    # 執行資料庫初始化腳本
    if [ -f "scripts/init-db.sql" ]; then
        docker exec -i postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < scripts/init-db.sql
        log_success "資料庫初始化完成"
    fi
}

# 啟動所有服務
start_services() {
    log_info "啟動生產環境服務..."
    
    # 設定環境變數
    export COMPOSE_FILE=docker-compose.prod.yml
    export COMPOSE_PROJECT_NAME=auto-video-prod
    
    # 啟動所有服務
    docker-compose -f docker-compose.prod.yml up -d
    
    log_success "服務啟動完成"
}

# 等待服務啟動
wait_for_services() {
    log_info "等待服務啟動..."
    
    # 等待 API Gateway 啟動
    for i in {1..30}; do
        if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "API Gateway 已啟動"
            break
        fi
        
        if [ $i -eq 30 ]; then
            log_error "API Gateway 啟動超時"
            exit 1
        fi
        
        log_info "等待 API Gateway 啟動... ($i/30)"
        sleep 10
    done
}

# 執行健康檢查
health_check() {
    log_info "執行健康檢查..."
    
    # 檢查各服務狀態
    services=("api-gateway" "auth-service" "data-service" "ai-service" "video-service" "social-service" "trend-service" "scheduler-service")
    
    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.prod.yml ps | grep -q "${service}.*Up"; then
            log_success "${service} 運行正常"
        else
            log_error "${service} 運行異常"
            docker-compose -f docker-compose.prod.yml logs --tail=20 ${service}
        fi
    done
    
    # 檢查資料庫連接
    if docker exec postgres pg_isready -U ${POSTGRES_USER} > /dev/null 2>&1; then
        log_success "PostgreSQL 連接正常"
    else
        log_error "PostgreSQL 連接失敗"
    fi
    
    # 檢查 Redis 連接
    if docker exec redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis 連接正常"
    else
        log_error "Redis 連接失敗"
    fi
}

# 設定監控
setup_monitoring() {
    log_info "設定監控服務..."
    
    # 啟動監控服務
    if [ -f "docker-compose.monitoring.yml" ]; then
        docker-compose -f docker-compose.monitoring.yml up -d
        log_success "監控服務已啟動"
        log_info "Grafana: http://localhost:3001"
        log_info "Prometheus: http://localhost:9090"
    else
        log_warning "監控配置檔案不存在，跳過監控設定"
    fi
}

# 顯示部署資訊
show_deployment_info() {
    log_success "🎉 生產環境部署完成！"
    echo ""
    echo "服務訪問資訊:"
    echo "  • 主要 API: https://localhost (或您的域名)"
    echo "  • API Gateway: http://localhost:8000"
    echo "  • MinIO Console: http://localhost:9001"
    echo "  • Grafana: http://localhost:3001"
    echo "  • Prometheus: http://localhost:9090"
    echo ""
    echo "管理命令:"
    echo "  • 查看服務狀態: docker-compose -f docker-compose.prod.yml ps"
    echo "  • 查看日誌: docker-compose -f docker-compose.prod.yml logs -f [service-name]"
    echo "  • 停止服務: docker-compose -f docker-compose.prod.yml down"
    echo "  • 重啟服務: docker-compose -f docker-compose.prod.yml restart [service-name]"
    echo ""
    log_warning "重要提醒:"
    echo "  1. 請確保已替換 .env.production 中的所有密鑰和密碼"
    echo "  2. 生產環境請使用有效的 SSL 憑證"
    echo "  3. 建議設定定期資料庫備份"
    echo "  4. 監控各服務的資源使用情況"
}

# 主要部署流程
main() {
    log_info "開始生產環境部署..."
    
    # 載入環境變數
    if [ -f ".env.production" ]; then
        source .env.production
    fi
    
    # 執行部署步驟
    check_prerequisites
    create_directories
    setup_ssl
    
    # 如果有現有服務，先備份
    backup_database
    stop_services
    
    # 構建和啟動服務
    pull_images
    build_services
    init_database
    start_services
    
    # 等待和檢查
    wait_for_services
    health_check
    
    # 設定監控
    setup_monitoring
    
    # 顯示部署資訊
    show_deployment_info
}

# 錯誤處理
trap 'log_error "部署過程中發生錯誤，請檢查日誌"; exit 1' ERR

# 執行主函數
main "$@"