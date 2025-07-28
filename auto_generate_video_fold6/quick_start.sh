#!/bin/bash

# Auto Video Generation - 快速啟動腳本
# 一鍵部署和啟動整個系統

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

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

# 獲取專案根目錄
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
MODE="${1:-startup}"

echo ""
echo "🎬 Auto Video Generation - 快速啟動"
echo "======================================"
echo ""

# 檢查模式參數
if [[ "$MODE" != "startup" && "$MODE" != "enterprise" && "$MODE" != "docker" ]]; then
    log_error "無效的啟動模式: $MODE"
    echo ""
    echo "可用模式:"
    echo "  startup     - 創業模式 (本地部署)"
    echo "  enterprise  - 企業模式 (本地部署)"
    echo "  docker      - Docker 容器部署"
    echo ""
    echo "使用方法: $0 [startup|enterprise|docker]"
    exit 1
fi

# Docker 模式
if [[ "$MODE" == "docker" ]]; then
    log_info "使用 Docker 模式啟動..."
    
    # 檢查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝，請先安裝 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安裝，請先安裝 Docker Compose"
        exit 1
    fi
    
    # 複製環境變數檔案
    if [[ ! -f ".env" ]]; then
        log_info "創建環境變數檔案..."
        cp .env.example .env
        log_warning "請編輯 .env 檔案並填入正確的 API 密鑰"
    fi
    
    # 啟動 Docker 服務
    log_info "啟動 Docker 服務..."
    docker-compose -f docker-compose.standalone.yml up --build -d
    
    # 等待服務啟動
    log_info "等待服務啟動..."
    sleep 10
    
    # 檢查服務狀態
    log_info "檢查服務狀態..."
    docker-compose -f docker-compose.standalone.yml ps
    
    log_success "Docker 服務已啟動！"
    echo ""
    echo "服務地址:"
    echo "  🌐 前端: http://localhost:3000"
    echo "  🔧 後端 API: http://localhost:8000"
    echo "  📊 監控面板: http://localhost:8080"
    echo "  📚 API 文檔: http://localhost:8000/docs"
    echo ""
    echo "停止服務: docker-compose -f docker-compose.standalone.yml down"
    
    exit 0
fi

# 本地模式部署
log_info "使用 $MODE 模式進行本地部署..."

# 檢查是否已經部署過
if [[ ! -f "venv/bin/activate" ]] || [[ ! -d "frontend/node_modules" ]]; then
    log_info "首次部署，執行完整安裝..."
    bash scripts/standalone_deploy.sh "$MODE" true
else
    log_info "更新現有部署..."
    bash scripts/standalone_deploy.sh "$MODE" false
fi

# 設置模式
if [[ -f "scripts/switch_mode.sh" ]]; then
    log_info "設置系統模式為: $MODE"
    bash scripts/switch_mode.sh "$MODE"
fi

# 啟動服務
log_info "啟動系統服務..."

if [[ -f "scripts/start_system.sh" ]]; then
    bash scripts/start_system.sh
else
    log_error "找不到系統啟動腳本"
    exit 1
fi

# 等待服務啟動
log_info "等待服務完全啟動..."
sleep 15

# 檢查服務狀態
check_service() {
    local url=$1
    local name=$2
    
    if curl -s --connect-timeout 5 "$url" > /dev/null 2>&1; then
        log_success "$name 服務運行正常"
        return 0
    else
        log_warning "$name 服務可能未正常啟動"
        return 1
    fi
}

log_info "檢查服務狀態..."
check_service "http://localhost:3000" "前端"
check_service "http://localhost:8000" "後端"

echo ""
log_success "🎉 系統啟動完成！"
echo ""
echo "======================================"
echo "         系統資訊"
echo "======================================"
echo "模式: $MODE"
echo "專案路徑: $PROJECT_ROOT"
echo ""
echo "🔗 服務地址:"
echo "  前端應用: http://localhost:3000"
echo "  後端 API: http://localhost:8000"
echo "  API 文檔: http://localhost:8000/docs"
echo ""
echo "📋 管理命令:"
echo "  停止系統: bash scripts/stop_system.sh"
echo "  重啟系統: bash scripts/start_system.sh"
echo "  切換模式: bash scripts/switch_mode.sh [startup|enterprise]"
echo "  系統狀態: bash scripts/system-validation.sh"
echo ""
echo "📝 日誌文件:"
echo "  前端日誌: logs/frontend.log"
echo "  後端日誌: logs/backend.log"
echo "  部署日誌: logs/deployment.log"
echo ""
echo "⚙️  下一步:"
echo "  1. 檢查並編輯 .env 檔案中的 API 密鑰"
echo "  2. 訪問前端應用開始使用系統"
echo "  3. 查看 API 文檔了解後端介面"
echo ""
echo "======================================"

# 可選：開啟瀏覽器
if command -v xdg-open &> /dev/null; then
    read -p "是否要開啟瀏覽器？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        xdg-open "http://localhost:3000" 2>/dev/null &
    fi
elif command -v open &> /dev/null; then
    read -p "是否要開啟瀏覽器？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "http://localhost:3000" 2>/dev/null &
    fi
fi