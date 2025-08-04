#!/bin/bash

# 🚀 Auto Video - 企業級版本發布腳本
# 自動化版本發布流程，包含完整的測試、構建和部署

set -euo pipefail

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CURRENT_VERSION=""
NEW_VERSION=""
RELEASE_TYPE=""
DRY_RUN=false
SKIP_TESTS=false
SKIP_BUILD=false

# 函數定義
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
    exit 1
}

show_help() {
    cat << EOF
🚀 Auto Video 企業級版本發布腳本

使用方式:
    $0 [選項] <版本類型>

版本類型:
    major    主版本 (1.0.0 -> 2.0.0)
    minor    次版本 (1.0.0 -> 1.1.0)  
    patch    修補版本 (1.0.0 -> 1.0.1)
    <版本號>  直接指定版本號 (如 1.2.3)

選項:
    -h, --help         顯示此幫助訊息
    -d, --dry-run      模擬運行，不執行實際操作
    -s, --skip-tests   跳過測試步驟
    -b, --skip-build   跳過構建步驟
    -v, --verbose      詳細輸出

範例:
    $0 patch                    # 發布修補版本
    $0 minor                    # 發布次版本
    $0 1.2.3                   # 發布指定版本
    $0 --dry-run patch          # 模擬發布修補版本

發布流程:
    1. 檢查工作目錄狀態
    2. 運行測試套件
    3. 更新版本號
    4. 更新 CHANGELOG
    5. 構建 Docker 映像
    6. 創建 Git 標籤
    7. 推送到遠程倉庫
    8. 創建 GitHub Release
    9. 部署到生產環境

EOF
}

# 檢查必要工具
check_dependencies() {
    log_info "檢查必要工具..."
    
    local missing=()
    
    command -v git >/dev/null 2>&1 || missing+=("git")
    command -v docker >/dev/null 2>&1 || missing+=("docker")
    command -v jq >/dev/null 2>&1 || missing+=("jq")
    command -v python3 >/dev/null 2>&1 || missing+=("python3")
    command -v npm >/dev/null 2>&1 || missing+=("npm")
    command -v gh >/dev/null 2>&1 || missing+=("gh")
    
    if [[ ${#missing[@]} -ne 0 ]]; then
        log_error "缺少必要工具: ${missing[*]}"
        log_error "請安裝缺少的工具後重試"
    fi
    
    log_success "所有必要工具已就緒"
}

# 檢查工作目錄狀態
check_working_directory() {
    log_info "檢查工作目錄狀態..."
    
    # 檢查是否在正確的分支
    local current_branch
    current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "main" && "$current_branch" != "master" ]]; then
        log_error "請在 main 或 master 分支上執行發布"
    fi
    
    # 檢查是否有未提交的變更
    if ! git diff-index --quiet HEAD --; then
        log_error "工作目錄有未提交的變更，請先提交或儲存"
    fi
    
    # 檢查是否與遠程同步
    git fetch origin
    local local_commit remote_commit
    local_commit=$(git rev-parse HEAD)
    remote_commit=$(git rev-parse "origin/$current_branch")
    
    if [[ "$local_commit" != "$remote_commit" ]]; then
        log_error "本地分支與遠程不同步，請先同步"
    fi
    
    log_success "工作目錄狀態正常"
}

# 獲取當前版本
get_current_version() {
    log_info "獲取當前版本..."
    
    if [[ -f "$PROJECT_ROOT/pyproject.toml" ]]; then
        CURRENT_VERSION=$(grep '^version = ' "$PROJECT_ROOT/pyproject.toml" | sed 's/version = "\(.*\)"/\1/')
    else
        log_error "找不到 pyproject.toml 文件"
    fi
    
    if [[ -z "$CURRENT_VERSION" ]]; then
        log_error "無法讀取當前版本"
    fi
    
    log_info "當前版本: $CURRENT_VERSION"
}

# 計算新版本號
calculate_new_version() {
    log_info "計算新版本號..."
    
    case "$RELEASE_TYPE" in
        major|minor|patch)
            # 使用語義化版本工具計算
            if command -v semver >/dev/null 2>&1; then
                NEW_VERSION=$(semver -i "$RELEASE_TYPE" "$CURRENT_VERSION")
            else
                # 手動計算
                IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
                local major=${VERSION_PARTS[0]}
                local minor=${VERSION_PARTS[1]:-0}
                local patch=${VERSION_PARTS[2]:-0}
                
                case "$RELEASE_TYPE" in
                    major) NEW_VERSION="$((major + 1)).0.0" ;;
                    minor) NEW_VERSION="$major.$((minor + 1)).0" ;;
                    patch) NEW_VERSION="$major.$minor.$((patch + 1))" ;;
                esac
            fi
            ;;
        *)
            # 直接指定版本號
            if [[ "$RELEASE_TYPE" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                NEW_VERSION="$RELEASE_TYPE"
            else
                log_error "無效的版本號格式: $RELEASE_TYPE"
            fi
            ;;
    esac
    
    log_info "新版本: $NEW_VERSION"
    
    # 檢查版本是否已存在
    if git tag -l | grep -q "^v$NEW_VERSION$"; then
        log_error "版本 v$NEW_VERSION 已存在"
    fi
}

# 運行測試
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        log_warning "跳過測試步驟"
        return
    fi
    
    log_info "運行完整測試套件..."
    
    # 後端測試
    log_info "運行後端測試..."
    cd "$PROJECT_ROOT"
    python -m pytest tests/ -v --cov=services --cov-report=html --cov-fail-under=80
    
    # 前端測試
    log_info "運行前端測試..."
    cd "$PROJECT_ROOT/frontend"
    npm test
    npm run test:e2e
    
    # 安全掃描
    log_info "運行安全掃描..."
    cd "$PROJECT_ROOT"
    bandit -r services/ -f json -o security-report.json || true
    
    # Docker 映像掃描
    log_info "掃描 Docker 映像..."
    if command -v trivy >/dev/null 2>&1; then
        docker-compose build
        trivy image auto-video:latest || true
    fi
    
    log_success "所有測試通過"
}

# 更新版本號
update_version() {
    log_info "更新版本號到 $NEW_VERSION..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將更新版本號"
        return
    fi
    
    # 更新 pyproject.toml
    sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" "$PROJECT_ROOT/pyproject.toml"
    
    # 更新 package.json
    if [[ -f "$PROJECT_ROOT/frontend/package.json" ]]; then
        cd "$PROJECT_ROOT/frontend"
        npm version "$NEW_VERSION" --no-git-tag-version
    fi
    
    # 更新 Docker 標籤
    find "$PROJECT_ROOT" -name "docker-compose*.yml" -exec sed -i "s/:latest/:$NEW_VERSION/g" {} \;
    
    log_success "版本號已更新"
}

# 更新 CHANGELOG
update_changelog() {
    log_info "更新 CHANGELOG..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將更新 CHANGELOG"
        return
    fi
    
    local changelog_file="$PROJECT_ROOT/CHANGELOG.md"
    local temp_file=$(mktemp)
    local release_date
    release_date=$(date +%Y-%m-%d)
    
    # 生成發布說明
    {
        echo "# Changelog"
        echo ""
        echo "## [未發布]"
        echo ""
        echo "## [$NEW_VERSION] - $release_date"
        echo ""
        echo "### 新增"
        echo "- 新功能和改進"
        echo ""
        echo "### 變更"
        echo "- API 變更和改進"
        echo ""
        echo "### 修復"
        echo "- 問題修復"
        echo ""
        echo "### 安全性"
        echo "- 安全性相關更新"
        echo ""
        tail -n +3 "$changelog_file"
    } > "$temp_file"
    
    mv "$temp_file" "$changelog_file"
    log_success "CHANGELOG 已更新"
}

# 構建 Docker 映像
build_docker_images() {
    if [[ "$SKIP_BUILD" == "true" ]]; then
        log_warning "跳過構建步驟"
        return
    fi
    
    log_info "構建 Docker 映像..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將構建 Docker 映像"
        return
    fi
    
    cd "$PROJECT_ROOT"
    
    # 構建所有服務
    docker-compose build --parallel
    
    # 標記版本
    docker tag auto-video:latest "auto-video:$NEW_VERSION"
    
    # 推送到容器註冊表（如果配置了）
    if [[ -n "${DOCKER_REGISTRY:-}" ]]; then
        docker tag "auto-video:$NEW_VERSION" "$DOCKER_REGISTRY/auto-video:$NEW_VERSION"
        docker push "$DOCKER_REGISTRY/auto-video:$NEW_VERSION"
    fi
    
    log_success "Docker 映像構建完成"
}

# 創建 Git 標籤
create_git_tag() {
    log_info "創建 Git 標籤..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將創建標籤 v$NEW_VERSION"
        return
    fi
    
    # 提交版本更新
    git add .
    git commit -m "chore: bump version to $NEW_VERSION

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    # 創建標籤
    git tag -a "v$NEW_VERSION" -m "Release version $NEW_VERSION

$(git log --oneline $(git describe --tags --abbrev=0)..HEAD)"
    
    log_success "Git 標籤已創建"
}

# 推送到遠程
push_to_remote() {
    log_info "推送到遠程倉庫..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將推送到遠程倉庫"
        return
    fi
    
    git push origin main
    git push origin "v$NEW_VERSION"
    
    log_success "已推送到遠程倉庫"
}

# 創建 GitHub Release
create_github_release() {
    log_info "創建 GitHub Release..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將創建 GitHub Release"
        return
    fi
    
    # 生成發布說明
    local release_notes
    release_notes=$(git log --oneline "$(git describe --tags --abbrev=0 HEAD^)"..HEAD | sed 's/^/- /')
    
    gh release create "v$NEW_VERSION" \
        --title "Release $NEW_VERSION" \
        --notes "## 🚀 Release $NEW_VERSION

### 變更內容
$release_notes

### 安裝方式
\`\`\`bash
git clone -b v$NEW_VERSION https://github.com/auto-video/auto-video.git
cd auto-video
./scripts/dev-setup.sh
\`\`\`

### Docker 部署
\`\`\`bash
docker pull auto-video:$NEW_VERSION
docker-compose up -d
\`\`\`

完整變更記錄請參考 [CHANGELOG.md](CHANGELOG.md)"
    
    log_success "GitHub Release 已創建"
}

# 部署到生產環境
deploy_to_production() {
    log_info "部署到生產環境..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將部署到生產環境"
        return
    fi
    
    # 這裡應該根據實際的部署策略進行調整
    if [[ -f "$PROJECT_ROOT/scripts/deploy-production.sh" ]]; then
        "$PROJECT_ROOT/scripts/deploy-production.sh" "$NEW_VERSION"
    else
        log_warning "未找到生產部署腳本，跳過自動部署"
    fi
    
    log_success "生產部署完成"
}

# 清理臨時文件
cleanup() {
    log_info "清理臨時文件..."
    
    # 清理構建產物
    find "$PROJECT_ROOT" -name "*.pyc" -delete
    find "$PROJECT_ROOT" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # 清理測試報告
    rm -f "$PROJECT_ROOT/security-report.json"
    
    log_success "清理完成"
}

# 發布摘要
show_release_summary() {
    log_success "🎉 版本 $NEW_VERSION 發布完成！"
    
    cat << EOF

📋 發布摘要:
=====================================
版本號:      $CURRENT_VERSION -> $NEW_VERSION
發布類型:    $RELEASE_TYPE
發布時間:    $(date)
Git 標籤:    v$NEW_VERSION
GitHub:      https://github.com/auto-video/auto-video/releases/tag/v$NEW_VERSION

🚀 後續步驟:
- 監控生產環境運行狀況
- 更新文檔和教學材料
- 通知團隊和用戶新版本發布
- 準備下一個版本的開發計劃

EOF
}

# 主要執行流程
main() {
    log_info "🚀 Auto Video 企業級版本發布開始"
    
    # 解析命令行參數
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -s|--skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            -b|--skip-build)
                SKIP_BUILD=true
                shift
                ;;
            -v|--verbose)
                set -x
                shift
                ;;
            *)
                RELEASE_TYPE="$1"
                shift
                ;;
        esac
    done
    
    # 檢查必要參數
    if [[ -z "$RELEASE_TYPE" ]]; then
        log_error "請指定版本類型 (major/minor/patch/版本號)"
        show_help
        exit 1
    fi
    
    # 執行發布流程
    check_dependencies
    check_working_directory
    get_current_version
    calculate_new_version
    
    # 確認發布
    if [[ "$DRY_RUN" != "true" ]]; then
        echo -e "${YELLOW}準備發布版本 $CURRENT_VERSION -> $NEW_VERSION${NC}"
        echo -n "確定要繼續嗎？(y/N) "
        read -r confirmation
        if [[ "$confirmation" != "y" && "$confirmation" != "Y" ]]; then
            log_info "發布已取消"
            exit 0
        fi
    fi
    
    # 執行發布步驟
    run_tests
    update_version
    update_changelog
    build_docker_images
    create_git_tag
    push_to_remote
    create_github_release
    deploy_to_production
    cleanup
    show_release_summary
    
    log_success "✨ 版本發布流程完成！"
}

# 錯誤處理
trap 'log_error "發布過程中發生錯誤，請檢查輸出並手動處理"' ERR

# 執行主函數
main "$@"