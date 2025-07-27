#!/bin/bash

# ====================================================================
# Auto Video 系統測試執行腳本
# 自動化執行所有前端和後端測試
# ====================================================================

set -e  # 遇到錯誤即退出

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 獲取腳本目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 預設參數
RUN_FRONTEND=true
RUN_BACKEND=true
RUN_E2E=false
GENERATE_COVERAGE=true
PARALLEL=false
VERBOSE=false
FAIL_FAST=false

# 解析命令列參數
while [[ $# -gt 0 ]]; do
    case $1 in
        --frontend-only)
            RUN_FRONTEND=true
            RUN_BACKEND=false
            shift
            ;;
        --backend-only)
            RUN_FRONTEND=false
            RUN_BACKEND=true
            shift
            ;;
        --e2e)
            RUN_E2E=true
            shift
            ;;
        --no-coverage)
            GENERATE_COVERAGE=false
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --fail-fast)
            FAIL_FAST=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --frontend-only    只執行前端測試"
            echo "  --backend-only     只執行後端測試"
            echo "  --e2e             執行端對端測試"
            echo "  --no-coverage     不生成覆蓋率報告"
            echo "  --parallel        並行執行測試"
            echo "  --verbose         詳細輸出"
            echo "  --fail-fast       遇到失敗立即停止"
            echo "  --help           顯示此幫助訊息"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

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

# 檢查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 檢查依賴
check_dependencies() {
    log_info "檢查測試依賴..."
    
    if [[ "$RUN_FRONTEND" == true ]]; then
        if ! command_exists npm; then
            log_error "npm 未安裝，無法執行前端測試"
            exit 1
        fi
        
        if ! command_exists node; then
            log_error "Node.js 未安裝，無法執行前端測試"
            exit 1
        fi
    fi
    
    if [[ "$RUN_BACKEND" == true ]]; then
        if ! command_exists python3; then
            log_error "Python 3 未安裝，無法執行後端測試"
            exit 1
        fi
        
        if ! command_exists pytest; then
            log_error "pytest 未安裝，請先執行: pip install pytest"
            exit 1
        fi
    fi
    
    log_success "依賴檢查完成"
}

# 設定測試環境
setup_test_environment() {
    log_info "設定測試環境..."
    
    # 設定環境變數
    export NODE_ENV=test
    export TESTING=true
    export DATABASE_URL="sqlite+aiosqlite:///:memory:"
    export REDIS_URL="redis://localhost:6379/1"
    export JWT_SECRET="test-secret-key-for-testing-only"
    export DISABLE_EXTERNAL_APIS=true
    
    # 創建測試報告目錄
    mkdir -p "$PROJECT_ROOT/test-results"
    mkdir -p "$PROJECT_ROOT/coverage-reports"
    
    log_success "測試環境設定完成"
}

# 執行前端測試
run_frontend_tests() {
    if [[ "$RUN_FRONTEND" != true ]]; then
        return 0
    fi
    
    log_info "執行前端測試..."
    cd "$PROJECT_ROOT/frontend"
    
    # 檢查是否已安裝依賴
    if [[ ! -d "node_modules" ]]; then
        log_info "安裝前端依賴..."
        npm ci
    fi
    
    local test_cmd=""
    local coverage_cmd=""
    
    if [[ "$GENERATE_COVERAGE" == true ]]; then
        coverage_cmd="--coverage"
    fi
    
    if [[ "$FAIL_FAST" == true ]]; then
        test_cmd="$test_cmd --bail"
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        test_cmd="$test_cmd --verbose"
    fi
    
    # 執行單元測試
    log_info "執行前端單元測試..."
    if ! npm run test:unit $coverage_cmd -- $test_cmd; then
        log_error "前端單元測試失敗"
        return 1
    fi
    
    # 執行組件測試
    log_info "執行前端組件測試..."
    if ! npm run test:component $coverage_cmd -- $test_cmd; then
        log_error "前端組件測試失敗"
        return 1
    fi
    
    # 執行整合測試
    log_info "執行前端整合測試..."
    if ! npm run test:integration $coverage_cmd -- $test_cmd; then
        log_error "前端整合測試失敗"
        return 1
    fi
    
    # 程式碼檢查
    log_info "執行前端程式碼檢查..."
    if ! npm run lint; then
        log_error "前端程式碼檢查失敗"
        return 1
    fi
    
    # TypeScript 檢查
    log_info "執行前端 TypeScript 檢查..."
    if ! npm run check; then
        log_error "前端 TypeScript 檢查失敗"
        return 1
    fi
    
    # 複製覆蓋率報告
    if [[ "$GENERATE_COVERAGE" == true && -d "coverage" ]]; then
        cp -r coverage/* "$PROJECT_ROOT/coverage-reports/" 2>/dev/null || true
    fi
    
    cd "$PROJECT_ROOT"
    log_success "前端測試完成"
    return 0
}

# 執行後端測試
run_backend_tests() {
    if [[ "$RUN_BACKEND" != true ]]; then
        return 0
    fi
    
    log_info "執行後端測試..."
    cd "$PROJECT_ROOT"
    
    local pytest_args=""
    
    if [[ "$GENERATE_COVERAGE" == true ]]; then
        pytest_args="$pytest_args --cov=services --cov-report=html:coverage-reports/backend --cov-report=xml:coverage-reports/backend-coverage.xml --cov-report=term-missing"
    fi
    
    if [[ "$FAIL_FAST" == true ]]; then
        pytest_args="$pytest_args -x"
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        pytest_args="$pytest_args -v"
    fi
    
    if [[ "$PARALLEL" == true ]]; then
        pytest_args="$pytest_args -n auto"
    fi
    
    # 執行所有後端服務測試
    log_info "執行後端服務測試..."
    
    local failed_services=()
    
    for service_dir in "$PROJECT_ROOT"/services/*/; do
        if [[ -d "$service_dir/tests" ]]; then
            service_name=$(basename "$service_dir")
            log_info "測試 $service_name 服務..."
            
            cd "$service_dir"
            
            # 檢查是否有 requirements.txt
            if [[ -f "requirements.txt" ]]; then
                # 安裝依賴（如果需要）
                if [[ ! -d "venv" ]]; then
                    log_info "為 $service_name 創建虛擬環境..."
                    python3 -m venv venv
                    source venv/bin/activate
                    pip install -r requirements.txt
                    if [[ -f "requirements-dev.txt" ]]; then
                        pip install -r requirements-dev.txt
                    fi
                else
                    source venv/bin/activate
                fi
            fi
            
            # 執行測試
            if ! pytest tests/ $pytest_args; then
                log_error "$service_name 服務測試失敗"
                failed_services+=("$service_name")
                if [[ "$FAIL_FAST" == true ]]; then
                    cd "$PROJECT_ROOT"
                    return 1
                fi
            else
                log_success "$service_name 服務測試通過"
            fi
            
            # 反啟動虛擬環境
            if [[ -n "$VIRTUAL_ENV" ]]; then
                deactivate
            fi
            
            cd "$PROJECT_ROOT"
        fi
    done
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log_error "以下服務測試失敗: ${failed_services[*]}"
        return 1
    fi
    
    log_success "後端測試完成"
    return 0
}

# 執行端對端測試
run_e2e_tests() {
    if [[ "$RUN_E2E" != true ]]; then
        return 0
    fi
    
    log_info "執行端對端測試..."
    cd "$PROJECT_ROOT/frontend"
    
    # 檢查是否需要啟動服務
    local need_services=true
    
    if command_exists docker-compose; then
        log_info "使用 Docker Compose 啟動測試環境..."
        docker-compose -f docker-compose.test.yml up -d
        sleep 30  # 等待服務啟動
        need_services=false
    else
        log_warning "未找到 Docker Compose，請確保測試環境已手動啟動"
    fi
    
    # 執行 E2E 測試
    local e2e_cmd="npm run test:e2e"
    
    if [[ "$VERBOSE" == true ]]; then
        e2e_cmd="$e2e_cmd -- --reporter=spec"
    fi
    
    if ! $e2e_cmd; then
        log_error "端對端測試失敗"
        
        # 清理
        if [[ "$need_services" == false ]]; then
            docker-compose -f docker-compose.test.yml down
        fi
        
        return 1
    fi
    
    # 清理
    if [[ "$need_services" == false ]]; then
        log_info "停止測試環境..."
        docker-compose -f docker-compose.test.yml down
    fi
    
    cd "$PROJECT_ROOT"
    log_success "端對端測試完成"
    return 0
}

# 生成測試報告
generate_test_report() {
    log_info "生成測試報告..."
    
    local report_file="$PROJECT_ROOT/test-results/test-report-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "$report_file" << EOF
# Auto Video 系統測試報告

**生成時間**: $(date)
**測試配置**:
- 前端測試: $RUN_FRONTEND
- 後端測試: $RUN_BACKEND
- 端對端測試: $RUN_E2E
- 覆蓋率報告: $GENERATE_COVERAGE
- 並行執行: $PARALLEL

## 測試結果

EOF

    if [[ "$RUN_FRONTEND" == true ]]; then
        echo "### 前端測試" >> "$report_file"
        if [[ -f "$PROJECT_ROOT/frontend/coverage/coverage-summary.json" ]]; then
            echo "覆蓋率報告: [查看詳細報告](../coverage-reports/frontend/index.html)" >> "$report_file"
        fi
        echo "" >> "$report_file"
    fi
    
    if [[ "$RUN_BACKEND" == true ]]; then
        echo "### 後端測試" >> "$report_file"
        if [[ -f "$PROJECT_ROOT/coverage-reports/backend-coverage.xml" ]]; then
            echo "覆蓋率報告: [查看詳細報告](../coverage-reports/backend/index.html)" >> "$report_file"
        fi
        echo "" >> "$report_file"
    fi
    
    if [[ "$RUN_E2E" == true ]]; then
        echo "### 端對端測試" >> "$report_file"
        if [[ -d "$PROJECT_ROOT/frontend/playwright-report" ]]; then
            echo "測試報告: [查看詳細報告](../frontend/playwright-report/index.html)" >> "$report_file"
        fi
        echo "" >> "$report_file"
    fi
    
    echo "測試報告已生成: $report_file"
}

# 主函數
main() {
    log_info "開始執行 Auto Video 系統測試"
    log_info "專案根目錄: $PROJECT_ROOT"
    
    # 檢查依賴
    check_dependencies
    
    # 設定環境
    setup_test_environment
    
    local overall_success=true
    
    # 並行執行測試（如果啟用）
    if [[ "$PARALLEL" == true && "$RUN_FRONTEND" == true && "$RUN_BACKEND" == true ]]; then
        log_info "並行執行前端和後端測試..."
        
        run_frontend_tests &
        frontend_pid=$!
        
        run_backend_tests &
        backend_pid=$!
        
        wait $frontend_pid
        frontend_result=$?
        
        wait $backend_pid
        backend_result=$?
        
        if [[ $frontend_result -ne 0 || $backend_result -ne 0 ]]; then
            overall_success=false
        fi
    else
        # 順序執行測試
        if ! run_frontend_tests; then
            overall_success=false
        fi
        
        if ! run_backend_tests; then
            overall_success=false
        fi
    fi
    
    # 執行 E2E 測試
    if ! run_e2e_tests; then
        overall_success=false
    fi
    
    # 生成報告
    if [[ "$GENERATE_COVERAGE" == true ]]; then
        generate_test_report
    fi
    
    # 總結
    if [[ "$overall_success" == true ]]; then
        log_success "所有測試通過！ ✅"
        exit 0
    else
        log_error "部分測試失敗！ ❌"
        exit 1
    fi
}

# 捕獲中斷信號
trap 'log_warning "測試被中斷"; exit 130' INT TERM

# 執行主函數
main "$@"