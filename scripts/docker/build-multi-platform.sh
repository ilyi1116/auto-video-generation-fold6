#!/bin/bash
##############################################################################
# Docker 多平台構建腳本
# 支援 AMD64 和 ARM64 (M4 Max) 平台
##############################################################################

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 配置變數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REGISTRY="${REGISTRY:-localhost:5000}"
PROJECT_NAME="${PROJECT_NAME:-voice-clone}"
VERSION="${VERSION:-latest}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"

# 服務列表
SERVICES=(
    "api-gateway"
    "auth-service"
    "ai-service"
    "video-service"
    "storage-service"
)

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

log_header() {
    echo -e "${PURPLE}${NC}"
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║$(printf "%62s" "$1")║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# 顯示使用說明
show_help() {
    cat << EOF
Docker 多平台構建腳本

使用方法:
    $0 [選項] [服務名稱...]

選項:
    -r, --registry REGISTRY  - Docker registry (預設: localhost:5000)
    -v, --version VERSION    - 映像版本標籤 (預設: latest)
    -p, --platforms PLATFORMS - 目標平台，逗號分隔 (預設: linux/amd64,linux/arm64)
    --push                   - 推送到 registry
    --cache                  - 啟用構建快取
    --parallel               - 並行構建所有服務
    -h, --help              - 顯示此說明

服務名稱:
    api-gateway    - API 閘道服務
    auth-service   - 認證服務
    ai-service     - AI 處理服務
    video-service  - 影片生成服務
    storage-service - 存儲服務
    all           - 構建所有服務 (預設)

範例:
    $0 api-gateway --push
    $0 all --registry ghcr.io/username --version v1.2.3
    $0 ai-service video-service --platforms linux/arm64 --cache

EOF
}

# 檢查先決條件
check_prerequisites() {
    log_info "檢查構建先決條件..."
    
    # 檢查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝"
        return 1
    fi
    
    # 檢查 Docker Buildx
    if ! docker buildx version &> /dev/null; then
        log_error "Docker Buildx 未啟用"
        return 1
    fi
    
    # 檢查 Docker 守護程序
    if ! docker info &> /dev/null; then
        log_error "Docker 守護程序未運行"
        return 1
    fi
    
    log_success "Docker 環境檢查通過"
    
    # 檢查並創建 buildx builder
    if ! docker buildx ls | grep -q "multi-platform"; then
        log_info "創建多平台 builder..."
        docker buildx create --name multi-platform --driver docker-container --platform ${PLATFORMS}
        docker buildx use multi-platform
        docker buildx inspect --bootstrap
        log_success "多平台 builder 已創建"
    else
        docker buildx use multi-platform
        log_success "使用現有多平台 builder"
    fi
    
    return 0
}

# 構建單個服務
build_service() {
    local service_name="$1"
    local service_dir="${PROJECT_ROOT}/src/services/${service_name}"
    local dockerfile="${service_dir}/Dockerfile"
    
    if [ ! -f "$dockerfile" ]; then
        log_error "Dockerfile 不存在: $dockerfile"
        return 1
    fi
    
    log_header "構建服務: $service_name"
    
    local image_name="${REGISTRY}/${PROJECT_NAME}-${service_name}:${VERSION}"
    local build_args=(
        "--platform" "$PLATFORMS"
        "--file" "$dockerfile"
        "--tag" "$image_name"
    )
    
    # 添加構建參數
    if [ "$USE_CACHE" = true ]; then
        build_args+=(
            "--cache-from" "type=registry,ref=${REGISTRY}/${PROJECT_NAME}-${service_name}:cache"
            "--cache-to" "type=registry,ref=${REGISTRY}/${PROJECT_NAME}-${service_name}:cache,mode=max"
        )
    fi
    
    # 添加推送選項
    if [ "$PUSH_IMAGES" = true ]; then
        build_args+=("--push")
    else
        build_args+=("--load")
    fi
    
    # 添加構建上下文特定參數
    case $service_name in
        "ai-service")
            build_args+=(
                "--build-arg" "TORCH_VERSION=2.2.0"
                "--build-arg" "PYTHON_ARCH=arm64"
            )
            ;;
        "video-service")
            build_args+=(
                "--build-arg" "FFMPEG_ARCH=arm64"
            )
            ;;
    esac
    
    # 添加多階段構建優化
    build_args+=(
        "--build-arg" "BUILDKIT_INLINE_CACHE=1"
        "--build-arg" "BUILDPLATFORM=linux/arm64"
        "--build-arg" "TARGETPLATFORM=linux/arm64"
    )
    
    log_info "構建命令: docker buildx build ${build_args[*]} ${service_dir}"
    
    # 執行構建
    if docker buildx build "${build_args[@]}" "$service_dir"; then
        log_success "$service_name 構建成功"
        
        # 顯示映像資訊
        if [ "$PUSH_IMAGES" != true ]; then
            docker images | grep "${PROJECT_NAME}-${service_name}" | head -5
        fi
        
        return 0
    else
        log_error "$service_name 構建失敗"
        return 1
    fi
}

# 並行構建所有服務
build_services_parallel() {
    local services=("$@")
    local pids=()
    local failed_services=()
    
    log_header "並行構建 ${#services[@]} 個服務"
    
    for service in "${services[@]}"; do
        log_info "開始構建 $service (背景程序)..."
        build_service "$service" &
        pids+=($!)
    done
    
    # 等待所有構建完成
    for i in "${!pids[@]}"; do
        local pid=${pids[$i]}
        local service=${services[$i]}
        
        if wait $pid; then
            log_success "$service 構建完成"
        else
            log_error "$service 構建失敗"
            failed_services+=("$service")
        fi
    done
    
    # 檢查失敗的服務
    if [ ${#failed_services[@]} -gt 0 ]; then
        log_error "以下服務構建失敗: ${failed_services[*]}"
        return 1
    fi
    
    log_success "所有服務構建成功"
    return 0
}

# 驗證構建結果
verify_build() {
    log_header "驗證構建結果"
    
    local all_success=true
    
    for service in "${SERVICES[@]}"; do
        local image_name="${REGISTRY}/${PROJECT_NAME}-${service}:${VERSION}"
        
        if [ "$PUSH_IMAGES" = true ]; then
            # 檢查遠程 registry
            if docker manifest inspect "$image_name" &> /dev/null; then
                log_success "$service 映像已推送到 registry"
            else
                log_error "$service 映像推送失敗"
                all_success=false
            fi
        else
            # 檢查本地映像
            if docker images -q "$image_name" &> /dev/null; then
                log_success "$service 映像已構建到本地"
            else
                log_error "$service 本地映像不存在"
                all_success=false
            fi
        fi
    done
    
    if [ "$all_success" = true ]; then
        log_success "所有映像驗證通過"
        return 0
    else
        log_error "部分映像驗證失敗"
        return 1
    fi
}

# 生成構建報告
generate_build_report() {
    local report_file="${PROJECT_ROOT}/build-report-$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# Docker 多平台構建報告

## 構建配置

- **構建時間**: $(date -Iseconds)
- **平台**: $PLATFORMS
- **Registry**: $REGISTRY
- **版本**: $VERSION
- **服務數量**: ${#SERVICES[@]}

## 構建結果

EOF
    
    for service in "${SERVICES[@]}"; do
        local image_name="${REGISTRY}/${PROJECT_NAME}-${service}:${VERSION}"
        cat >> "$report_file" << EOF
### $service

- **映像名稱**: \`$image_name\`
- **平台支援**: $PLATFORMS
EOF
        
        if [ "$PUSH_IMAGES" = true ]; then
            echo "- **狀態**: 已推送到 registry" >> "$report_file"
        else
            echo "- **狀態**: 已構建到本地" >> "$report_file"
        fi
        
        echo "" >> "$report_file"
    done
    
    cat >> "$report_file" << EOF
## 使用說明

### 本地運行
\`\`\`bash
docker run --platform linux/arm64 $REGISTRY/$PROJECT_NAME-api-gateway:$VERSION
\`\`\`

### Docker Compose
\`\`\`bash
export REGISTRY=$REGISTRY
export VERSION=$VERSION
docker-compose up
\`\`\`

生成時間: $(date)
EOF
    
    log_success "構建報告已生成: $report_file"
}

# 清理函數
cleanup() {
    log_info "清理構建資源..."
    
    # 清理暫存檔案
    docker system prune -f --filter "label=stage=build" 2>/dev/null || true
    
    # 清理未使用的映像
    if [ "$CLEANUP_IMAGES" = true ]; then
        docker image prune -f 2>/dev/null || true
    fi
}

# 主函數
main() {
    local services_to_build=()
    local parallel_build=false
    
    # 預設值
    PUSH_IMAGES=false
    USE_CACHE=false
    CLEANUP_IMAGES=false
    
    # 解析命令行參數
    while [[ $# -gt 0 ]]; do
        case $1 in
            -r|--registry)
                REGISTRY="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -p|--platforms)
                PLATFORMS="$2"
                shift 2
                ;;
            --push)
                PUSH_IMAGES=true
                shift
                ;;
            --cache)
                USE_CACHE=true
                shift
                ;;
            --parallel)
                parallel_build=true
                shift
                ;;
            --cleanup)
                CLEANUP_IMAGES=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            all)
                services_to_build=("${SERVICES[@]}")
                shift
                ;;
            api-gateway|auth-service|ai-service|video-service|storage-service)
                services_to_build+=("$1")
                shift
                ;;
            *)
                log_error "未知參數: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 如果沒有指定服務，構建所有服務
    if [ ${#services_to_build[@]} -eq 0 ]; then
        services_to_build=("${SERVICES[@]}")
    fi
    
    # 設置清理陷阱
    trap cleanup EXIT
    
    log_header "Docker 多平台構建"
    
    # 顯示構建配置
    log_info "構建配置:"
    log_info "  - Registry: $REGISTRY"
    log_info "  - 版本: $VERSION"
    log_info "  - 平台: $PLATFORMS"
    log_info "  - 服務: ${services_to_build[*]}"
    log_info "  - 推送: $PUSH_IMAGES"
    log_info "  - 快取: $USE_CACHE"
    log_info "  - 並行: $parallel_build"
    
    # 檢查先決條件
    if ! check_prerequisites; then
        log_error "先決條件檢查失敗"
        exit 1
    fi
    
    # 構建服務
    if [ "$parallel_build" = true ]; then
        if ! build_services_parallel "${services_to_build[@]}"; then
            log_error "並行構建失敗"
            exit 1
        fi
    else
        for service in "${services_to_build[@]}"; do
            if ! build_service "$service"; then
                log_error "服務 $service 構建失敗"
                exit 1
            fi
        done
    fi
    
    # 驗證構建結果
    verify_build
    
    # 生成構建報告
    generate_build_report
    
    log_success "Docker 多平台構建完成！"
}

# 運行主函數
main "$@"