#!/bin/bash

# ===========================================
# Auto Video Generation System - 統一部署腳本
# Phase 2 & 3 整合部署自動化腳本
# ===========================================

set -euo pipefail

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 部署選項
DEPLOYMENT_TYPE="${1:-docker}"  # docker, k8s, dev
ENVIRONMENT="${2:-development}"  # development, staging, production
VERBOSE="${VERBOSE:-false}"

# 專案根目錄
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

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
    exit 1
}

log_step() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# 顯示使用說明
show_usage() {
    cat << EOF
使用方法: $0 [部署類型] [環境]

部署類型:
  docker    - Docker Compose 部署 (預設)
  k8s       - Kubernetes 部署
  dev       - 開發環境快速啟動

環境:
  development - 開發環境 (預設)
  staging     - 測試環境
  production  - 生產環境

範例:
  $0 docker development     # Docker 開發環境
  $0 k8s production        # Kubernetes 生產環境
  $0 dev                   # 開發環境快速啟動

環境變數:
  VERBOSE=true             # 顯示詳細輸出
  SKIP_BUILD=true          # 跳過 Docker 映像構建
  FORCE_RECREATE=true      # 強制重新建立容器
EOF
}

# 檢查依賴
check_dependencies() {
    log_step "檢查依賴工具"
    
    local missing_tools=()
    
    # 檢查 Docker
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    # 檢查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        missing_tools+=("docker-compose")
    fi
    
    # 如果是 Kubernetes 部署，檢查 kubectl
    if [[ "$DEPLOYMENT_TYPE" == "k8s" ]]; then
        if ! command -v kubectl &> /dev/null; then
            missing_tools+=("kubectl")
        fi
    fi
    
    # 檢查 Python
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "缺少必要工具: ${missing_tools[*]}"
    fi
    
    log_success "所有依賴工具已安裝"
}

# 設定環境配置
setup_environment() {
    log_step "設定環境配置"
    
    # 檢查 .env 檔案
    if [[ ! -f ".env" ]]; then
        log_warning ".env 檔案不存在，從範本複製"
        cp .env.template .env
        log_info "請編輯 .env 檔案並設定必要的環境變數"
        
        # 自動設定基本配置
        sed -i "s/ENVIRONMENT=development/ENVIRONMENT=$ENVIRONMENT/g" .env
        
        if [[ "$ENVIRONMENT" == "production" ]]; then
            sed -i "s/DEBUG=true/DEBUG=false/g" .env
            sed -i "s/LOG_LEVEL=debug/LOG_LEVEL=info/g" .env
        fi
    fi
    
    # 檢查必要的環境變數
    source .env
    
    local required_vars=("POSTGRES_PASSWORD" "JWT_SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "環境變數 $var 未設定"
        fi
    done
    
    log_success "環境配置完成"
}

# 準備 Phase 2 資料庫系統
prepare_database() {
    log_step "準備 Phase 2 統一資料庫系統"
    
    # 檢查 Alembic 配置
    if [[ ! -f "alembic.ini" ]]; then
        log_error "Alembic 配置檔案不存在"
    fi
    
    # 檢查模型定義
    if [[ ! -d "auto_generate_video_fold6/models" ]]; then
        log_error "資料庫模型目錄不存在"
    fi
    
    # 檢查遷移腳本
    if [[ ! -f "scripts/db-migration-manager.py" ]]; then
        log_error "資料庫遷移管理腳本不存在"
    fi
    
    log_success "Phase 2 資料庫系統準備完成"
}

# Docker Compose 部署
deploy_docker() {
    log_step "執行 Docker Compose 部署"
    
    local compose_file="docker-compose.unified.yml"
    local compose_args=()
    
    # 設定 compose 參數
    if [[ "$ENVIRONMENT" == "production" ]]; then
        compose_args+=("-f" "$compose_file" "-f" "auto_generate_video_fold6/docker/docker-compose.prod.yml")
    else
        compose_args+=("-f" "$compose_file")
    fi
    
    # 添加監控服務
    if [[ "${ENABLE_MONITORING:-false}" == "true" ]]; then
        compose_args+=("--profile" "monitoring")
    fi
    
    # 構建映像 (如果需要)
    if [[ "${SKIP_BUILD:-false}" != "true" ]]; then
        log_info "構建 Docker 映像..."
        docker-compose "${compose_args[@]}" build
    fi
    
    # 停止現有服務 (如果需要)
    if [[ "${FORCE_RECREATE:-false}" == "true" ]]; then
        log_info "停止現有服務..."
        docker-compose "${compose_args[@]}" down
    fi
    
    # 啟動基礎設施服務
    log_info "啟動基礎設施服務 (PostgreSQL, Redis, MinIO)..."
    docker-compose "${compose_args[@]}" up -d postgres redis minio
    
    # 等待資料庫準備完成
    log_info "等待 PostgreSQL 準備完成..."
    timeout 60 bash -c 'until docker-compose -f docker-compose.unified.yml exec -T postgres pg_isready -U postgres; do sleep 2; done'
    
    # 執行資料庫遷移
    log_info "執行資料庫遷移..."
    docker-compose "${compose_args[@]}" up migrations
    
    # 啟動應用服務
    log_info "啟動應用服務..."
    docker-compose "${compose_args[@]}" up -d
    
    # 等待服務啟動
    sleep 10
    
    # 健康檢查
    log_info "執行健康檢查..."
    check_docker_health "${compose_args[@]}"
    
    log_success "Docker Compose 部署完成"
}

# Kubernetes 部署
deploy_kubernetes() {
    log_step "執行 Kubernetes 部署"
    
    local k8s_manifest="k8s/unified-deployment.yaml"
    
    # 檢查 Kubernetes 連接
    if ! kubectl cluster-info &> /dev/null; then
        log_error "無法連接到 Kubernetes 集群"
    fi
    
    # 應用 Kubernetes 配置
    log_info "部署 Kubernetes 資源..."
    kubectl apply -f "$k8s_manifest"
    
    # 等待資料庫準備完成
    log_info "等待 PostgreSQL 準備完成..."
    kubectl wait --for=condition=Ready pod -l app=postgres -n auto-video-generation --timeout=300s
    
    # 等待資料庫遷移完成
    log_info "等待資料庫遷移完成..."
    kubectl wait --for=condition=Complete job/database-migration -n auto-video-generation --timeout=600s
    
    # 等待應用服務準備完成
    log_info "等待應用服務準備完成..."
    kubectl rollout status deployment/api-gateway -n auto-video-generation
    kubectl rollout status deployment/auth-service -n auto-video-generation
    kubectl rollout status deployment/video-service -n auto-video-generation
    
    # 健康檢查
    log_info "執行健康檢查..."
    check_k8s_health
    
    log_success "Kubernetes 部署完成"
}

# 開發環境快速啟動
deploy_dev() {
    log_step "開發環境快速啟動"
    
    # 設定開發環境變數
    export ENVIRONMENT=development
    export DEBUG=true
    export LOG_LEVEL=debug
    
    # 啟動基礎服務
    log_info "啟動基礎服務..."
    docker-compose -f docker-compose.unified.yml up -d postgres redis minio
    
    # 等待服務準備完成
    timeout 30 bash -c 'until docker-compose -f docker-compose.unified.yml exec -T postgres pg_isready -U postgres; do sleep 2; done'
    
    # 執行資料庫遷移
    log_info "執行資料庫遷移..."
    python scripts/db-migration-manager.py create-db
    python scripts/db-migration-manager.py init
    alembic upgrade head
    
    log_info "開發環境已準備完成！"
    log_info "資料庫: postgresql://postgres:password@localhost:5432/auto_video_generation"
    log_info "Redis: redis://localhost:6379/0"
    log_info "MinIO: http://localhost:9000 (minioadmin/minioadmin123)"
    
    log_success "開發環境啟動完成"
}

# Docker 健康檢查
check_docker_health() {
    local compose_args=("$@")
    local services=("postgres" "redis" "minio" "api-gateway")
    
    for service in "${services[@]}"; do
        if docker-compose "${compose_args[@]}" ps "$service" | grep -q "Up"; then
            log_success "$service 服務運行正常"
        else
            log_warning "$service 服務可能未正常運行"
        fi
    done
    
    # 檢查 API 端點
    if curl -f -s "http://localhost:8000/health" > /dev/null; then
        log_success "API Gateway 健康檢查通過"
    else
        log_warning "API Gateway 健康檢查失敗"
    fi
}

# Kubernetes 健康檢查
check_k8s_health() {
    # 檢查 Pod 狀態
    log_info "檢查 Pod 狀態..."
    kubectl get pods -n auto-video-generation
    
    # 檢查服務端點
    log_info "檢查服務端點..."
    kubectl get services -n auto-video-generation
    
    # 檢查 Ingress
    if kubectl get ingress -n auto-video-generation &> /dev/null; then
        log_info "檢查 Ingress..."
        kubectl get ingress -n auto-video-generation
    fi
}

# 顯示部署結果
show_deployment_info() {
    log_step "部署完成資訊"
    
    case "$DEPLOYMENT_TYPE" in
        "docker")
            log_info "Docker Compose 部署完成"
            log_info "前端: http://localhost:3000"
            log_info "API Gateway: http://localhost:8000"
            log_info "MinIO Console: http://localhost:9001"
            if [[ "${ENABLE_MONITORING:-false}" == "true" ]]; then
                log_info "Prometheus: http://localhost:9090"
                log_info "Grafana: http://localhost:3001"
            fi
            ;;
        "k8s")
            log_info "Kubernetes 部署完成"
            log_info "使用以下命令檢查狀態:"
            log_info "  kubectl get pods -n auto-video-generation"
            log_info "  kubectl get services -n auto-video-generation"
            ;;
        "dev")
            log_info "開發環境準備完成"
            log_info "現在可以啟動個別服務進行開發"
            ;;
    esac
    
    log_success "🎉 部署流程完成！"
}

# 主執行邏輯
main() {
    # 顯示標題
    echo -e "${BLUE}"
    echo "=============================================="
    echo "  Auto Video Generation System 統一部署工具  "
    echo "  Phase 2 & 3 整合部署自動化                  "
    echo "=============================================="
    echo -e "${NC}"
    
    # 檢查參數
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        show_usage
        exit 0
    fi
    
    # 執行部署流程
    check_dependencies
    setup_environment
    prepare_database
    
    case "$DEPLOYMENT_TYPE" in
        "docker")
            deploy_docker
            ;;
        "k8s")
            deploy_kubernetes
            ;;
        "dev")
            deploy_dev
            ;;
        *)
            log_error "不支援的部署類型: $DEPLOYMENT_TYPE"
            show_usage
            exit 1
            ;;
    esac
    
    show_deployment_info
}

# 錯誤處理
trap 'log_error "部署過程中發生錯誤"' ERR

# 執行主函數
main "$@"