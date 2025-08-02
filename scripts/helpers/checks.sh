#!/bin/bash

# 檢查腳本

source "$(dirname "$0")/utils.sh"

# 檢查系統要求
check_system_requirements() {
    log_info "Checking system requirements..."
    
    # 檢查 Python 版本
    if ! check_command python3; then
        return 1
    fi
    
    # 檢查 pip
    if ! check_command pip; then
        return 1
    fi
    
    # 檢查 Docker (可選)
    if command -v docker &> /dev/null; then
        log_info "Docker is available"
    else
        log_warn "Docker is not installed (optional)"
    fi
    
    log_info "System requirements check completed"
    return 0
}

# 檢查依賴
check_dependencies() {
    log_info "Checking Python dependencies..."
    
    if [ ! -f "backend/requirements.txt" ]; then
        log_error "requirements.txt not found"
        return 1
    fi
    
    # 檢查是否安裝了必要的包
    python3 -c "import fastapi, uvicorn, sqlalchemy" 2>/dev/null || {
        log_warn "Some dependencies are missing. Run: pip install -r backend/requirements.txt"
        return 1
    }
    
    log_info "Dependencies check completed"
    return 0
}

# 檢查配置文件
check_config_files() {
    log_info "Checking configuration files..."
    
    config_files=("env.development" "env.production" "env.test")
    
    for file in "${config_files[@]}"; do
        if [ -f "$file" ]; then
            log_info "✅ $file exists"
        else
            log_warn "⚠️  $file not found"
        fi
    done
    
    log_info "Configuration check completed"
}

# 主檢查函數
main() {
    log_info "Starting system checks..."
    
    check_system_requirements || exit 1
    check_dependencies || exit 1
    check_config_files
    
    log_info "All checks completed!"
}

main "$@" 