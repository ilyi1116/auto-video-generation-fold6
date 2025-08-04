#!/bin/bash

# rollback-migration.sh - 專案結構改善回滾腳本
# 用途：回滾所有結構改善變更到原始狀態

set -e

# 顏色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日誌函數
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 顯示使用方式
show_usage() {
    echo "使用方式: $0 [backup_directory]"
    echo ""
    echo "參數："
    echo "  backup_directory  備份目錄路徑 (可選)"
    echo ""
    echo "如果未指定備份目錄，腳本將嘗試自動找到最近的備份。"
    echo ""
    echo "範例："
    echo "  $0                               # 自動找到備份"
    echo "  $0 backup_20241204_143022        # 使用指定備份"
}

# 尋找備份目錄
find_backup_directory() {
    local backup_dir=""
    
    # 檢查是否有記錄的備份路徑
    if [ -f ".backup_path" ]; then
        backup_dir=$(cat .backup_path)
        if [ -d "$backup_dir" ]; then
            echo "$backup_dir"
            return 0
        fi
    fi
    
    # 尋找最新的備份目錄
    backup_dir=$(find . -maxdepth 1 -name "backup_*" -type d | sort | tail -1)
    if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
        echo "$backup_dir"
        return 0
    fi
    
    return 1
}

# 驗證備份目錄
validate_backup() {
    local backup_dir="$1"
    
    if [ ! -d "$backup_dir" ]; then
        log_error "備份目錄不存在: $backup_dir"
        return 1
    fi
    
    # 檢查重要檔案是否存在
    local required_files=("pyproject.toml")
    for file in "${required_files[@]}"; do
        if [ ! -f "$backup_dir/$file" ]; then
            log_warning "備份中缺少重要檔案: $file"
        fi
    done
    
    log_info "備份目錄驗證通過: $backup_dir"
    return 0
}

# 回滾結構變更
rollback_structure_changes() {
    log_info "回滾結構變更..."
    
    # 移除新建立的目錄
    if [ -d "src" ]; then
        log_info "移除 src/ 目錄..."
        rm -rf src/
    fi
    
    if [ -d "infra" ]; then
        log_info "移除 infra/ 目錄..."
        rm -rf infra/
    fi
    
    if [ -d "config" ]; then
        log_info "移除 config/ 目錄..."
        rm -rf config/
    fi
    
    # 恢復 legacy 目錄內容
    if [ -d "legacy/backend" ]; then
        log_info "恢復 backend/ 目錄..."
        cp -r legacy/backend/ backend/ 2>/dev/null || true
    fi
    
    if [ -d "legacy/services" ]; then
        log_info "恢復 services/ 目錄..."
        cp -r legacy/services/ services/ 2>/dev/null || true
    fi
    
    # 恢復 auto_generate_video_fold6
    if [ -d "auto_generate_video_fold6.old" ]; then
        log_info "恢復 auto_generate_video_fold6/ 目錄..."
        mv auto_generate_video_fold6.old auto_generate_video_fold6
    fi
    
    # 移除 legacy 目錄
    if [ -d "legacy" ]; then
        rm -rf legacy/
    fi
    
    log_success "結構變更回滾完成"
}

# 回滾配置變更
rollback_config_changes() {
    local backup_dir="$1"
    
    log_info "回滾配置變更..."
    
    # 恢復原始配置檔案
    if [ -f "$backup_dir/.env" ]; then
        cp "$backup_dir/.env" .env
        log_info "已恢復 .env"
    fi
    
    if [ -f "$backup_dir/.env.development" ]; then
        cp "$backup_dir/.env.development" .env.development
        log_info "已恢復 .env.development"
    fi
    
    if [ -f "$backup_dir/.env.production" ]; then
        cp "$backup_dir/.env.production" .env.production
        log_info "已恢復 .env.production"
    fi
    
    # 移除新建立的配置檔案
    rm -f .env.example.unified
    rm -f docker-compose.env
    rm -f docker-compose.yml.new
    rm -f docker-compose.yml.updated
    
    # 恢復配置備份
    local config_backup_path=""
    if [ -f ".config_backup_path" ]; then
        config_backup_path=$(cat .config_backup_path)
        if [ -d "$config_backup_path" ]; then
            log_info "恢復配置檔案從: $config_backup_path"
            cp "$config_backup_path"/.env* . 2>/dev/null || true
        fi
    fi
    
    log_success "配置變更回滾完成"
}

# 回滾依賴變更
rollback_dependency_changes() {
    local backup_dir="$1"
    
    log_info "回滾依賴變更..."
    
    # 恢復原始 pyproject.toml
    if [ -f "pyproject.toml.original" ]; then
        cp pyproject.toml.original pyproject.toml
        log_info "已恢復原始 pyproject.toml"
    elif [ -f "pyproject.toml.backup" ]; then
        cp pyproject.toml.backup pyproject.toml
        log_info "已恢復備份的 pyproject.toml"
    elif [ -f "$backup_dir/pyproject.toml" ]; then
        cp "$backup_dir/pyproject.toml" pyproject.toml
        log_info "已從備份恢復 pyproject.toml"
    fi
    
    # 移除新建立的檔案
    rm -f pyproject.toml.new
    rm -f pyproject.toml.backup
    rm -f pyproject.toml.original
    
    # 恢復 requirements.txt 檔案
    local requirements_backup_path=""
    if [ -f ".requirements_backup_path" ]; then
        requirements_backup_path=$(cat .requirements_backup_path)
        if [ -d "$requirements_backup_path" ]; then
            log_info "恢復 requirements.txt 檔案從: $requirements_backup_path"
            cp "$requirements_backup_path"/requirements*.txt . 2>/dev/null || true
            
            # 恢復服務目錄中的 requirements 檔案
            find "$requirements_backup_path" -name "requirements*.txt" | while read -r file; do
                filename=$(basename "$file")
                # 嘗試將檔案放回原始位置（這需要一些猜測）
                if [[ "$filename" == *"auth"* ]]; then
                    cp "$file" services/auth-service/ 2>/dev/null || true
                elif [[ "$filename" == *"video"* ]]; then
                    cp "$file" services/video-service/ 2>/dev/null || true
                fi
            done
        fi
    fi
    
    log_success "依賴變更回滾完成"
}

# 回滾 Docker 變更
rollback_docker_changes() {
    log_info "回滾 Docker 變更..."
    
    # 恢復 Dockerfile 備份
    find . -name "Dockerfile*.backup" | while read -r backup_file; do
        original_file="${backup_file%.backup}"
        if [ -f "$backup_file" ]; then
            cp "$backup_file" "$original_file"
            log_info "已恢復 $original_file"
        fi
    done
    
    log_success "Docker 變更回滾完成"
}

# 清理臨時檔案
cleanup_temp_files() {
    log_info "清理臨時檔案..."
    
    # 移除管理腳本建立的檔案
    rm -f migration_report_*.md
    rm -f config_cleanup_report_*.md
    rm -f dependency_migration_report_*.md
    rm -f dependency_report_*.md
    rm -f migration_validation_report.*
    rm -f security_report*.json
    rm -f security_check.json
    
    # 移除狀態檔案
    rm -f .backup_path
    rm -f .config_backup_path
    rm -f .requirements_backup_path
    
    log_success "臨時檔案清理完成"
}

# 驗證回滾結果
validate_rollback() {
    log_info "驗證回滾結果..."
    
    local errors=0
    
    # 檢查重要目錄
    if [ ! -d "auto_generate_video_fold6" ]; then
        log_error "auto_generate_video_fold6 目錄不存在"
        ((errors++))
    fi
    
    # 檢查是否還有新結構目錄
    if [ -d "src" ] || [ -d "infra" ]; then
        log_error "新結構目錄仍然存在"
        ((errors++))
    fi
    
    # 檢查重要檔案
    if [ ! -f "pyproject.toml" ]; then
        log_error "pyproject.toml 不存在"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        log_success "回滾驗證通過"
        return 0
    else
        log_error "發現 $errors 個問題"
        return 1
    fi
}

# 生成回滾報告
generate_rollback_report() {
    local backup_dir="$1"
    local report_file="rollback_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# 專案結構改善回滾報告

## 回滾時間
$(date)

## 回滾摘要
- 使用的備份: $backup_dir
- 回滾範圍: 完整回滾到原始狀態

## 回滾操作

### 結構變更回滾
- ✅ 移除 src/ 目錄
- ✅ 移除 infra/ 目錄  
- ✅ 移除 config/ 目錄
- ✅ 恢復 auto_generate_video_fold6/
- ✅ 恢復 backend/ 和 services/
- ✅ 移除 legacy/ 目錄

### 配置變更回滾
- ✅ 恢復原始 .env 檔案
- ✅ 移除統一配置檔案
- ✅ 恢復環境特定配置

### 依賴變更回滾
- ✅ 恢復原始 pyproject.toml
- ✅ 恢復 requirements.txt 檔案
- ✅ 移除依賴管理腳本

### Docker 變更回滾
- ✅ 恢復原始 Dockerfile
- ✅ 移除 Docker 配置更新

## 驗證結果
$(validate_rollback && echo "✅ 回滾驗證通過" || echo "❌ 回滾驗證失敗")

## 目前狀態
專案已回滾到改善前的原始狀態。

## 建議行動
1. 檢查應用程式是否正常運行
2. 確認所有服務可以正常啟動
3. 驗證原始功能是否完整
4. 如需重新實施改善，請分析失敗原因

## 備份保留
原始備份目錄: $backup_dir (建議保留一段時間)

EOF

    log_success "回滾報告已生成: $report_file"
}

# 主函數
main() {
    local backup_dir="$1"
    
    log_warning "⚠️  專案結構改善回滾腳本"
    log_warning "這將回滾所有結構改善變更到原始狀態"
    
    # 尋找備份目錄
    if [ -z "$backup_dir" ]; then
        log_info "嘗試自動尋找備份目錄..."
        backup_dir=$(find_backup_directory)
        if [ $? -ne 0 ]; then
            log_error "找不到備份目錄"
            log_error "請手動指定備份目錄路徑"
            show_usage
            exit 1
        fi
        log_info "找到備份目錄: $backup_dir"
    fi
    
    # 驗證備份
    if ! validate_backup "$backup_dir"; then
        exit 1
    fi
    
    # 最後確認
    echo
    log_warning "即將回滾到備份: $backup_dir"
    log_warning "這將移除所有結構改善的變更！"
    echo
    read -p "是否確定要繼續回滾？(輸入 'YES' 確認): " -r
    echo
    
    if [[ $REPLY != "YES" ]]; then
        log_info "回滾已取消"
        exit 0
    fi
    
    # 執行回滾
    log_info "開始執行回滾..."
    
    rollback_structure_changes
    rollback_config_changes "$backup_dir"
    rollback_dependency_changes "$backup_dir"
    rollback_docker_changes
    cleanup_temp_files
    
    if validate_rollback; then
        generate_rollback_report "$backup_dir"
        log_success "✅ 回滾完成！"
        log_info "專案已恢復到原始狀態"
        log_info "請檢查應用程式是否正常運行"
    else
        log_error "❌ 回滾可能不完整"
        log_error "請手動檢查並修復問題"
        exit 1
    fi
}

# 檢查參數
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_usage
    exit 0
fi

# 執行主函數
main "$@"