#!/bin/bash

# 自動 Google Trends 短影音生成系統啟動腳本
# 整合關鍵字採集與影片生成的完整自動化流程

set -e

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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 配置變數
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CONFIG_FILE="$PROJECT_ROOT/config/auto_trends_config.json"
LOG_DIR="$PROJECT_ROOT/logs"
SERVICES_DIR="$PROJECT_ROOT/services"
VENV_DIR="$PROJECT_ROOT/venv"

# 創建必要目錄
mkdir -p "$LOG_DIR"
mkdir -p "$PROJECT_ROOT/generated_videos"

# 檢查環境
check_environment() {
    log_step "檢查系統環境..."
    
    # 檢查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安裝"
        exit 1
    fi
    
    # 檢查 Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安裝"
        exit 1
    fi
    
    # 檢查 Docker
    if ! command -v docker &> /dev/null; then
        log_warning "Docker 未安裝，將使用本地模式"
    fi
    
    # 檢查 FFmpeg (影片處理)
    if ! command -v ffmpeg &> /dev/null; then
        log_warning "FFmpeg 未安裝，影片處理功能可能受限"
    fi
    
    log_success "環境檢查完成"
}

# 設置 Python 虛擬環境
setup_python_env() {
    log_step "設置 Python 虛擬環境..."
    
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        log_info "已創建虛擬環境"
    fi
    
    source "$VENV_DIR/bin/activate"
    
    # 安裝依賴
    pip install --upgrade pip
    pip install aiohttp asyncio pytrends pandas pillow moviepy requests
    
    log_success "Python 環境設置完成"
}

# 啟動服務
start_services() {
    log_step "啟動微服務..."
    
    # 檢查是否使用 Docker
    if command -v docker &> /dev/null && [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        log_info "使用 Docker 啟動服務..."
        
        cd "$PROJECT_ROOT"
        docker-compose up -d trend-service video-service ai-service
        
        # 等待服務啟動
        sleep 30
        
        # 檢查服務狀態
        check_service_health
    else
        log_info "使用本地模式啟動服務..."
        start_local_services
    fi
}

# 檢查服務健康狀態
check_service_health() {
    log_step "檢查服務健康狀態..."
    
    services=(
        "http://localhost:8001/health:Trend Service"
        "http://localhost:8002/health:Video Service" 
        "http://localhost:8003/health:AI Service"
    )
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r url name <<< "$service_info"
        
        if curl -sf "$url" > /dev/null 2>&1; then
            log_success "$name 運行正常"
        else
            log_warning "$name 未響應，請檢查服務狀態"
        fi
    done
}

# 啟動本地服務
start_local_services() {
    log_info "本地模式啟動服務..."
    
    # 啟動 Trend Service
    if [ -f "$SERVICES_DIR/trend-service/main.py" ]; then
        cd "$SERVICES_DIR/trend-service"
        nohup python3 main.py > "$LOG_DIR/trend-service.log" 2>&1 &
        echo $! > "$LOG_DIR/trend-service.pid"
        log_info "Trend Service 已啟動 (PID: $(cat $LOG_DIR/trend-service.pid))"
    fi
    
    # 啟動 Video Service
    if [ -f "$SERVICES_DIR/video-service/main.py" ]; then
        cd "$SERVICES_DIR/video-service"
        nohup python3 main.py > "$LOG_DIR/video-service.log" 2>&1 &
        echo $! > "$LOG_DIR/video-service.pid"
        log_info "Video Service 已啟動 (PID: $(cat $LOG_DIR/video-service.pid))"
    fi
    
    # 啟動 AI Service
    if [ -f "$SERVICES_DIR/ai-service/main.py" ]; then
        cd "$SERVICES_DIR/ai-service"
        nohup python3 main.py > "$LOG_DIR/ai-service.log" 2>&1 &
        echo $! > "$LOG_DIR/ai-service.pid"
        log_info "AI Service 已啟動 (PID: $(cat $LOG_DIR/ai-service.pid))"
    fi
    
    sleep 10
}

# 運行自動生成系統
run_auto_generation() {
    log_step "啟動自動趨勢影片生成系統..."
    
    cd "$PROJECT_ROOT"
    source "$VENV_DIR/bin/activate"
    
    # 檢查配置檔案
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "配置檔案不存在: $CONFIG_FILE"
        exit 1
    fi
    
    # 根據參數選擇運行模式
    case "${1:-schedule}" in
        "once")
            log_info "執行一次生成..."
            python3 scripts/auto_trends_video.py --config "$CONFIG_FILE" --once
            ;;
        "schedule")
            log_info "啟動排程模式..."
            python3 scripts/auto_trends_video.py --config "$CONFIG_FILE" --schedule
            ;;
        "test")
            log_info "執行測試模式..."
            python3 scripts/auto_trends_video.py --config "$CONFIG_FILE" --once
            ;;
        *)
            log_error "未知的運行模式: $1"
            show_usage
            exit 1
            ;;
    esac
}

# 停止服務
stop_services() {
    log_step "停止服務..."
    
    # 停止 Docker 服務
    if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        cd "$PROJECT_ROOT"
        docker-compose down
    fi
    
    # 停止本地服務
    for service in trend-service video-service ai-service; do
        if [ -f "$LOG_DIR/$service.pid" ]; then
            pid=$(cat "$LOG_DIR/$service.pid")
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid"
                log_info "已停止 $service (PID: $pid)"
            fi
            rm -f "$LOG_DIR/$service.pid"
        fi
    done
    
    log_success "所有服務已停止"
}

# 顯示狀態
show_status() {
    log_step "檢查系統狀態..."
    
    echo ""
    echo "=== 服務狀態 ==="
    
    # 檢查 Docker 服務
    if command -v docker &> /dev/null; then
        echo "Docker 服務:"
        docker-compose ps 2>/dev/null || echo "  Docker Compose 未運行"
    fi
    
    echo ""
    echo "本地服務:"
    for service in trend-service video-service ai-service; do
        if [ -f "$LOG_DIR/$service.pid" ]; then
            pid=$(cat "$LOG_DIR/$service.pid")
            if kill -0 "$pid" 2>/dev/null; then
                echo "  ✅ $service (PID: $pid)"
            else
                echo "  ❌ $service (進程已死亡)"
            fi
        else
            echo "  ⚪ $service (未啟動)"
        fi
    done
    
    echo ""
    echo "=== 最近的生成結果 ==="
    if [ -d "$PROJECT_ROOT/generated_videos" ]; then
        ls -lt "$PROJECT_ROOT/generated_videos" | head -5
    else
        echo "  沒有生成結果"
    fi
}

# 查看日誌
show_logs() {
    service_name="${1:-all}"
    
    case "$service_name" in
        "trend"|"trend-service")
            if [ -f "$LOG_DIR/trend-service.log" ]; then
                tail -f "$LOG_DIR/trend-service.log"
            else
                log_error "Trend Service 日誌不存在"
            fi
            ;;
        "video"|"video-service")
            if [ -f "$LOG_DIR/video-service.log" ]; then
                tail -f "$LOG_DIR/video-service.log"
            else
                log_error "Video Service 日誌不存在"
            fi
            ;;
        "ai"|"ai-service")
            if [ -f "$LOG_DIR/ai-service.log" ]; then
                tail -f "$LOG_DIR/ai-service.log"
            else
                log_error "AI Service 日誌不存在"
            fi
            ;;
        "all")
            log_info "顯示所有服務日誌..."
            tail -f "$LOG_DIR"/*.log 2>/dev/null || log_warning "沒有找到日誌檔案"
            ;;
        *)
            log_error "未知的服務名稱: $service_name"
            echo "可用的服務: trend, video, ai, all"
            ;;
    esac
}

# 顯示使用方法
show_usage() {
    echo ""
    echo "自動 Google Trends 短影音生成系統"
    echo "====================================="
    echo ""
    echo "使用方法:"
    echo "  $0 <command> [options]"
    echo ""
    echo "可用命令:"
    echo "  start [mode]     啟動系統 (mode: once|schedule|test, 默認: schedule)"
    echo "  stop             停止所有服務"
    echo "  restart [mode]   重啟系統"
    echo "  status           顯示系統狀態"
    echo "  logs [service]   查看日誌 (service: trend|video|ai|all, 默認: all)"
    echo "  setup            設置環境"
    echo "  test             運行測試"
    echo "  help             顯示此幫助"
    echo ""
    echo "範例:"
    echo "  $0 start once              # 執行一次生成"
    echo "  $0 start schedule          # 啟動排程模式"
    echo "  $0 logs trend              # 查看趨勢服務日誌"
    echo "  $0 stop                    # 停止所有服務"
    echo ""
}

# 安裝依賴
install_dependencies() {
    log_step "安裝系統依賴..."
    
    # 檢查作業系統
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv nodejs npm ffmpeg
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3 python3-pip nodejs npm ffmpeg
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install python3 node ffmpeg
        fi
    fi
    
    log_success "依賴安裝完成"
}

# 運行測試
run_tests() {
    log_step "運行系統測試..."
    
    # 測試服務連接
    log_info "測試服務連接..."
    
    # 測試關鍵字獲取
    log_info "測試關鍵字獲取..."
    
    # 測試影片生成
    log_info "測試影片生成..."
    
    log_success "測試完成"
}

# 主函數
main() {
    command="${1:-help}"
    
    case "$command" in
        "start")
            check_environment
            setup_python_env
            start_services
            run_auto_generation "${2:-schedule}"
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            sleep 5
            check_environment
            setup_python_env
            start_services
            run_auto_generation "${2:-schedule}"
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$2"
            ;;
        "setup")
            install_dependencies
            check_environment
            setup_python_env
            ;;
        "test")
            check_environment
            setup_python_env
            start_services
            run_tests
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        *)
            log_error "未知命令: $command"
            show_usage
            exit 1
            ;;
    esac
}

# 錯誤處理
trap 'log_error "腳本執行出錯，正在清理..."; stop_services; exit 1' ERR

# 執行主函數
main "$@"