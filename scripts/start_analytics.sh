#!/bin/bash

# 分析和報告服務啟動腳本

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# 配置變數
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
COMMAND="${1:-dashboard}"
PORT="${2:-8050}"

# 檢查 Python 環境
check_python_env() {
    log_info "檢查 Python 環境..."
    
    if [[ -f "$PROJECT_ROOT/venv/bin/activate" ]]; then
        source "$PROJECT_ROOT/venv/bin/activate"
        log_success "Python 虛擬環境已啟用"
    else
        log_warning "未找到 Python 虛擬環境"
    fi
}

# 安裝報告依賴
install_reporting_deps() {
    log_info "安裝報告依賴..."
    
    if [[ -f "$PROJECT_ROOT/requirements-reporting.txt" ]]; then
        pip install -r "$PROJECT_ROOT/requirements-reporting.txt"
        log_success "報告依賴安裝完成"
    else
        log_warning "未找到報告依賴文件，嘗試安裝基本依賴..."
        pip install matplotlib pandas plotly dash jinja2 seaborn
    fi
}

# 啟動分析儀表板
start_dashboard() {
    log_info "啟動分析儀表板..."
    
    cd "$PROJECT_ROOT"
    
    # 檢查端口是否被占用
    if command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":$PORT "; then
            log_error "端口 $PORT 已被占用"
            exit 1
        fi
    fi
    
    log_success "分析儀表板將在 http://localhost:$PORT 啟動"
    python monitoring/analytics_dashboard.py
}

# 生成報告
generate_report() {
    local report_type="${2:-daily}"
    
    log_info "生成 $report_type 報告..."
    
    cd "$PROJECT_ROOT"
    
    case "$report_type" in
        "daily")
            python -c "
import asyncio
from monitoring.report_generator import ReportGenerator

async def main():
    generator = ReportGenerator()
    report_path = await generator.generate_daily_report()
    print(f'每日報告已生成: {report_path}')

asyncio.run(main())
"
            ;;
        "weekly")
            python -c "
import asyncio
from monitoring.report_generator import ReportGenerator

async def main():
    generator = ReportGenerator()
    report_path = await generator.generate_weekly_report()
    print(f'週報告已生成: {report_path}')

asyncio.run(main())
"
            ;;
        "monthly")
            python -c "
import asyncio
from monitoring.report_generator import ReportGenerator

async def main():
    generator = ReportGenerator()
    report_path = await generator.generate_monthly_report()
    print(f'月報告已生成: {report_path}')

asyncio.run(main())
"
            ;;
        *)
            log_error "不支援的報告類型: $report_type"
            exit 1
            ;;
    esac
}

# 啟動報告服務器
start_report_server() {
    log_info "啟動報告服務器..."
    
    cd "$PROJECT_ROOT"
    
    # 創建簡單的報告服務器
    python -c "
import http.server
import socketserver
import os
from pathlib import Path

PORT = $PORT
REPORTS_DIR = Path('reports')

class ReportHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPORTS_DIR), **kwargs)

if not REPORTS_DIR.exists():
    REPORTS_DIR.mkdir()
    print('報告目錄已創建')

with socketserver.TCPServer(('', PORT), ReportHandler) as httpd:
    print(f'報告服務器已啟動: http://localhost:{PORT}')
    print('按 Ctrl+C 停止服務器')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\\n服務器已停止')
"
}

# 顯示使用說明
show_usage() {
    echo ""
    echo "分析和報告服務管理工具"
    echo "========================"
    echo ""
    echo "使用方法: $0 <command> [options]"
    echo ""
    echo "命令:"
    echo "  dashboard              啟動分析儀表板"
    echo "  report <type>          生成報告 (daily/weekly/monthly)"
    echo "  server                 啟動報告文件服務器"
    echo "  install-deps           安裝報告依賴"
    echo "  help                   顯示此說明"
    echo ""
    echo "選項:"
    echo "  --port <port>          指定端口 (預設: 8050)"
    echo ""
    echo "範例:"
    echo "  $0 dashboard           # 啟動儀表板"
    echo "  $0 report daily        # 生成每日報告"
    echo "  $0 server --port 8080  # 在端口 8080 啟動報告服務器"
    echo ""
}

# 主函數
main() {
    check_python_env
    
    case "$COMMAND" in
        "dashboard")
            install_reporting_deps
            start_dashboard
            ;;
        "report")
            install_reporting_deps
            generate_report "$@"
            ;;
        "server")
            start_report_server
            ;;
        "install-deps")
            install_reporting_deps
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