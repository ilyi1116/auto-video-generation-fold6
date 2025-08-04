#!/bin/bash

# 系統啟動器 - 整合服務管理和健康監控的統一啟動解決方案

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
COMMAND="${1:-start}"
SERVICE_NAME="${2:-}"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$LOG_DIR/pids"

# 創建必要目錄
mkdir -p "$LOG_DIR" "$PID_DIR"

# 檢查 Python 環境
check_python_env() {
    log_step "檢查 Python 環境..."
    
    if [[ -f "$PROJECT_ROOT/venv/bin/activate" ]]; then
        source "$PROJECT_ROOT/venv/bin/activate"
        log_success "Python 虛擬環境已啟用"
    else
        log_warning "未找到 Python 虛擬環境，使用系統 Python"
    fi
    
    # 檢查必要的 Python 套件
    if ! python -c "import asyncio, aiohttp, psutil" 2>/dev/null; then
        log_error "缺少必要的 Python 套件，請執行: pip install aiohttp psutil"
        exit 1
    fi
}

# 檢查系統需求
check_system_requirements() {
    log_step "檢查系統需求..."
    
    # 檢查端口占用
    check_port() {
        local port=$1
        local service=$2
        
        if command -v netstat &> /dev/null; then
            if netstat -tuln | grep -q ":$port "; then
                log_warning "端口 $port ($service) 已被占用"
                return 1
            fi
        elif command -v ss &> /dev/null; then
            if ss -tuln | grep -q ":$port "; then
                log_warning "端口 $port ($service) 已被占用"
                return 1
            fi
        fi
        return 0
    }
    
    # 檢查主要端口
    check_port 3000 "前端" || true
    check_port 8000 "後端" || true
    check_port 6379 "Redis" || true
    
    # 檢查磁盤空間
    AVAILABLE_SPACE=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    if [[ $AVAILABLE_SPACE -lt 1048576 ]]; then  # 1GB in KB
        log_warning "可用磁盤空間不足 1GB"
    fi
    
    log_success "系統需求檢查完成"
}

# 啟動服務管理器
start_service_manager() {
    log_step "啟動服務管理器..."
    
    cd "$PROJECT_ROOT"
    
    if [[ -n "$SERVICE_NAME" ]]; then
        log_info "啟動單個服務: $SERVICE_NAME"
        python scripts/service_manager.py start "$SERVICE_NAME"
    else
        log_info "啟動所有服務..."
        python scripts/service_manager.py start
    fi
}

# 停止服務管理器
stop_service_manager() {
    log_step "停止服務管理器..."
    
    cd "$PROJECT_ROOT"
    
    if [[ -n "$SERVICE_NAME" ]]; then
        log_info "停止單個服務: $SERVICE_NAME"
        python scripts/service_manager.py stop "$SERVICE_NAME"
    else
        log_info "停止所有服務..."
        python scripts/service_manager.py stop
    fi
}

# 重啟服務管理器
restart_service_manager() {
    log_step "重啟服務管理器..."
    
    cd "$PROJECT_ROOT"
    
    if [[ -n "$SERVICE_NAME" ]]; then
        log_info "重啟單個服務: $SERVICE_NAME"
        python scripts/service_manager.py restart "$SERVICE_NAME"
    else
        log_info "重啟所有服務..."
        python scripts/service_manager.py restart
    fi
}

# 啟動健康監控
start_health_monitor() {
    log_step "啟動健康監控..."
    
    cd "$PROJECT_ROOT"
    
    # 檢查健康監控是否已在運行
    if [[ -f "$PID_DIR/health_monitor.pid" ]]; then
        HEALTH_PID=$(cat "$PID_DIR/health_monitor.pid")
        if kill -0 "$HEALTH_PID" 2>/dev/null; then
            log_info "健康監控已在運行 (PID: $HEALTH_PID)"
            return 0
        fi
    fi
    
    # 啟動健康監控
    python monitoring/health_monitor.py > "$LOG_DIR/health_monitor.log" 2>&1 &
    HEALTH_PID=$!
    echo $HEALTH_PID > "$PID_DIR/health_monitor.pid"
    
    log_success "健康監控已啟動 (PID: $HEALTH_PID)"
}

# 停止健康監控
stop_health_monitor() {
    log_step "停止健康監控..."
    
    if [[ -f "$PID_DIR/health_monitor.pid" ]]; then
        HEALTH_PID=$(cat "$PID_DIR/health_monitor.pid")
        if kill -0 "$HEALTH_PID" 2>/dev/null; then
            kill "$HEALTH_PID"
            rm "$PID_DIR/health_monitor.pid"
            log_success "健康監控已停止"
        else
            log_warning "健康監控進程不存在"
            rm "$PID_DIR/health_monitor.pid"
        fi
    else
        log_info "健康監控未運行"
    fi
}

# 顯示系統狀態
show_status() {
    log_step "檢查系統狀態..."
    
    cd "$PROJECT_ROOT"
    
    echo ""
    echo "=== 服務狀態 ==="
    python scripts/service_manager.py status
    
    echo ""
    echo "=== 健康檢查 ==="
    if command -v python &> /dev/null; then
        python monitoring/health_monitor.py once 2>/dev/null || log_warning "健康檢查執行失敗"
    fi
    
    echo ""
    echo "=== 系統資源 ==="
    if command -v python &> /dev/null; then
        python -c "
import psutil
import json

cpu_percent = psutil.cpu_percent(interval=1)
memory = psutil.virtual_memory()
disk = psutil.disk_usage('/')

status = {
    'cpu_usage': f'{cpu_percent:.1f}%',
    'memory_usage': f'{memory.percent:.1f}%',
    'disk_usage': f'{(disk.used/disk.total)*100:.1f}%',
    'load_average': list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else 'N/A'
}

print(json.dumps(status, indent=2))
"
    fi
    
    echo ""
    echo "=== 網路連接 ==="
    if command -v netstat &> /dev/null; then
        echo "活動端口:"
        netstat -tuln | grep -E ":(3000|8000|8001|8002|6379|8080)" | head -10
    elif command -v ss &> /dev/null; then
        echo "活動端口:"
        ss -tuln | grep -E ":(3000|8000|8001|8002|6379|8080)" | head -10
    fi
}

# 監控模式
monitor_mode() {
    log_step "進入監控模式..."
    
    cd "$PROJECT_ROOT"
    
    # 啟動服務監控
    python scripts/service_manager.py monitor &
    SERVICE_MONITOR_PID=$!
    
    # 啟動健康監控 (如果未運行)
    start_health_monitor
    
    log_success "監控模式已啟動"
    log_info "按 Ctrl+C 退出監控模式"
    
    # 監控迴圈
    trap 'kill $SERVICE_MONITOR_PID 2>/dev/null; stop_health_monitor; exit 0' SIGINT SIGTERM
    
    while true; do
        sleep 30
        
        # 每30秒顯示狀態摘要
        echo ""
        echo "=== $(date) ==="
        python scripts/service_manager.py status | grep -E "(running|failed|stopped)" | head -5
        echo ""
        
        # 檢查系統資源
        python -c "
import psutil
cpu = psutil.cpu_percent(interval=1)
mem = psutil.virtual_memory()
print(f'CPU: {cpu:.1f}% | Memory: {mem.percent:.1f}% | Load: {psutil.getloadavg()[0]:.2f}' if hasattr(psutil, 'getloadavg') else f'CPU: {cpu:.1f}% | Memory: {mem.percent:.1f}%')
"
    done
}

# 日誌查看
show_logs() {
    local service="${SERVICE_NAME:-all}"
    
    log_step "顯示日誌: $service"
    
    if [[ "$service" == "all" ]]; then
        echo "=== 最近的系統日誌 ==="
        find "$LOG_DIR" -name "*.log" -type f -exec tail -n 5 {} + 2>/dev/null || log_warning "無日誌文件"
    else
        log_file="$LOG_DIR/${service}.log"
        if [[ -f "$log_file" ]]; then
            tail -f "$log_file"
        else
            log_error "日誌文件不存在: $log_file"
        fi
    fi
}

# 清理功能
cleanup() {
    log_step "執行清理..."
    
    # 清理舊的日誌文件 (保留最近7天)
    find "$LOG_DIR" -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true
    
    # 清理無效的 PID 文件
    for pid_file in "$PID_DIR"/*.pid; do
        if [[ -f "$pid_file" ]]; then
            pid=$(cat "$pid_file" 2>/dev/null || echo "")
            if [[ -n "$pid" ]] && ! kill -0 "$pid" 2>/dev/null; then
                rm "$pid_file"
                log_info "清理無效 PID 文件: $(basename "$pid_file")"
            fi
        fi
    done
    
    # 清理臨時文件
    find "$PROJECT_ROOT/data/temp" -type f -mtime +1 -delete 2>/dev/null || true
    
    log_success "清理完成"
}

# 顯示使用說明
show_usage() {
    echo ""
    echo "系統啟動器 - Auto Video Generation"
    echo "===================================="
    echo ""
    echo "使用方法: $0 <command> [service_name]"
    echo ""
    echo "命令:"
    echo "  start       啟動服務 (預設)"
    echo "  stop        停止服務"
    echo "  restart     重啟服務"
    echo "  status      顯示狀態"
    echo "  monitor     監控模式"
    echo "  logs        查看日誌"
    echo "  cleanup     清理舊文件"
    echo "  health      執行健康檢查"
    echo "  help        顯示此說明"
    echo ""
    echo "服務名稱 (可選):"
    echo "  frontend    前端服務"
    echo "  backend     後端服務"
    echo "  ai-service  AI 服務"
    echo "  video-service 影片處理服務"
    echo "  redis       Redis 快取"
    echo "  scheduler   排程器服務"
    echo ""
    echo "範例:"
    echo "  $0 start              # 啟動所有服務"
    echo "  $0 start frontend     # 只啟動前端服務"
    echo "  $0 stop               # 停止所有服務"
    echo "  $0 status             # 查看系統狀態"
    echo "  $0 monitor            # 進入監控模式"
    echo "  $0 logs backend       # 查看後端日誌"
    echo ""
}

# 主函數
main() {
    case "$COMMAND" in
        "start")
            check_python_env
            check_system_requirements
            start_service_manager
            start_health_monitor
            log_success "系統啟動完成"
            ;;
        "stop")
            check_python_env
            stop_health_monitor
            stop_service_manager
            log_success "系統停止完成"
            ;;
        "restart")
            check_python_env
            stop_health_monitor
            restart_service_manager
            start_health_monitor
            log_success "系統重啟完成"
            ;;
        "status")
            check_python_env
            show_status
            ;;
        "monitor")
            check_python_env
            monitor_mode
            ;;
        "logs")
            show_logs
            ;;
        "cleanup")
            cleanup
            ;;
        "health")
            check_python_env
            cd "$PROJECT_ROOT"
            python monitoring/health_monitor.py once
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        *)
            log_error "未知命令: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
}

# 執行主函數
main "$@"