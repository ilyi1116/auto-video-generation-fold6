#!/bin/bash
# 生產環境部署腳本

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

main() {
    log "🚀 生產環境部署開始"
    
    # 檢查必需命令
    for cmd in docker docker-compose; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "Required command '$cmd' is not installed"
            exit 1
        fi
    done
    
    cd "$PROJECT_ROOT"
    
    # 構建並部署
    log "構建鏡像..."
    docker-compose build
    
    log "部署服務..."
    docker-compose up -d
    
    log_success "部署完成"
}

main "$@"