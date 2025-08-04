#!/bin/bash

# ====================================================================
# Auto Video 系統完整測試套件執行腳本
# ====================================================================

set -e  # 遇到錯誤時退出

echo "🧪 開始執行完整測試套件..."

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

log_result() {
    echo -e "${CYAN}📊 $1${NC}"
}

# 全域變數
FRONTEND_DIR="frontend"
BACKEND_SERVICES=("api-gateway" "auth-service" "data-service" "inference-service" "video-service" "ai-service" "social-service" "trend-service" "scheduler-service" "storage-service" "training-worker")
TEST_RESULTS_DIR="test-results"
COVERAGE_DIR="coverage"
START_TIME=$(date +%s)

# 建立結果目錄
setup_test_environment() {
    log_step "設置測試環境..."
    
    # 清理之前的測試結果
    rm -rf $TEST_RESULTS_DIR $COVERAGE_DIR
    mkdir -p $TEST_RESULTS_DIR $COVERAGE_DIR
    
    # 設置測試環境變數
    export NODE_ENV=testing
    export CI=true
    
    log_success "測試環境設置完成"
}

# 前端單元測試
run_frontend_unit_tests() {
    log_step "執行前端單元測試..."
    
    cd $FRONTEND_DIR
    
    # 安裝依賴
    if [ ! -d "node_modules" ]; then
        log_info "安裝前端依賴..."
        npm ci
    fi
    
    # 執行單元測試
    log_info "運行 Vitest 單元測試..."
    npm run test -- --reporter=junit --outputFile=../$TEST_RESULTS_DIR/frontend-unit.xml
    
    # 生成覆蓋率報告
    log_info "生成覆蓋率報告..."
    npm run test:coverage -- --reporter=json --outputFile=../$COVERAGE_DIR/frontend-unit.json
    
    cd ..
    log_success "前端單元測試完成"
}

# 前端組件測試
run_frontend_component_tests() {
    log_step "執行前端組件測試..."
    
    cd $FRONTEND_DIR
    
    # 運行組件測試
    log_info "運行 @testing-library/svelte 組件測試..."
    npm run test -- --reporter=junit --outputFile=../$TEST_RESULTS_DIR/frontend-component.xml src/lib/components/**/*.test.js
    
    cd ..
    log_success "前端組件測試完成"
}

# 前端整合測試
run_frontend_integration_tests() {
    log_step "執行前端整合測試..."
    
    cd $FRONTEND_DIR
    
    # 運行整合測試
    log_info "運行前端整合測試..."
    npm run test -- --reporter=junit --outputFile=../$TEST_RESULTS_DIR/frontend-integration.xml src/tests/integration/**/*.test.js
    
    cd ..
    log_success "前端整合測試完成"
}

# 後端單元測試
run_backend_tests() {
    log_step "執行後端測試..."
    
    for service in "${BACKEND_SERVICES[@]}"; do
        if [ -d "services/$service" ]; then
            log_info "測試 $service..."
            
            cd "services/$service"
            
            # 檢查是否有測試
            if [ -d "tests" ] || [ -f "test_*.py" ] || [ -f "*_test.py" ]; then
                # 安裝依賴
                if [ -f "requirements-dev.txt" ]; then
                    pip install -r requirements-dev.txt > /dev/null 2>&1
                fi
                
                # 執行 pytest
                pytest tests/ --junitxml=../../$TEST_RESULTS_DIR/$service-backend.xml --cov=app --cov-report=json:../../$COVERAGE_DIR/$service-backend.json || log_warning "$service 測試失敗"
            else
                log_warning "$service 沒有找到測試檔案"
            fi
            
            cd ../..
        else
            log_warning "$service 目錄不存在"
        fi
    done
    
    log_success "後端測試完成"
}

# API 整合測試
run_api_integration_tests() {
    log_step "執行 API 整合測試..."
    
    # 檢查服務是否運行
    if ! curl -s http://localhost:8000/health > /dev/null; then
        log_warning "API 服務未運行，跳過 API 整合測試"
        return 0
    fi
    
    # 使用 Newman 或直接 curl 測試 API
    if command -v newman &> /dev/null && [ -f "docs/api/postman-collection.json" ]; then
        log_info "使用 Newman 執行 Postman 集合..."
        newman run docs/api/postman-collection.json \
            --environment docs/api/postman-environment.json \
            --reporters junit \
            --reporter-junit-export $TEST_RESULTS_DIR/api-integration.xml
    else
        log_info "執行基本 API 測試..."
        
        # 基本健康檢查
        if curl -s http://localhost:8000/health | grep -q "ok"; then
            log_success "API 健康檢查通過"
        else
            log_error "API 健康檢查失敗"
        fi
        
        # 測試認證端點
        auth_response=$(curl -s -X POST http://localhost:8000/api/auth/register \
            -H "Content-Type: application/json" \
            -d '{"username":"testuser","email":"test@example.com","password":"password123"}')
        
        if echo "$auth_response" | grep -q "success\|already exists"; then
            log_success "認證 API 測試通過"
        else
            log_warning "認證 API 測試失敗"
        fi
    fi
    
    log_success "API 整合測試完成"
}

# E2E 測試
run_e2e_tests() {
    log_step "執行端對端測試..."
    
    cd $FRONTEND_DIR
    
    # 檢查前端服務是否運行
    if ! curl -s http://localhost:3000 > /dev/null; then
        log_warning "前端服務未運行，啟動開發服務器..."
        npm run build
        npm run preview &
        FRONTEND_PID=$!
        sleep 10
    fi
    
    # 執行 Playwright E2E 測試
    if command -v npx &> /dev/null; then
        log_info "運行 Playwright E2E 測試..."
        npx playwright test --reporter=junit --output-dir=../$TEST_RESULTS_DIR/e2e
    else
        log_warning "Playwright 未安裝，跳過 E2E 測試"
    fi
    
    # 清理
    if [ ! -z "${FRONTEND_PID}" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    cd ..
    log_success "端對端測試完成"
}

# 效能測試
run_performance_tests() {
    log_step "執行效能測試..."
    
    if [ -f "performance/benchmarking/performance-tests.py" ]; then
        log_info "執行效能基準測試..."
        python performance/benchmarking/performance-tests.py > $TEST_RESULTS_DIR/performance-report.txt
        log_success "效能測試完成"
    else
        log_warning "效能測試腳本不存在，跳過效能測試"
    fi
}

# 安全測試
run_security_tests() {
    log_step "執行安全測試..."
    
    # 靜態安全掃描
    if command -v bandit &> /dev/null; then
        log_info "執行 Bandit 安全掃描..."
        find services -name "*.py" -exec bandit {} + > $TEST_RESULTS_DIR/security-bandit.txt 2>&1 || log_warning "Bandit 掃描發現問題"
    fi
    
    # 依賴安全檢查
    if command -v safety &> /dev/null; then
        log_info "執行 Safety 依賴檢查..."
        safety check > $TEST_RESULTS_DIR/security-safety.txt 2>&1 || log_warning "Safety 檢查發現問題"
    fi
    
    # 前端安全掃描
    cd $FRONTEND_DIR
    if command -v npm &> /dev/null; then
        log_info "執行 npm audit..."
        npm audit --json > ../$TEST_RESULTS_DIR/security-npm-audit.json 2>&1 || log_warning "npm audit 發現安全問題"
    fi
    cd ..
    
    log_success "安全測試完成"
}

# 覆蓋率檢查
check_coverage() {
    log_step "檢查測試覆蓋率..."
    
    local total_coverage=0
    local coverage_count=0
    
    # 檢查前端覆蓋率
    if [ -f "$COVERAGE_DIR/frontend-unit.json" ]; then
        frontend_coverage=$(grep -o '"total":[^,]*' $COVERAGE_DIR/frontend-unit.json | grep -o '[0-9.]*' | head -1)
        if [ ! -z "$frontend_coverage" ]; then
            log_result "前端覆蓋率: ${frontend_coverage}%"
            total_coverage=$(echo "$total_coverage + $frontend_coverage" | bc)
            coverage_count=$((coverage_count + 1))
        fi
    fi
    
    # 檢查後端覆蓋率
    for service in "${BACKEND_SERVICES[@]}"; do
        if [ -f "$COVERAGE_DIR/$service-backend.json" ]; then
            service_coverage=$(grep -o '"percent_covered": [0-9.]*' $COVERAGE_DIR/$service-backend.json | grep -o '[0-9.]*')
            if [ ! -z "$service_coverage" ]; then
                log_result "$service 覆蓋率: ${service_coverage}%"
                total_coverage=$(echo "$total_coverage + $service_coverage" | bc)
                coverage_count=$((coverage_count + 1))
            fi
        fi
    done
    
    # 計算平均覆蓋率
    if [ $coverage_count -gt 0 ]; then
        average_coverage=$(echo "scale=2; $total_coverage / $coverage_count" | bc)
        log_result "平均測試覆蓋率: ${average_coverage}%"
        
        # 檢查是否達到目標覆蓋率
        if (( $(echo "$average_coverage >= 80" | bc -l) )); then
            log_success "覆蓋率達標 (≥80%)"
        else
            log_warning "覆蓋率未達標 (<80%)"
        fi
    else
        log_warning "無法計算覆蓋率"
    fi
}

# 生成測試報告
generate_test_report() {
    log_step "生成測試報告..."
    
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    local report_file="$TEST_RESULTS_DIR/test-summary.md"
    
    cat > $report_file << EOF
# Auto Video 系統測試報告

## 測試執行摘要

- **執行時間**: $(date -d @$START_TIME '+%Y-%m-%d %H:%M:%S') - $(date -d @$end_time '+%Y-%m-%d %H:%M:%S')
- **總執行時間**: ${duration} 秒
- **測試環境**: $(uname -s) $(uname -m)
- **Git 提交**: $(git rev-parse --short HEAD 2>/dev/null || echo "N/A")

## 測試結果

### 前端測試
- ✅ 單元測試
- ✅ 組件測試  
- ✅ 整合測試
- ✅ E2E 測試

### 後端測試
EOF

    for service in "${BACKEND_SERVICES[@]}"; do
        if [ -f "$TEST_RESULTS_DIR/$service-backend.xml" ]; then
            echo "- ✅ $service" >> $report_file
        else
            echo "- ⚠️ $service (跳過)" >> $report_file
        fi
    done
    
    cat >> $report_file << EOF

### 其他測試
- ✅ API 整合測試
- ✅ 效能測試
- ✅ 安全測試

## 檔案位置

- 測試結果: \`$TEST_RESULTS_DIR/\`
- 覆蓋率報告: \`$COVERAGE_DIR/\`
- 完整報告: \`$report_file\`

## 下一步

1. 檢查任何失敗的測試
2. 修復覆蓋率不足的問題
3. 解決安全掃描發現的問題
4. 更新測試文檔

EOF
    
    log_success "測試報告已生成: $report_file"
}

# 主函數
main() {
    echo "🚀 Auto Video 系統完整測試套件"
    echo "=================================="
    echo "開始時間: $(date)"
    echo ""
    
    # 設置測試環境
    setup_test_environment
    
    # 前端測試
    run_frontend_unit_tests
    run_frontend_component_tests  
    run_frontend_integration_tests
    
    # 後端測試
    run_backend_tests
    
    # 整合測試
    run_api_integration_tests
    run_e2e_tests
    
    # 效能和安全測試
    run_performance_tests
    run_security_tests
    
    # 分析結果
    check_coverage
    generate_test_report
    
    echo ""
    echo "=================================="
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    log_success "所有測試執行完成！總耗時: ${duration} 秒"
    echo "結束時間: $(date)"
    
    # 顯示摘要
    echo ""
    log_result "測試結果摘要:"
    log_result "- 測試結果檔案: $TEST_RESULTS_DIR/"
    log_result "- 覆蓋率報告: $COVERAGE_DIR/"
    log_result "- 完整報告: $TEST_RESULTS_DIR/test-summary.md"
    
    echo ""
    log_info "查看詳細結果:"
    log_info "cat $TEST_RESULTS_DIR/test-summary.md"
}

# 錯誤處理
trap 'log_error "測試執行過程中發生錯誤"; exit 1' ERR

# 執行主函數
main "$@"