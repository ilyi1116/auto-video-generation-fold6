#!/bin/bash
##############################################################################
# 負載測試運行腳本
# 自動化執行 K6 和 JMeter 負載測試
##############################################################################

set -e

# 顏色常數
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 配置變數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BASE_URL="${BASE_URL:-http://localhost:8000}"
TEST_DURATION="${TEST_DURATION:-300}"
VIRTUAL_USERS="${VIRTUAL_USERS:-50}"
RESULTS_DIR="${SCRIPT_DIR}/results/$(date +%Y%m%d_%H%M%S)"

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
負載測試運行腳本

使用方法:
    $0 [選項] [測試類型]

測試類型:
    k6          - 運行 K6 負載測試
    jmeter      - 運行 JMeter 負載測試  
    all         - 運行所有測試 (預設)

選項:
    -u, --url URL           - 目標伺服器 URL (預設: http://localhost:8000)
    -t, --duration SECONDS  - 測試持續時間秒數 (預設: 300)
    -v, --users NUMBER      - 虛擬用戶數量 (預設: 50)  
    -r, --results DIR       - 結果輸出目錄
    -h, --help             - 顯示此說明

範例:
    $0 k6 -u http://api.example.com -t 600 -v 100
    $0 jmeter --url http://localhost:8000 --duration 300
    $0 all

EOF
}

# 檢查先決條件
check_prerequisites() {
    log_info "檢查測試先決條件..."
    
    # 檢查系統是否運行
    if ! curl -s --max-time 5 "${BASE_URL}/health" > /dev/null 2>&1; then
        log_error "無法連接到 ${BASE_URL}，請確保系統正在運行"
        return 1
    fi
    
    log_success "系統健康檢查通過"
    
    # 檢查測試工具
    local tools_missing=0
    
    if ! command -v k6 &> /dev/null; then
        log_warning "K6 未安裝，將跳過 K6 測試"
        K6_AVAILABLE=false
    else
        K6_AVAILABLE=true
        log_success "K6 已安裝: $(k6 version --short)"
    fi
    
    if ! command -v jmeter &> /dev/null; then
        log_warning "JMeter 未安裝，將跳過 JMeter 測試"
        JMETER_AVAILABLE=false
    else
        JMETER_AVAILABLE=true
        local jmeter_version=$(jmeter --version 2>&1 | head -n1 | awk '{print $3}')
        log_success "JMeter 已安裝: $jmeter_version"
    fi
    
    # 檢查測試檔案
    if [ ! -f "${SCRIPT_DIR}/test-users.csv" ]; then
        log_error "測試用戶數據檔案不存在: ${SCRIPT_DIR}/test-users.csv"
        return 1
    fi
    
    if [ ! -f "${SCRIPT_DIR}/k6-load-test.js" ]; then
        log_error "K6 測試腳本不存在: ${SCRIPT_DIR}/k6-load-test.js"
        return 1
    fi
    
    if [ ! -f "${SCRIPT_DIR}/jmeter-test-plan.jmx" ]; then
        log_error "JMeter 測試計劃不存在: ${SCRIPT_DIR}/jmeter-test-plan.jmx"
        return 1
    fi
    
    return 0
}

# 準備測試環境
prepare_test_environment() {
    log_info "準備測試環境..."
    
    # 創建結果目錄
    mkdir -p "${RESULTS_DIR}"
    
    # 複製測試檔案到結果目錄
    cp "${SCRIPT_DIR}/test-users.csv" "${RESULTS_DIR}/"
    
    # 創建測試配置檔案
    cat > "${RESULTS_DIR}/test-config.json" << EOF
{
    "test_run_id": "$(uuidgen 2>/dev/null || date +%s)",
    "timestamp": "$(date -Iseconds)",
    "base_url": "${BASE_URL}",
    "test_duration": ${TEST_DURATION},
    "virtual_users": ${VIRTUAL_USERS},
    "environment": {
        "hostname": "$(hostname)",
        "os": "$(uname -s)",
        "arch": "$(uname -m)",
        "load_avg": "$(uptime | awk -F'load average:' '{print $2}' | sed 's/^[[:space:]]*//')"
    }
}
EOF
    
    log_success "測試環境準備完成: ${RESULTS_DIR}"
}

# 運行 K6 負載測試
run_k6_test() {
    if [ "$K6_AVAILABLE" != true ]; then
        log_warning "K6 不可用，跳過 K6 測試"
        return 0
    fi
    
    log_header "運行 K6 負載測試"
    
    local k6_options=(
        "--duration" "${TEST_DURATION}s"
        "--vus" "${VIRTUAL_USERS}"
        "--env" "BASE_URL=${BASE_URL}"
        "--out" "json=${RESULTS_DIR}/k6-results.json"
        "--out" "csv=${RESULTS_DIR}/k6-results.csv"
    )
    
    log_info "K6 測試參數:"
    log_info "  - 目標 URL: ${BASE_URL}"
    log_info "  - 測試時間: ${TEST_DURATION} 秒"
    log_info "  - 虛擬用戶: ${VIRTUAL_USERS}"
    log_info "  - 結果目錄: ${RESULTS_DIR}"
    
    # 運行 K6 測試
    if k6 run "${k6_options[@]}" "${SCRIPT_DIR}/k6-load-test.js" > "${RESULTS_DIR}/k6-console.log" 2>&1; then
        log_success "K6 測試完成"
        
        # 生成 K6 HTML 報告
        if command -v k6-html-reporter &> /dev/null; then
            k6-html-reporter "${RESULTS_DIR}/k6-results.json" -o "${RESULTS_DIR}/k6-report.html"
            log_success "K6 HTML 報告已生成: ${RESULTS_DIR}/k6-report.html"
        fi
    else
        log_error "K6 測試失敗，檢查日誌: ${RESULTS_DIR}/k6-console.log"
        return 1
    fi
}

# 運行 JMeter 負載測試
run_jmeter_test() {
    if [ "$JMETER_AVAILABLE" != true ]; then
        log_warning "JMeter 不可用，跳過 JMeter 測試"
        return 0
    fi
    
    log_header "運行 JMeter 負載測試"
    
    local jmeter_options=(
        "-n"  # 非 GUI 模式
        "-t" "${SCRIPT_DIR}/jmeter-test-plan.jmx"
        "-l" "${RESULTS_DIR}/jmeter-results.jtl"
        "-e"  # 生成 HTML 報告
        "-o" "${RESULTS_DIR}/jmeter-html-report"
        "-Jhost=$(echo ${BASE_URL} | sed 's|http://||' | sed 's|:.*||')"
        "-Jport=$(echo ${BASE_URL} | grep -o ':[0-9]*' | sed 's/://' || echo '80')"
        "-JtestUsers=${VIRTUAL_USERS}"
        "-JtestDuration=${TEST_DURATION}"
        "-Jtestdata.file=${RESULTS_DIR}/test-users.csv"
    )
    
    log_info "JMeter 測試參數:"
    log_info "  - 測試計劃: ${SCRIPT_DIR}/jmeter-test-plan.jmx"
    log_info "  - 目標 URL: ${BASE_URL}"
    log_info "  - 虛擬用戶: ${VIRTUAL_USERS}"
    log_info "  - 測試時間: ${TEST_DURATION} 秒"
    
    # 運行 JMeter 測試
    if jmeter "${jmeter_options[@]}" > "${RESULTS_DIR}/jmeter-console.log" 2>&1; then
        log_success "JMeter 測試完成"
        log_success "JMeter HTML 報告已生成: ${RESULTS_DIR}/jmeter-html-report/index.html"
    else
        log_error "JMeter 測試失敗，檢查日誌: ${RESULTS_DIR}/jmeter-console.log"
        return 1
    fi
}

# 生成統合報告
generate_summary_report() {
    log_header "生成測試結果統合報告"
    
    local summary_file="${RESULTS_DIR}/test-summary.md"
    
    cat > "${summary_file}" << EOF
# 負載測試結果報告

## 測試配置

- **測試時間**: $(date -Iseconds)
- **目標 URL**: ${BASE_URL}
- **測試持續時間**: ${TEST_DURATION} 秒
- **虛擬用戶數**: ${VIRTUAL_USERS}
- **測試環境**: $(hostname) - $(uname -s) $(uname -m)

## 測試結果

### K6 測試結果
EOF
    
    if [ -f "${RESULTS_DIR}/k6-results.json" ]; then
        cat >> "${summary_file}" << EOF

K6 測試已完成，詳細結果請查看：
- [K6 控制台日誌](./k6-console.log)
- [K6 JSON 結果](./k6-results.json)
- [K6 CSV 結果](./k6-results.csv)
EOF
        if [ -f "${RESULTS_DIR}/k6-report.html" ]; then
            echo "- [K6 HTML 報告](./k6-report.html)" >> "${summary_file}"
        fi
    else
        echo "K6 測試未運行或失敗" >> "${summary_file}"
    fi
    
    cat >> "${summary_file}" << EOF

### JMeter 測試結果
EOF
    
    if [ -f "${RESULTS_DIR}/jmeter-results.jtl" ]; then
        cat >> "${summary_file}" << EOF

JMeter 測試已完成，詳細結果請查看：
- [JMeter 控制台日誌](./jmeter-console.log)
- [JMeter 結果檔案](./jmeter-results.jtl)
- [JMeter HTML 報告](./jmeter-html-report/index.html)
EOF
    else
        echo "JMeter 測試未運行或失敗" >> "${summary_file}"
    fi
    
    cat >> "${summary_file}" << EOF

## 檔案清單

\`\`\`
$(find "${RESULTS_DIR}" -type f -exec basename {} \; | sort)
\`\`\`

## 建議

根據測試結果，請檢查以下指標：
1. **響應時間**: 95% 的請求應在 500ms 內完成
2. **錯誤率**: 應低於 1%
3. **吞吐量**: 根據業務需求評估
4. **資源使用**: 檢查 CPU、記憶體和網路使用情況

生成時間: $(date)
EOF
    
    log_success "統合報告已生成: ${summary_file}"
}

# 清理函數
cleanup() {
    log_info "清理暫存檔案..."
    # 在這裡添加任何必要的清理邏輯
}

# 主函數
main() {
    local test_type="all"
    
    # 解析命令行參數
    while [[ $# -gt 0 ]]; do
        case $1 in
            -u|--url)
                BASE_URL="$2"
                shift 2
                ;;
            -t|--duration)
                TEST_DURATION="$2"
                shift 2  
                ;;
            -v|--users)
                VIRTUAL_USERS="$2"
                shift 2
                ;;
            -r|--results)
                RESULTS_DIR="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            k6|jmeter|all)
                test_type="$1"
                shift
                ;;
            *)
                log_error "未知參數: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 設置清理陷阱
    trap cleanup EXIT
    
    log_header "聲音克隆系統負載測試"
    
    # 檢查先決條件
    if ! check_prerequisites; then
        log_error "先決條件檢查失敗"
        exit 1
    fi
    
    # 準備測試環境
    prepare_test_environment
    
    # 運行測試
    case $test_type in
        k6)
            run_k6_test
            ;;
        jmeter)
            run_jmeter_test
            ;;
        all)
            run_k6_test
            run_jmeter_test
            ;;
    esac
    
    # 生成統合報告
    generate_summary_report
    
    log_success "負載測試完成！結果保存在: ${RESULTS_DIR}"
    log_info "查看報告: cat ${RESULTS_DIR}/test-summary.md"
}

# 運行主函數
main "$@"