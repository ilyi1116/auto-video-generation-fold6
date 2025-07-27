#!/bin/bash

# ====================================================================
# Auto Video 系統回滾腳本
# ====================================================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 日誌函數
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${PURPLE}🔸 $1${NC}"; }

# 變數
NAMESPACE="${NAMESPACE:-auto-video}"
ROLLBACK_REVISION="${1}"

# 顯示用法
usage() {
    echo "用法: $0 [revision]"
    echo ""
    echo "參數:"
    echo "  revision  - 回滾到指定版本 (可選，預設為上一版本)"
    echo ""
    echo "範例:"
    echo "  $0        # 回滾到上一版本"
    echo "  $0 3      # 回滾到版本 3"
    echo ""
    echo "查看部署歷史:"
    echo "  kubectl rollout history deployment/api-gateway -n $NAMESPACE"
}

# 檢查先決條件
check_prerequisites() {
    log_step "檢查回滾先決條件..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl 未安裝"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "無法連接到 Kubernetes 集群"
        exit 1
    fi
    
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "命名空間 $NAMESPACE 不存在"
        exit 1
    fi
    
    log_success "先決條件檢查通過"
}

# 顯示部署歷史
show_deployment_history() {
    log_step "顯示部署歷史..."
    
    local deployments=(
        "api-gateway" "auth-service" "data-service" "inference-service"
        "video-service" "ai-service" "social-service" "trend-service"
        "scheduler-service" "storage-service" "frontend" "nginx"
    )
    
    for deployment in "${deployments[@]}"; do
        if kubectl get deployment "$deployment" -n "$NAMESPACE" &> /dev/null; then
            echo ""
            log_info "部署歷史: $deployment"
            kubectl rollout history deployment/"$deployment" -n "$NAMESPACE"
        fi
    done
}

# 執行回滾
perform_rollback() {
    log_step "執行回滾操作..."
    
    local deployments=(
        "api-gateway" "auth-service" "data-service" "inference-service"
        "video-service" "ai-service" "social-service" "trend-service"
        "scheduler-service" "storage-service" "frontend" "nginx"
    )
    
    for deployment in "${deployments[@]}"; do
        if kubectl get deployment "$deployment" -n "$NAMESPACE" &> /dev/null; then
            log_info "回滾 $deployment..."
            
            if [[ -n "$ROLLBACK_REVISION" ]]; then
                kubectl rollout undo deployment/"$deployment" \
                    --to-revision="$ROLLBACK_REVISION" -n "$NAMESPACE"
            else
                kubectl rollout undo deployment/"$deployment" -n "$NAMESPACE"
            fi
            
            # 等待回滾完成
            kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout=300s
        else
            log_warning "$deployment 不存在，跳過"
        fi
    done
    
    log_success "回滾操作完成"
}

# 驗證回滾
verify_rollback() {
    log_step "驗證回滾狀態..."
    
    # 檢查所有 Pod 狀態
    log_info "檢查 Pod 狀態..."
    kubectl get pods -n "$NAMESPACE" -o wide
    
    # 檢查服務健康狀態
    log_info "執行健康檢查..."
    
    # 等待所有 Pod 就緒
    kubectl wait --for=condition=ready pod \
        -l app.kubernetes.io/part-of=auto-video-system \
        -n "$NAMESPACE" --timeout=300s
    
    # 測試 API 健康檢查
    if kubectl get service nginx-service -n "$NAMESPACE" &> /dev/null; then
        local service_ip=$(kubectl get service nginx-service -n "$NAMESPACE" \
            -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        
        if [[ -n "$service_ip" ]]; then
            log_info "測試服務連接: http://$service_ip/health"
            if timeout 10 curl -f -s "http://$service_ip/health" > /dev/null; then
                log_success "健康檢查通過"
            else
                log_warning "健康檢查失敗，請手動檢查服務狀態"
            fi
        fi
    fi
    
    log_success "回滾驗證完成"
}

# 顯示回滾後資訊
show_rollback_info() {
    log_step "回滾資訊摘要"
    
    echo ""
    echo "🔄 Auto Video 系統回滾完成！"
    echo ""
    echo "命名空間: $NAMESPACE"
    if [[ -n "$ROLLBACK_REVISION" ]]; then
        echo "回滾到版本: $ROLLBACK_REVISION"
    else
        echo "回滾到: 上一版本"
    fi
    echo "完成時間: $(date)"
    echo ""
    
    # 顯示當前部署狀態
    log_info "當前部署狀態:"
    kubectl get deployments -n "$NAMESPACE" -o wide
    
    echo ""
    log_info "如需進一步操作："
    echo "  查看詳細狀態: kubectl get all -n $NAMESPACE"
    echo "  查看 Pod 日誌: kubectl logs -f deployment/api-gateway -n $NAMESPACE"
    echo "  重新部署:     ./scripts/deploy.sh"
}

# 確認回滾操作
confirm_rollback() {
    if [[ -n "$ROLLBACK_REVISION" ]]; then
        log_warning "即將回滾到版本 $ROLLBACK_REVISION"
    else
        log_warning "即將回滾到上一版本"
    fi
    
    echo ""
    read -p "確定要執行回滾操作嗎？(y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "回滾操作已取消"
        exit 0
    fi
}

# 主函數
main() {
    echo "🔄 Auto Video 系統回滾腳本"
    echo "================================"
    echo "開始時間: $(date)"
    echo ""
    
    # 處理幫助參數
    if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
        usage
        exit 0
    fi
    
    # 檢查先決條件
    check_prerequisites
    
    # 顯示部署歷史
    show_deployment_history
    
    # 確認回滾操作
    confirm_rollback
    
    # 執行回滾
    perform_rollback
    
    # 驗證回滾
    verify_rollback
    
    # 顯示回滾資訊
    show_rollback_info
    
    log_success "回滾流程完成！"
}

# 執行主函數
main "$@"