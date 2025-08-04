#!/bin/bash

# migrate-structure.sh - 專案結構重組自動化腳本
# 用途：將 auto_generate_video_fold6 提升為主專案結構

set -e  # 遇到錯誤時停止執行

# 顏色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 檢查是否在正確的目錄
check_project_root() {
    if [ ! -f "pyproject.toml" ] || [ ! -d "auto_generate_video_fold6" ]; then
        log_error "請在專案根目錄執行此腳本"
        exit 1
    fi
}

# 建立備份
create_backup() {
    local backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
    log_info "建立備份到 $backup_dir..."
    
    mkdir -p "$backup_dir"
    
    # 備份重要目錄和檔案
    [ -d "backend" ] && cp -r "backend" "$backup_dir/"
    [ -d "services" ] && cp -r "services" "$backup_dir/"
    [ -d "auto_generate_video_fold6" ] && cp -r "auto_generate_video_fold6" "$backup_dir/"
    
    # 備份配置檔案
    cp *.env* "$backup_dir/" 2>/dev/null || true
    cp pyproject.toml "$backup_dir/"
    cp docker-compose*.yml "$backup_dir/" 2>/dev/null || true
    
    log_success "備份完成：$backup_dir"
    echo "$backup_dir" > .backup_path
}

# 建立新的目錄結構
create_new_structure() {
    log_info "建立新的目錄結構..."
    
    # 建立主要目錄
    mkdir -p src/{services,frontend,shared,config}
    mkdir -p infra/{docker,k8s,monitoring,security}
    mkdir -p legacy/{backend,services}
    mkdir -p config/environments
    
    log_success "新目錄結構建立完成"
}

# 移動 auto_generate_video_fold6 內容
migrate_main_content() {
    log_info "遷移主要應用程式碼..."
    
    # 移動服務
    if [ -d "auto_generate_video_fold6/services" ]; then
        log_info "移動微服務..."
        cp -r auto_generate_video_fold6/services/* src/services/ 2>/dev/null || true
    fi
    
    # 移動前端
    if [ -d "auto_generate_video_fold6/frontend" ]; then
        log_info "移動前端應用..."
        cp -r auto_generate_video_fold6/frontend/* src/frontend/ 2>/dev/null || true
    fi
    
    # 移動共享組件
    if [ -d "auto_generate_video_fold6/shared" ]; then
        log_info "移動共享組件..."
        cp -r auto_generate_video_fold6/shared/* src/shared/ 2>/dev/null || true
    fi
    
    # 移動配置
    if [ -d "auto_generate_video_fold6/config" ]; then
        log_info "移動配置檔案..."
        cp -r auto_generate_video_fold6/config/* src/config/ 2>/dev/null || true
    fi
    
    log_success "主要應用程式碼遷移完成"
}

# 移動基礎設施代碼
migrate_infrastructure() {
    log_info "遷移基礎設施代碼..."
    
    # 移動 Docker 配置
    if [ -d "auto_generate_video_fold6/docker" ]; then
        log_info "移動 Docker 配置..."
        cp -r auto_generate_video_fold6/docker/* infra/docker/ 2>/dev/null || true
    fi
    
    # 移動 Kubernetes 配置
    if [ -d "auto_generate_video_fold6/k8s" ]; then
        log_info "移動 Kubernetes 配置..."
        cp -r auto_generate_video_fold6/k8s/* infra/k8s/ 2>/dev/null || true
    fi
    
    # 移動監控配置
    if [ -d "auto_generate_video_fold6/monitoring" ]; then
        log_info "移動監控系統..."
        cp -r auto_generate_video_fold6/monitoring/* infra/monitoring/ 2>/dev/null || true
    fi
    
    # 移動安全配置
    if [ -d "auto_generate_video_fold6/security" ]; then
        log_info "移動安全配置..."
        cp -r auto_generate_video_fold6/security/* infra/security/ 2>/dev/null || true
    fi
    
    log_success "基礎設施代碼遷移完成"
}

# 移動腳本和工具
migrate_scripts() {
    log_info "遷移腳本和工具..."
    
    if [ -d "auto_generate_video_fold6/scripts" ]; then
        # 合併腳本目錄
        cp -r auto_generate_video_fold6/scripts/* scripts/ 2>/dev/null || true
    fi
    
    log_success "腳本遷移完成"
}

# 保留舊版本代碼
preserve_legacy() {
    log_info "保留舊版本代碼到 legacy/..."
    
    # 移動原始 backend
    if [ -d "backend" ]; then
        log_info "保留原始 backend..."
        cp -r backend/* legacy/backend/ 2>/dev/null || true
    fi
    
    # 移動原始 services  
    if [ -d "services" ] && [ "$(ls -A services)" ]; then
        log_info "保留原始 services..."
        cp -r services/* legacy/services/ 2>/dev/null || true
    fi
    
    log_success "舊版本代碼保留完成"
}

# 處理配置檔案
migrate_configs() {
    log_info "遷移和統一配置檔案..."
    
    # 建立統一的環境配置
    if [ -f "auto_generate_video_fold6/.env.development" ]; then
        cp "auto_generate_video_fold6/.env.development" "config/environments/development.env"
        log_info "已建立 development.env"
    fi
    
    if [ -f "auto_generate_video_fold6/.env.production" ]; then
        cp "auto_generate_video_fold6/.env.production" "config/environments/production.env"
        log_info "已建立 production.env"
    fi
    
    if [ -f "auto_generate_video_fold6/.env.testing" ]; then
        cp "auto_generate_video_fold6/.env.testing" "config/environments/testing.env"
        log_info "已建立 testing.env"
    fi
    
    # 保留統一的 .env.example
    if [ -f "auto_generate_video_fold6/.env.example" ]; then
        cp "auto_generate_video_fold6/.env.example" ".env.example.new"
        log_info "已更新 .env.example"
    fi
    
    log_success "配置檔案遷移完成"
}

# 更新主要配置檔案
update_main_configs() {
    log_info "更新主要配置檔案..."
    
    # 更新 docker-compose.yml
    if [ -f "auto_generate_video_fold6/docker-compose.yml" ]; then
        cp "auto_generate_video_fold6/docker-compose.yml" "docker-compose.yml.new"
        log_info "已更新 docker-compose.yml"
    fi
    
    # 更新 alembic.ini
    if [ -f "auto_generate_video_fold6/alembic.ini" ]; then
        cp "auto_generate_video_fold6/alembic.ini" "alembic.ini"
        log_info "已更新 alembic.ini"
    fi
    
    log_success "主要配置檔案更新完成"
}

# 移動文檔
migrate_docs() {
    log_info "整合文檔..."
    
    if [ -d "auto_generate_video_fold6/docs" ]; then
        # 合併文檔，保留兩邊的內容
        cp -r auto_generate_video_fold6/docs/* docs/ 2>/dev/null || true
        log_info "文檔整合完成"
    fi
    
    log_success "文檔遷移完成"
}

# 清理和重命名
cleanup_and_rename() {
    log_info "清理和重命名舊目錄..."
    
    # 重命名 auto_generate_video_fold6 為 auto_generate_video_fold6.old
    if [ -d "auto_generate_video_fold6" ]; then
        mv "auto_generate_video_fold6" "auto_generate_video_fold6.old"
        log_info "已重命名 auto_generate_video_fold6 為 auto_generate_video_fold6.old"
    fi
    
    # 清理空的舊目錄
    [ -d "backend" ] && [ ! "$(ls -A backend)" ] && rmdir backend 2>/dev/null || true
    [ -d "services" ] && [ ! "$(ls -A services)" ] && rmdir services 2>/dev/null || true
    
    log_success "清理完成"
}

# 驗證新結構
validate_structure() {
    log_info "驗證新結構..."
    
    local errors=0
    
    # 檢查必要目錄
    for dir in "src/services" "src/frontend" "infra/docker" "config/environments"; do
        if [ ! -d "$dir" ]; then
            log_error "缺少目錄: $dir"
            ((errors++))
        fi
    done
    
    # 檢查重要檔案
    if [ ! -f "pyproject.toml" ]; then
        log_error "缺少 pyproject.toml"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        log_success "結構驗證通過"
        return 0
    else
        log_error "發現 $errors 個錯誤"
        return 1
    fi
}

# 生成遷移報告
generate_report() {
    local report_file="migration_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# 專案結構遷移報告

## 遷移時間
$(date)

## 遷移摘要
- 來源：auto_generate_video_fold6/
- 目標：新的 src/ 結構
- 備份位置：$(cat .backup_path)

## 新目錄結構
\`\`\`
src/
├── services/     # 微服務
├── frontend/     # 前端應用
├── shared/       # 共享組件
└── config/       # 配置管理

infra/
├── docker/       # Docker 配置
├── k8s/         # Kubernetes 配置
├── monitoring/   # 監控系統
└── security/     # 安全配置

legacy/
├── backend/      # 原始後端代碼
└── services/     # 原始服務代碼

config/
└── environments/ # 環境特定配置
\`\`\`

## 重要檔案更新
- docker-compose.yml -> docker-compose.yml.new
- .env.example -> .env.example.new
- 環境配置 -> config/environments/*.env

## 下一步行動
1. 檢查新結構的功能完整性
2. 更新路徑引用
3. 測試 Docker 構建
4. 更新 CI/CD 配置
5. 更新文檔中的路徑引用

## 回滾指令
如需回滾，執行：
\`\`\`bash
./scripts/rollback-migration.sh $(cat .backup_path)
\`\`\`
EOF

    log_success "遷移報告已生成：$report_file"
}

# 主函數
main() {
    log_info "開始專案結構重組..."
    log_info "這個過程將會："
    log_info "1. 建立完整備份"
    log_info "2. 建立新的目錄結構"
    log_info "3. 遷移 auto_generate_video_fold6 的內容"
    log_info "4. 保留舊版本代碼到 legacy/"
    log_info "5. 統一配置管理"
    
    echo
    read -p "是否繼續？(y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "遷移已取消"
        exit 0
    fi
    
    # 執行遷移步驟
    check_project_root
    create_backup
    create_new_structure
    migrate_main_content
    migrate_infrastructure
    migrate_scripts
    preserve_legacy
    migrate_configs
    update_main_configs
    migrate_docs
    cleanup_and_rename
    
    if validate_structure; then
        generate_report
        log_success "專案結構重組完成！"
        log_info "請查看遷移報告了解詳細資訊"
        log_warning "重要：請測試新結構的功能並更新相關配置"
    else
        log_error "結構驗證失敗，請檢查錯誤並手動修復"
        exit 1
    fi
}

# 執行主函數
main "$@"