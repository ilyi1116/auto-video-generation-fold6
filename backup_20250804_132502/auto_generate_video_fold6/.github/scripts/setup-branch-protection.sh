#!/bin/bash

# 主分支保護設定腳本
# 使用 GitHub CLI 自動設定分支保護規則

set -e  # 錯誤時退出

# 顏色定義
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

# 檢查必要工具
check_requirements() {
    log_info "檢查系統需求..."
    
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) 未安裝，請先安裝："
        echo "  # macOS"
        echo "  brew install gh"
        echo ""
        echo "  # Ubuntu/Debian"
        echo "  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg"
        echo "  echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null"
        echo "  sudo apt update && sudo apt install gh"
        exit 1
    fi
    
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI 未登入，請先登入："
        echo "  gh auth login"
        exit 1
    fi
    
    log_success "系統需求檢查通過"
}

# 獲取倉庫資訊
get_repo_info() {
    log_info "獲取倉庫資訊..."
    
    if ! git rev-parse --is-inside-work-tree &> /dev/null; then
        log_error "當前目錄不是 Git 倉庫"
        exit 1
    fi
    
    REPO_URL=$(git config --get remote.origin.url)
    if [[ $REPO_URL == https://github.com/* ]]; then
        REPO_PATH=${REPO_URL#https://github.com/}
        REPO_PATH=${REPO_PATH%.git}
    elif [[ $REPO_URL == git@github.com:* ]]; then
        REPO_PATH=${REPO_URL#git@github.com:}
        REPO_PATH=${REPO_PATH%.git}
    else
        log_error "無法識別的 GitHub 倉庫 URL: $REPO_URL"
        exit 1
    fi
    
    OWNER=$(echo $REPO_PATH | cut -d'/' -f1)
    REPO=$(echo $REPO_PATH | cut -d'/' -f2)
    
    log_info "倉庫: $OWNER/$REPO"
}

# 檢查分支是否存在
check_branch_exists() {
    local branch=$1
    log_info "檢查分支 '$branch' 是否存在..."
    
    if gh api repos/$OWNER/$REPO/branches/$branch &> /dev/null; then
        log_success "分支 '$branch' 存在"
        return 0
    else
        log_warning "分支 '$branch' 不存在"
        return 1
    fi
}

# 設定基本分支保護
setup_basic_protection() {
    local branch=$1
    log_info "設定 '$branch' 分支基本保護規則..."
    
    local protection_config='{
        "required_status_checks": {
            "strict": true,
            "contexts": [
                "CI / test",
                "CI / lint", 
                "CI / build",
                "CI / typecheck"
            ]
        },
        "enforce_admins": true,
        "required_pull_request_reviews": {
            "required_approving_review_count": 1,
            "dismiss_stale_reviews": true,
            "require_code_owner_reviews": false,
            "require_last_push_approval": false
        },
        "restrictions": null,
        "allow_force_pushes": false,
        "allow_deletions": false,
        "block_creations": false,
        "required_linear_history": false,
        "required_conversation_resolution": true
    }'
    
    if gh api -X PUT repos/$OWNER/$REPO/branches/$branch/protection \
        --input - <<< "$protection_config" &> /dev/null; then
        log_success "基本保護規則設定完成"
    else
        log_error "基本保護規則設定失敗"
        return 1
    fi
}

# 設定嚴格分支保護
setup_strict_protection() {
    local branch=$1
    log_info "設定 '$branch' 分支嚴格保護規則..."
    
    local protection_config='{
        "required_status_checks": {
            "strict": true,
            "contexts": [
                "CI / test",
                "CI / lint",
                "CI / build", 
                "CI / typecheck",
                "CI / security",
                "security / dependency-scan",
                "security / code-scan"
            ]
        },
        "enforce_admins": true,
        "required_pull_request_reviews": {
            "required_approving_review_count": 2,
            "dismiss_stale_reviews": true,
            "require_code_owner_reviews": true,
            "require_last_push_approval": true
        },
        "restrictions": null,
        "allow_force_pushes": false,
        "allow_deletions": false,
        "block_creations": false,
        "required_linear_history": true,
        "required_conversation_resolution": true
    }'
    
    if gh api -X PUT repos/$OWNER/$REPO/branches/$branch/protection \
        --input - <<< "$protection_config" &> /dev/null; then
        log_success "嚴格保護規則設定完成"
    else
        log_error "嚴格保護規則設定失敗"
        return 1
    fi
}

# 設定企業級分支保護
setup_enterprise_protection() {
    local branch=$1
    log_info "設定 '$branch' 分支企業級保護規則..."
    
    # 先設定基本保護規則
    local protection_config='{
        "required_status_checks": {
            "strict": true,
            "contexts": [
                "CI / test",
                "CI / lint",
                "CI / build",
                "CI / typecheck", 
                "CI / security",
                "CI / performance",
                "CI / accessibility",
                "security / dependency-scan",
                "security / code-scan",
                "security / secrets-scan"
            ]
        },
        "enforce_admins": true,
        "required_pull_request_reviews": {
            "required_approving_review_count": 2,
            "dismiss_stale_reviews": true,
            "require_code_owner_reviews": true,
            "require_last_push_approval": true
        },
        "restrictions": null,
        "allow_force_pushes": false,
        "allow_deletions": false,
        "block_creations": false,
        "required_linear_history": true,
        "required_conversation_resolution": true
    }'
    
    if gh api -X PUT repos/$OWNER/$REPO/branches/$branch/protection \
        --input - <<< "$protection_config" &> /dev/null; then
        log_success "企業級保護規則設定完成"
    else
        log_error "企業級保護規則設定失敗"
        return 1
    fi
    
    # 設定簽名提交要求（如果支援的話）
    log_info "嘗試啟用簽名提交要求..."
    if gh api -X PATCH repos/$OWNER/$REPO \
        --field required_signatures=true &> /dev/null; then
        log_success "簽名提交要求已啟用"
    else
        log_warning "無法啟用簽名提交要求（可能需要企業帳戶）"
    fi
}

# 驗證保護規則
verify_protection() {
    local branch=$1
    log_info "驗證 '$branch' 分支保護規則..."
    
    local protection_info
    if protection_info=$(gh api repos/$OWNER/$REPO/branches/$branch/protection 2>/dev/null); then
        echo "$protection_info" | jq -r '
            "保護規則配置:",
            "- 需要 PR: \(.required_pull_request_reviews != null)",
            "- 需要審查數量: \(.required_pull_request_reviews.required_approving_review_count // "N/A")",
            "- 需要狀態檢查: \(.required_status_checks != null)",
            "- 狀態檢查項目: \(.required_status_checks.contexts // [] | join(", "))",
            "- 管理員受限: \(.enforce_admins)",
            "- 禁止強制推送: \(.allow_force_pushes | not)",
            "- 禁止刪除: \(.allow_deletions | not)",
            "- 需要線性歷史: \(.required_linear_history)",
            "- 需要解決對話: \(.required_conversation_resolution)"
        '
        log_success "分支保護規則驗證完成"
    else
        log_error "無法獲取保護規則資訊"
        return 1
    fi
}

# 創建 CODEOWNERS 檔案
create_codeowners() {
    log_info "創建 CODEOWNERS 檔案..."
    
    local codeowners_file=".github/CODEOWNERS"
    
    if [[ ! -f "$codeowners_file" ]]; then
        cat > "$codeowners_file" << 'EOF'
# 全域代碼擁有者
* @ilyi1116

# 前端相關
/frontend/ @ilyi1116
*.svelte @ilyi1116
*.ts @ilyi1116
*.js @ilyi1116

# 後端相關  
/services/ @ilyi1116
*.py @ilyi1116

# 基礎設施
/docker-compose*.yml @ilyi1116
/nginx/ @ilyi1116
/.github/ @ilyi1116

# 文檔
*.md @ilyi1116
/docs/ @ilyi1116

# 配置檔案
*.json @ilyi1116
*.yaml @ilyi1116
*.yml @ilyi1116
EOF
        log_success "CODEOWNERS 檔案已創建"
    else
        log_info "CODEOWNERS 檔案已存在"
    fi
}

# 主函數
main() {
    echo "🛡️  GitHub 分支保護設定工具"
    echo "=================================="
    echo ""
    
    # 檢查參數
    PROTECTION_LEVEL=${1:-"basic"}
    BRANCH=${2:-"main"}
    
    case $PROTECTION_LEVEL in
        basic|strict|enterprise)
            ;;
        *)
            log_error "無效的保護級別: $PROTECTION_LEVEL"
            echo "使用方式: $0 [basic|strict|enterprise] [branch_name]"
            echo ""
            echo "保護級別:"
            echo "  basic      - 基本保護 (1人審查, 基本CI檢查)"
            echo "  strict     - 嚴格保護 (2人審查, 代碼擁有者審查, 完整CI檢查)"
            echo "  enterprise - 企業級保護 (嚴格保護 + 簽名提交 + 線性歷史)"
            echo ""
            echo "範例:"
            echo "  $0 basic main"
            echo "  $0 strict main" 
            echo "  $0 enterprise main"
            exit 1
            ;;
    esac
    
    log_info "保護級別: $PROTECTION_LEVEL"
    log_info "目標分支: $BRANCH"
    echo ""
    
    # 執行設定流程
    check_requirements
    get_repo_info
    
    if ! check_branch_exists "$BRANCH"; then
        log_error "分支 '$BRANCH' 不存在，請確保分支已推送到遠端倉庫"
        exit 1
    fi
    
    create_codeowners
    
    case $PROTECTION_LEVEL in
        basic)
            setup_basic_protection "$BRANCH" 
            ;;
        strict)
            setup_strict_protection "$BRANCH"
            ;;
        enterprise)
            setup_enterprise_protection "$BRANCH"
            ;;
    esac
    
    verify_protection "$BRANCH"
    
    echo ""
    log_success "🎉 分支保護設定完成！"
    echo ""
    echo "接下來的步驟:"
    echo "1. 檢查 GitHub 倉庫的 Settings → Branches 確認設定"
    echo "2. 測試創建 Pull Request 驗證保護規則"
    echo "3. 確保 CI/CD 工作流程正常運作"
    echo "4. 通知團隊成員新的工作流程"
}

# 執行主函數
main "$@"