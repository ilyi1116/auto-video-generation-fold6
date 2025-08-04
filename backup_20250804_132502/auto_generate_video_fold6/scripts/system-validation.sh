#!/bin/bash

# ====================================================================
# Auto Video 系統驗證腳本
# 檢查整個系統的完整性和配置正確性
# ====================================================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 日誌函數
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${PURPLE}🔸 $1${NC}"; }
log_result() { echo -e "${CYAN}📊 $1${NC}"; }

# 全域變數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VALIDATION_REPORT="$PROJECT_ROOT/system-validation-report.md"
ERRORS=0
WARNINGS=0
TOTAL_CHECKS=0

# 結果記錄函數
record_check() {
    local status="$1"
    local message="$2"
    local details="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    case "$status" in
        "PASS")
            log_success "$message"
            echo "- ✅ $message" >> "$VALIDATION_REPORT"
            ;;
        "FAIL")
            log_error "$message"
            echo "- ❌ $message" >> "$VALIDATION_REPORT"
            ERRORS=$((ERRORS + 1))
            if [[ -n "$details" ]]; then
                echo "  - 詳細資訊: $details" >> "$VALIDATION_REPORT"
            fi
            ;;
        "WARN")
            log_warning "$message"
            echo "- ⚠️ $message" >> "$VALIDATION_REPORT"
            WARNINGS=$((WARNINGS + 1))
            if [[ -n "$details" ]]; then
                echo "  - 詳細資訊: $details" >> "$VALIDATION_REPORT"
            fi
            ;;
    esac
}

# 初始化驗證報告
init_report() {
    cat > "$VALIDATION_REPORT" << EOF
# Auto Video 系統驗證報告

**生成時間**: $(date)
**Git 提交**: $(git rev-parse --short HEAD 2>/dev/null || echo "N/A")
**Git 分支**: $(git branch --show-current 2>/dev/null || echo "N/A")

## 驗證結果摘要

EOF
}

# 檢查必要的開發工具
check_development_tools() {
    log_step "檢查開發工具..."
    echo "" >> "$VALIDATION_REPORT"
    echo "### 🛠️ 開發工具檢查" >> "$VALIDATION_REPORT"
    echo "" >> "$VALIDATION_REPORT"
    
    local tools=("docker" "docker-compose" "node" "npm" "python3" "pip" "git" "kubectl")
    
    for tool in "${tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            local version=$($tool --version 2>/dev/null | head -n1 || echo "未知版本")
            record_check "PASS" "$tool 已安裝" "$version"
        else
            record_check "FAIL" "$tool 未安裝"
        fi
    done
}

# 檢查專案結構
check_project_structure() {
    log_step "檢查專案結構..."
    echo "" >> "$VALIDATION_REPORT"
    echo "### 📁 專案結構檢查" >> "$VALIDATION_REPORT"
    echo "" >> "$VALIDATION_REPORT"
    
    cd "$PROJECT_ROOT"
    
    # 必要的目錄
    local required_dirs=(
        "frontend"
        "services"
        "k8s"
        "docs"
        "scripts"
        "monitoring"
        "database"
        "security"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            record_check "PASS" "目錄 $dir 存在"
        else
            record_check "FAIL" "目錄 $dir 不存在"
        fi
    done
    
    # 檢查重要檔案
    local required_files=(
        "README.md"
        "Makefile"
        "docker-compose.yml"
        ".env.example"
        ".env.development"
        ".env.production"
        ".env.testing"
        ".gitignore"
        ".editorconfig"
        ".prettierrc"
        ".eslintrc.js"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            record_check "PASS" "檔案 $file 存在"
        else
            record_check "FAIL" "檔案 $file 不存在"
        fi
    done
}

# 檢查前端配置
check_frontend_configuration() {
    log_step "檢查前端配置..."
    echo "" >> "$VALIDATION_REPORT"
    echo "### 🎨 前端配置檢查" >> "$VALIDATION_REPORT"
    echo "" >> "$VALIDATION_REPORT"
    
    cd "$PROJECT_ROOT/frontend"
    
    # 檢查 package.json
    if [[ -f "package.json" ]]; then
        record_check "PASS" "package.json 存在"
        
        # 檢查必要的腳本
        local scripts=("dev" "build" "test" "lint" "format")
        for script in "${scripts[@]}"; do
            if jq -e ".scripts[\"$script\"]" package.json > /dev/null 2>&1; then
                record_check "PASS" "npm script '$script' 已定義"
            else
                record_check "WARN" "npm script '$script' 未定義"
            fi
        done
        
        # 檢查重要依賴
        local deps=("@sveltejs/kit" "svelte" "tailwindcss" "vite")
        for dep in "${deps[@]}"; do
            if jq -e ".dependencies[\"$dep\"] // .devDependencies[\"$dep\"]" package.json > /dev/null 2>&1; then
                record_check "PASS" "依賴 '$dep' 已安裝"
            else
                record_check "WARN" "依賴 '$dep' 未找到"
            fi
        done
    else
        record_check "FAIL" "package.json 不存在"
    fi
    
    # 檢查配置檔案
    local config_files=("vite.config.js" "svelte.config.js" "tailwind.config.js" "tsconfig.json")
    for config in "${config_files[@]}"; do
        if [[ -f "$config" ]]; then
            record_check "PASS" "配置檔案 $config 存在"
        else
            record_check "FAIL" "配置檔案 $config 不存在"
        fi
    done
    
    cd "$PROJECT_ROOT"
}

# 檢查後端服務
check_backend_services() {
    log_step "檢查後端服務..."
    echo "" >> "$VALIDATION_REPORT"
    echo "### 🔧 後端服務檢查" >> "$VALIDATION_REPORT"
    echo "" >> "$VALIDATION_REPORT"
    
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
    
    for service in "${services[@]}"; do
        local service_dir="$PROJECT_ROOT/services/$service"
        
        if [[ -d "$service_dir" ]]; then
            record_check "PASS" "服務目錄 $service 存在"
            
            # 檢查必要檔案
            if [[ -f "$service_dir/Dockerfile" ]]; then
                record_check "PASS" "$service Dockerfile 存在"
            else
                record_check "FAIL" "$service Dockerfile 不存在"
            fi
            
            if [[ -f "$service_dir/requirements.txt" ]]; then
                record_check "PASS" "$service requirements.txt 存在"
            else
                record_check "WARN" "$service requirements.txt 不存在"
            fi
            
            # 檢查主要應用檔案
            if [[ -f "$service_dir/main.py" ]] || [[ -f "$service_dir/app/main.py" ]]; then
                record_check "PASS" "$service 主應用檔案存在"
            else
                record_check "FAIL" "$service 主應用檔案不存在"
            fi
            
        else
            record_check "FAIL" "服務目錄 $service 不存在"
        fi
    done
}

# 檢查 Kubernetes 配置
check_kubernetes_configuration() {
    log_step "檢查 Kubernetes 配置..."
    echo "" >> "$VALIDATION_REPORT"
    echo "### ☸️ Kubernetes 配置檢查" >> "$VALIDATION_REPORT"
    echo "" >> "$VALIDATION_REPORT"
    
    cd "$PROJECT_ROOT/k8s"
    
    local k8s_files=(
        "namespace.yaml"
        "configmap.yaml"
        "secrets.yaml"
        "services.yaml"
        "deployments.yaml"
        "ingress.yaml"
        "hpa.yaml"
    )
    
    for file in "${k8s_files[@]}"; do
        if [[ -f "$file" ]]; then
            record_check "PASS" "K8s 配置 $file 存在"
            
            # 驗證 YAML 語法
            if kubectl dry-run=client --validate=true apply -f "$file" &> /dev/null; then
                record_check "PASS" "$file YAML 語法正確"
            else
                record_check "FAIL" "$file YAML 語法錯誤"
            fi
        else
            record_check "FAIL" "K8s 配置 $file 不存在"
        fi
    done
    
    cd "$PROJECT_ROOT"
}

# 檢查環境配置
check_environment_configuration() {
    log_step "檢查環境配置..."
    echo "" >> "$VALIDATION_REPORT"
    echo "### 🌍 環境配置檢查" >> "$VALIDATION_REPORT"
    echo "" >> "$VALIDATION_REPORT"
    
    local env_files=(".env.development" ".env.production" ".env.testing" ".env.example")
    
    for env_file in "${env_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$env_file" ]]; then
            record_check "PASS" "環境檔案 $env_file 存在"
            
            # 檢查重要環境變數
            local required_vars=(
                "NODE_ENV"
                "DATABASE_URL"
                "REDIS_URL"
                "JWT_SECRET"
            )
            
            for var in "${required_vars[@]}"; do
                if grep -q "^$var=" "$PROJECT_ROOT/$env_file"; then
                    record_check "PASS" "$env_file 包含 $var"
                else
                    record_check "WARN" "$env_file 缺少 $var"
                fi
            done
        else
            record_check "FAIL" "環境檔案 $env_file 不存在"
        fi
    done
}

# 檢查 Docker 配置
check_docker_configuration() {
    log_step "檢查 Docker 配置..."
    echo "" >> "$VALIDATION_REPORT"
    echo "### 🐳 Docker 配置檢查" >> "$VALIDATION_REPORT"
    echo "" >> "$VALIDATION_REPORT"
    
    cd "$PROJECT_ROOT"
    
    # 檢查 docker-compose 檔案
    local docker_files=(
        "docker-compose.yml"
        "docker-compose.dev.yml"
        "docker-compose.prod.yml"
        "docker-compose.monitoring.yml"
    )
    
    for file in "${docker_files[@]}"; do
        if [[ -f "$file" ]]; then
            record_check "PASS" "Docker 配置 $file 存在"
            
            # 驗證 Docker Compose 語法
            if docker-compose -f "$file" config &> /dev/null; then
                record_check "PASS" "$file 語法正確"
            else
                record_check "FAIL" "$file 語法錯誤"
            fi
        else
            record_check "WARN" "Docker 配置 $file 不存在"
        fi
    done
    
    # 檢查 .dockerignore
    if [[ -f ".dockerignore" ]]; then
        record_check "PASS" ".dockerignore 存在"
    else
        record_check "WARN" ".dockerignore 不存在"
    fi
}

# 檢查監控配置
check_monitoring_configuration() {
    log_step "檢查監控配置..."
    echo "" >> "$VALIDATION_REPORT"
    echo "### 📊 監控配置檢查" >> "$VALIDATION_REPORT"
    echo "" >> "$VALIDATION_REPORT"
    
    # 檢查監控目錄結構
    local monitoring_dirs=(
        "monitoring/prometheus"
        "monitoring/grafana"
        "monitoring/alertmanager"
    )
    
    for dir in "${monitoring_dirs[@]}"; do
        if [[ -d "$PROJECT_ROOT/$dir" ]]; then
            record_check "PASS" "監控目錄 $dir 存在"
        else
            record_check "WARN" "監控目錄 $dir 不存在"
        fi
    done
    
    # 檢查監控配置檔案
    local monitoring_files=(
        "monitoring/prometheus/prometheus.yml"
        "monitoring/grafana/dashboards/auto-video-overview.json"
        "monitoring/alertmanager/alertmanager.yml"
    )
    
    for file in "${monitoring_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            record_check "PASS" "監控配置 $file 存在"
        else
            record_check "WARN" "監控配置 $file 不存在"
        fi
    done
}

# 檢查安全配置
check_security_configuration() {
    log_step "檢查安全配置..."
    echo "" >> "$VALIDATION_REPORT"
    echo "### 🔒 安全配置檢查" >> "$VALIDATION_REPORT"
    echo "" >> "$VALIDATION_REPORT"
    
    # 檢查安全相關檔案
    local security_files=(
        "security/ssl/generate-certs.sh"
        "security/nginx/nginx.conf"
        "security/secrets-management/vault-config.json"
    )
    
    for file in "${security_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            record_check "PASS" "安全配置 $file 存在"
        else
            record_check "WARN" "安全配置 $file 不存在"
        fi
    done
    
    # 檢查敏感檔案是否在 .gitignore 中
    local sensitive_patterns=(
        "*.env"
        "*.key"
        "*.pem"
        "*.crt"
        "secrets.yaml"
    )
    
    if [[ -f "$PROJECT_ROOT/.gitignore" ]]; then
        for pattern in "${sensitive_patterns[@]}"; do
            if grep -q "$pattern" "$PROJECT_ROOT/.gitignore"; then
                record_check "PASS" "敏感檔案模式 '$pattern' 已在 .gitignore 中"
            else
                record_check "WARN" "敏感檔案模式 '$pattern' 未在 .gitignore 中"
            fi
        done
    fi
}

# 檢查測試配置
check_testing_configuration() {
    log_step "檢查測試配置..."
    echo "" >> "$VALIDATION_REPORT"
    echo "### 🧪 測試配置檢查" >> "$VALIDATION_REPORT"
    echo "" >> "$VALIDATION_REPORT"
    
    # 檢查前端測試
    if [[ -d "$PROJECT_ROOT/frontend" ]]; then
        cd "$PROJECT_ROOT/frontend"
        
        local test_configs=("vitest.config.js" "playwright.config.js")
        for config in "${test_configs[@]}"; do
            if [[ -f "$config" ]]; then
                record_check "PASS" "前端測試配置 $config 存在"
            else
                record_check "WARN" "前端測試配置 $config 不存在"
            fi
        done
        
        # 檢查測試目錄
        if [[ -d "src/lib/components/__tests__" ]]; then
            record_check "PASS" "前端測試目錄存在"
        else
            record_check "WARN" "前端測試目錄不存在"
        fi
    fi
    
    # 檢查後端測試
    local test_found=false
    for service_dir in "$PROJECT_ROOT"/services/*/; do
        if [[ -d "$service_dir/tests" ]]; then
            service_name=$(basename "$service_dir")
            record_check "PASS" "$service_name 測試目錄存在"
            test_found=true
        fi
    done
    
    if [[ "$test_found" == "false" ]]; then
        record_check "WARN" "後端服務缺少測試目錄"
    fi
    
    # 檢查測試腳本
    if [[ -f "$PROJECT_ROOT/scripts/run-all-tests.sh" ]]; then
        record_check "PASS" "完整測試腳本存在"
    else
        record_check "WARN" "完整測試腳本不存在"
    fi
    
    cd "$PROJECT_ROOT"
}

# 檢查 API 文檔
check_api_documentation() {
    log_step "檢查 API 文檔..."
    echo "" >> "$VALIDATION_REPORT"
    echo "### 📚 API 文檔檢查" >> "$VALIDATION_REPORT"
    echo "" >> "$VALIDATION_REPORT"
    
    if [[ -f "$PROJECT_ROOT/docs/api/openapi.yaml" ]]; then
        record_check "PASS" "OpenAPI 規格檔案存在"
        
        # 驗證 OpenAPI 語法
        if command -v swagger-validator &> /dev/null; then
            if swagger-validator "$PROJECT_ROOT/docs/api/openapi.yaml" &> /dev/null; then
                record_check "PASS" "OpenAPI 規格語法正確"
            else
                record_check "FAIL" "OpenAPI 規格語法錯誤"
            fi
        else
            record_check "WARN" "無法驗證 OpenAPI 語法 (swagger-validator 未安裝)"
        fi
    else
        record_check "FAIL" "OpenAPI 規格檔案不存在"
    fi
    
    # 檢查其他文檔
    local doc_files=(
        "README.md"
        "docs/README.md"
        "CLAUDE.md"
    )
    
    for doc in "${doc_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$doc" ]]; then
            record_check "PASS" "文檔 $doc 存在"
        else
            record_check "WARN" "文檔 $doc 不存在"
        fi
    done
}

# 檢查腳本執行權限
check_script_permissions() {
    log_step "檢查腳本執行權限..."
    echo "" >> "$VALIDATION_REPORT"
    echo "### 🔑 腳本權限檢查" >> "$VALIDATION_REPORT"
    echo "" >> "$VALIDATION_REPORT"
    
    local scripts=(
        "scripts/deploy.sh"
        "scripts/rollback.sh"
        "scripts/start-dev.sh"
        "scripts/backup-system.sh"
        "scripts/health-check.sh"
        "scripts/run-all-tests.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [[ -f "$PROJECT_ROOT/$script" ]]; then
            if [[ -x "$PROJECT_ROOT/$script" ]]; then
                record_check "PASS" "腳本 $script 可執行"
            else
                record_check "WARN" "腳本 $script 不可執行"
            fi
        else
            record_check "WARN" "腳本 $script 不存在"
        fi
    done
}

# 生成驗證報告摘要
generate_report_summary() {
    log_step "生成驗證報告摘要..."
    
    local success_rate=0
    if [[ $TOTAL_CHECKS -gt 0 ]]; then
        success_rate=$(( (TOTAL_CHECKS - ERRORS) * 100 / TOTAL_CHECKS ))
    fi
    
    cat >> "$VALIDATION_REPORT" << EOF

## 📊 驗證統計

- **總檢查項目**: $TOTAL_CHECKS
- **通過項目**: $((TOTAL_CHECKS - ERRORS - WARNINGS))
- **警告項目**: $WARNINGS
- **失敗項目**: $ERRORS
- **成功率**: ${success_rate}%

## 🎯 建議行動

EOF
    
    if [[ $ERRORS -gt 0 ]]; then
        echo "### ❌ 高優先級修復項目" >> "$VALIDATION_REPORT"
        echo "請優先解決上述標記為 ❌ 的問題，這些是系統正常運行的關鍵要求。" >> "$VALIDATION_REPORT"
        echo "" >> "$VALIDATION_REPORT"
    fi
    
    if [[ $WARNINGS -gt 0 ]]; then
        echo "### ⚠️ 建議改善項目" >> "$VALIDATION_REPORT"
        echo "標記為 ⚠️ 的項目建議在時間允許時進行改善，以提升系統完整性。" >> "$VALIDATION_REPORT"
        echo "" >> "$VALIDATION_REPORT"
    fi
    
    if [[ $ERRORS -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
        echo "### 🎉 系統狀態良好" >> "$VALIDATION_REPORT"
        echo "所有檢查項目均通過，系統配置完整且正確。" >> "$VALIDATION_REPORT"
        echo "" >> "$VALIDATION_REPORT"
    fi
    
    cat >> "$VALIDATION_REPORT" << EOF
## 📝 下一步

1. 解決所有 ❌ 標記的關鍵問題
2. 改善 ⚠️ 標記的建議項目
3. 執行完整測試: \`make test\`
4. 部署到測試環境: \`make deploy-staging\`
5. 重新執行驗證: \`./scripts/system-validation.sh\`

---
*報告生成時間: $(date)*
*執行者: $(whoami)*
*系統: $(uname -s) $(uname -r)*
EOF
}

# 顯示最終結果
show_final_results() {
    echo ""
    echo "======================================"
    log_result "系統驗證完成！"
    echo "======================================"
    echo ""
    
    echo "📊 統計摘要:"
    echo "  總檢查項目: $TOTAL_CHECKS"
    echo "  通過項目: $((TOTAL_CHECKS - ERRORS - WARNINGS))"
    echo "  警告項目: $WARNINGS"
    echo "  失敗項目: $ERRORS"
    echo ""
    
    if [[ $ERRORS -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
        log_success "🎉 所有檢查通過！系統狀態良好。"
    elif [[ $ERRORS -eq 0 ]]; then
        log_warning "⚠️ 存在 $WARNINGS 個警告項目，建議改善。"
    else
        log_error "❌ 存在 $ERRORS 個嚴重問題需要修復。"
    fi
    
    echo ""
    log_info "📄 詳細報告已生成: $VALIDATION_REPORT"
    echo ""
    
    # 根據結果設置退出碼
    if [[ $ERRORS -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# 主函數
main() {
    echo "🔍 Auto Video 系統驗證腳本"
    echo "=================================="
    echo "開始時間: $(date)"
    echo ""
    
    # 初始化報告
    init_report
    
    # 執行所有檢查
    check_development_tools
    check_project_structure
    check_frontend_configuration
    check_backend_services
    check_kubernetes_configuration
    check_environment_configuration
    check_docker_configuration
    check_monitoring_configuration
    check_security_configuration
    check_testing_configuration
    check_api_documentation
    check_script_permissions
    
    # 生成報告
    generate_report_summary
    
    # 顯示結果
    show_final_results
}

# 執行主函數
main "$@"