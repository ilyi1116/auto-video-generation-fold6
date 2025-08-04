#!/bin/bash

# ====================================================================
# Auto Video 系統生產環境部署腳本
# ====================================================================

set -e  # 遇到錯誤時退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${PURPLE}🔸 $1${NC}"
}

# 全域變數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ENV="${1:-production}"
NAMESPACE="auto-video"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-auto-video}"
VERSION="${VERSION:-1.0.0}"

# 顯示用法
usage() {
    echo "用法: $0 [environment] [options]"
    echo ""
    echo "環境選項:"
    echo "  production  - 生產環境部署 (預設)"
    echo "  staging     - 測試環境部署"
    echo "  development - 開發環境部署"
    echo ""
    echo "選項:"
    echo "  --skip-build    跳過 Docker 構建"
    echo "  --skip-push     跳過 Docker 推送"
    echo "  --skip-migrate  跳過資料庫遷移"
    echo "  --help          顯示此幫助"
    echo ""
    echo "環境變數:"
    echo "  DOCKER_REGISTRY - Docker 註冊表前綴 (預設: auto-video)"
    echo "  VERSION        - 應用版本標籤 (預設: 1.0.0)"
    echo "  KUBECONFIG     - Kubernetes 配置檔案路徑"
    echo ""
    echo "範例:"
    echo "  $0 production                    # 完整生產部署"
    echo "  $0 staging --skip-build          # 測試部署，跳過構建"
    echo "  VERSION=1.1.0 $0 production      # 指定版本部署"
}

# 解析命令行參數
SKIP_BUILD=false
SKIP_PUSH=false
SKIP_MIGRATE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-push)
            SKIP_PUSH=true
            shift
            ;;
        --skip-migrate)
            SKIP_MIGRATE=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        production|staging|development)
            DEPLOYMENT_ENV="$1"
            shift
            ;;
        *)
            log_error "未知參數: $1"
            usage
            exit 1
            ;;
    esac
done

# 檢查先決條件
check_prerequisites() {
    log_step "檢查部署先決條件..."
    
    # 檢查必要工具
    local tools=("docker" "kubectl" "helm")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool 未安裝或不在 PATH 中"
            exit 1
        fi
    done
    
    # 檢查 Kubernetes 連接
    if ! kubectl cluster-info &> /dev/null; then
        log_error "無法連接到 Kubernetes 集群"
        log_info "請檢查 KUBECONFIG 或 kubectl 配置"
        exit 1
    fi
    
    # 檢查 Docker 是否運行
    if ! docker info &> /dev/null; then
        log_error "Docker 未運行或無訪問權限"
        exit 1
    fi
    
    # 檢查環境配置檔案
    local env_file="$PROJECT_ROOT/.env.$DEPLOYMENT_ENV"
    if [[ ! -f "$env_file" ]]; then
        log_error "環境配置檔案不存在: $env_file"
        exit 1
    fi
    
    log_success "先決條件檢查通過"
}

# 載入環境變數
load_environment() {
    log_step "載入 $DEPLOYMENT_ENV 環境配置..."
    
    local env_file="$PROJECT_ROOT/.env.$DEPLOYMENT_ENV"
    if [[ -f "$env_file" ]]; then
        export $(cat "$env_file" | grep -v '^#' | xargs)
        log_success "環境配置載入完成"
    else
        log_warning "環境配置檔案不存在: $env_file"
    fi
}

# 構建 Docker 映像
build_docker_images() {
    if [[ "$SKIP_BUILD" == "true" ]]; then
        log_warning "跳過 Docker 映像構建"
        return 0
    fi
    
    log_step "構建 Docker 映像..."
    
    cd "$PROJECT_ROOT"
    
    # 構建所有服務的 Docker 映像
    local services=(
        "api-gateway"
        "auth-service"
        "data-service"
        "inference-service"
        "video-service"
        "ai-service"
        "social-service"
        "trend-service"
        "scheduler-service"
        "storage-service"
        "training-worker"
    )
    
    # 構建前端
    log_info "構建前端映像..."
    docker build -t "$DOCKER_REGISTRY/frontend:$VERSION" \
        -f frontend/Dockerfile frontend/
    
    # 構建後端服務
    for service in "${services[@]}"; do
        if [[ -d "services/$service" ]]; then
            log_info "構建 $service 映像..."
            docker build -t "$DOCKER_REGISTRY/$service:$VERSION" \
                -f "services/$service/Dockerfile" "services/$service/"
        else
            log_warning "$service 目錄不存在，跳過構建"
        fi
    done
    
    log_success "Docker 映像構建完成"
}

# 推送 Docker 映像
push_docker_images() {
    if [[ "$SKIP_PUSH" == "true" ]]; then
        log_warning "跳過 Docker 映像推送"
        return 0
    fi
    
    log_step "推送 Docker 映像到註冊表..."
    
    # 登錄到 Docker 註冊表 (如果需要)
    if [[ -n "$DOCKER_REGISTRY_URL" ]] && [[ -n "$DOCKER_REGISTRY_USERNAME" ]]; then
        echo "$DOCKER_REGISTRY_PASSWORD" | docker login "$DOCKER_REGISTRY_URL" \
            -u "$DOCKER_REGISTRY_USERNAME" --password-stdin
    fi
    
    # 推送前端映像
    docker push "$DOCKER_REGISTRY/frontend:$VERSION"
    
    # 推送所有服務映像
    local services=(
        "api-gateway" "auth-service" "data-service" "inference-service"
        "video-service" "ai-service" "social-service" "trend-service"
        "scheduler-service" "storage-service" "training-worker"
    )
    
    for service in "${services[@]}"; do
        if docker images | grep -q "$DOCKER_REGISTRY/$service:$VERSION"; then
            log_info "推送 $service:$VERSION..."
            docker push "$DOCKER_REGISTRY/$service:$VERSION"
        fi
    done
    
    log_success "Docker 映像推送完成"
}

# 創建命名空間
create_namespace() {
    log_step "創建 Kubernetes 命名空間..."
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_info "命名空間 $NAMESPACE 已存在"
    else
        kubectl apply -f "$PROJECT_ROOT/k8s/namespace.yaml"
        log_success "命名空間 $NAMESPACE 創建完成"
    fi
}

# 部署配置和密鑰
deploy_configs_and_secrets() {
    log_step "部署配置和密鑰..."
    
    cd "$PROJECT_ROOT"
    
    # 應用 ConfigMap
    kubectl apply -f k8s/configmap.yaml
    
    # 應用 Secrets (確保已正確配置)
    if [[ -f "k8s/secrets.yaml" ]]; then
        kubectl apply -f k8s/secrets.yaml
    else
        log_warning "secrets.yaml 不存在，請手動創建密鑰"
    fi
    
    log_success "配置和密鑰部署完成"
}

# 部署服務
deploy_services() {
    log_step "部署 Kubernetes 服務..."
    
    cd "$PROJECT_ROOT"
    
    # 應用服務定義
    kubectl apply -f k8s/services.yaml
    
    log_success "服務部署完成"
}

# 部署應用
deploy_applications() {
    log_step "部署應用程式..."
    
    cd "$PROJECT_ROOT"
    
    # 更新部署配置中的映像版本
    sed -i.bak "s|image: auto-video/|image: $DOCKER_REGISTRY/|g" k8s/deployments.yaml
    sed -i.bak "s|:1.0.0|:$VERSION|g" k8s/deployments.yaml
    
    # 應用部署配置
    kubectl apply -f k8s/deployments.yaml
    
    # 恢復原始配置
    mv k8s/deployments.yaml.bak k8s/deployments.yaml
    
    log_success "應用程式部署完成"
}

# 部署 Ingress
deploy_ingress() {
    log_step "部署 Ingress 配置..."
    
    cd "$PROJECT_ROOT"
    
    if [[ -f "k8s/ingress.yaml" ]]; then
        kubectl apply -f k8s/ingress.yaml
        log_success "Ingress 部署完成"
    else
        log_warning "ingress.yaml 不存在，跳過 Ingress 部署"
    fi
}

# 部署自動擴展配置
deploy_hpa() {
    log_step "部署水平自動擴展配置..."
    
    cd "$PROJECT_ROOT"
    
    if [[ -f "k8s/hpa.yaml" ]]; then
        kubectl apply -f k8s/hpa.yaml
        log_success "HPA 部署完成"
    else
        log_warning "hpa.yaml 不存在，跳過 HPA 部署"
    fi
}

# 資料庫遷移
run_database_migration() {
    if [[ "$SKIP_MIGRATE" == "true" ]]; then
        log_warning "跳過資料庫遷移"
        return 0
    fi
    
    log_step "執行資料庫遷移..."
    
    # 等待資料庫服務準備就緒
    log_info "等待 PostgreSQL 服務準備就緒..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgres \
        --namespace="$NAMESPACE" --timeout=300s
    
    # 執行遷移任務
    local migration_job="database-migration-$(date +%s)"
    
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: $migration_job
  namespace: $NAMESPACE
spec:
  template:
    spec:
      containers:
      - name: migration
        image: $DOCKER_REGISTRY/auth-service:$VERSION
        command: ["alembic", "upgrade", "head"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: auto-video-secrets
              key: database-url
      restartPolicy: Never
  backoffLimit: 3
EOF
    
    # 等待遷移完成
    kubectl wait --for=condition=complete job/$migration_job \
        --namespace="$NAMESPACE" --timeout=600s
    
    # 清理遷移任務
    kubectl delete job/$migration_job --namespace="$NAMESPACE"
    
    log_success "資料庫遷移完成"
}

# 驗證部署
verify_deployment() {
    log_step "驗證部署狀態..."
    
    # 檢查所有 Pod 是否運行
    log_info "檢查 Pod 狀態..."
    kubectl get pods --namespace="$NAMESPACE" -o wide
    
    # 等待所有部署準備就緒
    local deployments=(
        "api-gateway" "auth-service" "data-service" "inference-service"
        "video-service" "ai-service" "social-service" "trend-service"
        "scheduler-service" "storage-service" "frontend" "nginx"
    )
    
    for deployment in "${deployments[@]}"; do
        if kubectl get deployment "$deployment" --namespace="$NAMESPACE" &> /dev/null; then
            log_info "等待 $deployment 部署準備就緒..."
            kubectl rollout status deployment/"$deployment" --namespace="$NAMESPACE" --timeout=300s
        fi
    done
    
    # 檢查服務狀態
    log_info "檢查服務狀態..."
    kubectl get services --namespace="$NAMESPACE"
    
    # 健康檢查
    log_info "執行健康檢查..."
    if kubectl get service nginx-service --namespace="$NAMESPACE" &> /dev/null; then
        local service_ip=$(kubectl get service nginx-service --namespace="$NAMESPACE" \
            -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        
        if [[ -n "$service_ip" ]]; then
            log_info "測試服務連接性: http://$service_ip/health"
            if curl -f -s "http://$service_ip/health" > /dev/null; then
                log_success "健康檢查通過"
            else
                log_warning "健康檢查失敗，但部署已完成"
            fi
        fi
    fi
    
    log_success "部署驗證完成"
}

# 顯示部署資訊
show_deployment_info() {
    log_step "部署資訊摘要"
    
    echo ""
    echo "🎉 Auto Video 系統部署完成！"
    echo ""
    echo "環境: $DEPLOYMENT_ENV"
    echo "版本: $VERSION"
    echo "命名空間: $NAMESPACE"
    echo ""
    
    # 顯示訪問資訊
    if kubectl get ingress --namespace="$NAMESPACE" &> /dev/null; then
        echo "🌐 訪問地址:"
        kubectl get ingress --namespace="$NAMESPACE" \
            -o custom-columns=NAME:.metadata.name,HOSTS:.spec.rules[*].host,ADDRESS:.status.loadBalancer.ingress[*].ip
        echo ""
    fi
    
    # 顯示重要命令
    echo "📋 常用管理命令:"
    echo "  查看 Pod 狀態:    kubectl get pods -n $NAMESPACE"
    echo "  查看服務狀態:    kubectl get services -n $NAMESPACE"
    echo "  查看日誌:        kubectl logs -f deployment/api-gateway -n $NAMESPACE"
    echo "  擴展服務:        kubectl scale deployment api-gateway --replicas=5 -n $NAMESPACE"
    echo "  回滾部署:        kubectl rollout undo deployment/api-gateway -n $NAMESPACE"
    echo ""
    
    log_info "部署完成！請檢查所有服務是否正常運行。"
}

# 錯誤處理
cleanup_on_error() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "部署過程中發生錯誤 (退出碼: $exit_code)"
        log_info "正在清理資源..."
        
        # 可以在這裡添加清理邏輯
        # kubectl delete -f k8s/ --ignore-not-found=true
        
        log_info "如需回滾，請運行: ./scripts/rollback.sh"
    fi
    exit $exit_code
}

# 主函數
main() {
    echo "🚀 Auto Video 系統部署腳本"
    echo "================================"
    echo "環境: $DEPLOYMENT_ENV"
    echo "版本: $VERSION"
    echo "開始時間: $(date)"
    echo ""
    
    # 設置錯誤處理
    trap cleanup_on_error EXIT
    
    # 執行部署步驟
    check_prerequisites
    load_environment
    build_docker_images
    push_docker_images
    create_namespace
    deploy_configs_and_secrets
    deploy_services
    deploy_applications
    deploy_ingress
    deploy_hpa
    run_database_migration
    verify_deployment
    show_deployment_info
    
    # 移除錯誤處理
    trap - EXIT
    
    log_success "部署流程完成！"
}

# 執行主函數
main "$@"