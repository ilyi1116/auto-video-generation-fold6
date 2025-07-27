#!/bin/bash

# 模式切換腳本 - 支援創業模式與企業模式快速切換
# 讓使用者可以隨時在個人創業和企業級配置間無縫切換

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
CONFIG_DIR="$PROJECT_ROOT/config"
STARTUP_CONFIG="$CONFIG_DIR/startup-config.json"
ENTERPRISE_CONFIG="$CONFIG_DIR/enterprise-config.json"
CURRENT_CONFIG="$CONFIG_DIR/current-config.json"
AUTO_TRENDS_CONFIG="$CONFIG_DIR/auto_trends_config.json"

# 檢查配置檔案是否存在
check_config_files() {
    if [ ! -f "$STARTUP_CONFIG" ]; then
        log_error "創業模式配置檔案不存在: $STARTUP_CONFIG"
        exit 1
    fi
    
    if [ ! -f "$ENTERPRISE_CONFIG" ]; then
        log_error "企業模式配置檔案不存在: $ENTERPRISE_CONFIG"
        exit 1
    fi
}

# 獲取當前模式
get_current_mode() {
    if [ -L "$CURRENT_CONFIG" ]; then
        local target=$(readlink "$CURRENT_CONFIG")
        if [[ "$target" == *"startup"* ]]; then
            echo "startup"
        elif [[ "$target" == *"enterprise"* ]]; then
            echo "enterprise"
        else
            echo "unknown"
        fi
    elif [ -f "$CURRENT_CONFIG" ]; then
        # 檢查檔案內容
        if grep -q '"mode": "startup"' "$CURRENT_CONFIG" 2>/dev/null; then
            echo "startup"
        elif grep -q '"mode": "enterprise"' "$CURRENT_CONFIG" 2>/dev/null; then
            echo "enterprise"
        else
            echo "unknown"
        fi
    else
        echo "none"
    fi
}

# 切換到創業模式
switch_to_startup_mode() {
    log_step "切換到創業模式..."
    
    # 停止當前服務
    log_info "停止當前服務..."
    if [ -f "$PROJECT_ROOT/scripts/start_auto_trends.sh" ]; then
        "$PROJECT_ROOT/scripts/start_auto_trends.sh" stop || true
    fi
    
    # 使用統一配置管理器
    cd "$PROJECT_ROOT"
    if [ -f "config/config_manager.py" ]; then
        python3 -c "
from config.config_manager import config_manager
config_manager.set_mode('startup')
config_manager.save_current_config('current-config.json')
print('已切換到創業模式並更新配置')
"
    else
        # 回退到舊方式
        rm -f "$CURRENT_CONFIG"
        ln -sf "$STARTUP_CONFIG" "$CURRENT_CONFIG"
    fi
    
    # 更新 auto_trends_config.json
    if [ -f "$AUTO_TRENDS_CONFIG" ]; then
        # 備份原始配置
        cp "$AUTO_TRENDS_CONFIG" "$AUTO_TRENDS_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
        
        # 使用 jq 或直接替換關鍵配置 (簡化版)
        cat > "$AUTO_TRENDS_CONFIG" << 'EOF'
{
  "generation": {
    "daily_video_limit": 5,
    "batch_size": 1,
    "max_concurrent_jobs": 2,
    "quality_preset": "medium",
    "platforms": ["tiktok", "instagram_reels"]
  },
  "cost_control": {
    "daily_budget_usd": 10,
    "stop_on_budget_exceeded": true
  },
  "resources": {
    "max_memory_usage": "8GB",
    "max_cpu_cores": 4
  },
  "scheduling": {
    "work_hours_only": true,
    "start_time": "18:00",
    "end_time": "22:00"
  }
}
EOF
    fi
    
    # 設置環境變數
    export AUTO_VIDEO_MODE=startup
    export DAILY_VIDEO_LIMIT=5
    export MAX_CONCURRENT_JOBS=2
    
    log_success "已切換到創業模式"
    log_info "配置特性:"
    log_info "  • 每日限制: 3-5 則影片"
    log_info "  • 併發處理: 2 個任務"
    log_info "  • 成本預算: $10/日"
    log_info "  • 工作時間: 18:00-22:00"
    log_info "  • 目標平台: TikTok, Instagram Reels"
}

# 切換到企業模式
switch_to_enterprise_mode() {
    log_step "切換到企業模式..."
    
    # 停止當前服務
    log_info "停止當前服務..."
    if [ -f "$PROJECT_ROOT/scripts/start_auto_trends.sh" ]; then
        "$PROJECT_ROOT/scripts/start_auto_trends.sh" stop || true
    fi
    
    # 使用統一配置管理器
    cd "$PROJECT_ROOT"
    if [ -f "config/config_manager.py" ]; then
        python3 -c "
from config.config_manager import config_manager
config_manager.set_mode('enterprise')
config_manager.save_current_config('current-config.json')
print('已切換到企業模式並更新配置')
"
    else
        # 回退到舊方式
        rm -f "$CURRENT_CONFIG"
        ln -sf "$ENTERPRISE_CONFIG" "$CURRENT_CONFIG"
    fi
    
    # 更新 auto_trends_config.json
    if [ -f "$AUTO_TRENDS_CONFIG" ]; then
        # 備份原始配置
        cp "$AUTO_TRENDS_CONFIG" "$AUTO_TRENDS_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
        
        # 使用企業級配置
        cat > "$AUTO_TRENDS_CONFIG" << 'EOF'
{
  "generation": {
    "daily_video_limit": 50,
    "batch_size": 5,
    "max_concurrent_jobs": 8,
    "quality_preset": "high",
    "platforms": ["tiktok", "instagram_reels", "youtube_shorts", "facebook_reels"]
  },
  "cost_control": {
    "daily_budget_usd": 200,
    "stop_on_budget_exceeded": false
  },
  "resources": {
    "max_memory_usage": "32GB",
    "max_cpu_cores": 16
  },
  "scheduling": {
    "work_hours_only": false,
    "continuous_operation": true
  },
  "monitoring": {
    "prometheus_enabled": true,
    "grafana_enabled": true,
    "detailed_analytics": true
  }
}
EOF
    fi
    
    # 設置環境變數
    export AUTO_VIDEO_MODE=enterprise
    export DAILY_VIDEO_LIMIT=50
    export MAX_CONCURRENT_JOBS=8
    
    log_success "已切換到企業模式"
    log_info "配置特性:"
    log_info "  • 每日限制: 20-50 則影片"
    log_info "  • 併發處理: 8 個任務"
    log_info "  • 成本預算: $200/日"
    log_info "  • 24/7 連續運行"
    log_info "  • 全平台支援"
    log_info "  • 完整監控與分析"
}

# 顯示當前狀態
show_status() {
    local current_mode=$(get_current_mode)
    
    echo ""
    echo "=== 系統模式狀態 ==="
    echo ""
    
    case "$current_mode" in
        "startup")
            log_success "當前模式: 創業模式 (Startup Mode)"
            echo "  💡 輕量化配置，適合個人創業測試"
            echo "  📊 每日 3-5 則影片，成本可控"
            echo "  ⏰ 工作時間限制: 18:00-22:00"
            ;;
        "enterprise")
            log_success "當前模式: 企業模式 (Enterprise Mode)"
            echo "  🚀 高產量配置，適合商業運營"
            echo "  📈 每日 20-50 則影片，全平台支援"
            echo "  🔄 24/7 連續運行"
            ;;
        "none")
            log_warning "尚未設置模式"
            echo "  請使用 'switch_mode.sh startup' 或 'switch_mode.sh enterprise' 初始化"
            ;;
        *)
            log_error "模式配置異常: $current_mode"
            ;;
    esac
    
    echo ""
    echo "=== 配置檔案狀態 ==="
    if [ -L "$CURRENT_CONFIG" ]; then
        echo "  當前配置: $(readlink "$CURRENT_CONFIG")"
    elif [ -f "$CURRENT_CONFIG" ]; then
        echo "  當前配置: $CURRENT_CONFIG (檔案)"
    else
        echo "  當前配置: 未設置"
    fi
    
    echo ""
    echo "=== 服務狀態 ==="
    if command -v docker &> /dev/null && [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        cd "$PROJECT_ROOT"
        docker-compose ps 2>/dev/null || echo "  Docker 服務未運行"
    else
        echo "  本地模式 (檢查 logs/ 目錄中的 PID 檔案)"
    fi
}

# 快速啟動當前模式
quick_start() {
    local current_mode=$(get_current_mode)
    
    if [ "$current_mode" = "none" ] || [ "$current_mode" = "unknown" ]; then
        log_error "請先設置模式: startup 或 enterprise"
        exit 1
    fi
    
    log_info "使用 $current_mode 模式快速啟動..."
    
    if [ -f "$PROJECT_ROOT/scripts/start_auto_trends.sh" ]; then
        "$PROJECT_ROOT/scripts/start_auto_trends.sh" start once
    else
        log_error "啟動腳本不存在: $PROJECT_ROOT/scripts/start_auto_trends.sh"
        exit 1
    fi
}

# 顯示使用方法
show_usage() {
    echo ""
    echo "模式切換工具 - 創業模式 ⇄ 企業模式"
    echo "======================================="
    echo ""
    echo "使用方法:"
    echo "  $0 <command>"
    echo ""
    echo "可用命令:"
    echo "  startup      切換到創業模式 (個人創業，3-5影片/日)"
    echo "  enterprise   切換到企業模式 (商業運營，20-50影片/日)"
    echo "  status       顯示當前模式狀態"
    echo "  start        快速啟動當前模式"
    echo "  compare      比較兩種模式差異"
    echo "  help         顯示此幫助"
    echo ""
    echo "範例:"
    echo "  $0 startup          # 切換到創業模式"
    echo "  $0 enterprise       # 切換到企業模式"
    echo "  $0 status           # 檢查當前狀態"
    echo "  $0 start            # 啟動當前模式"
    echo ""
}

# 比較模式差異
show_comparison() {
    echo ""
    echo "=== 模式比較 ==="
    echo ""
    printf "%-20s %-20s %-20s\n" "功能項目" "創業模式" "企業模式"
    echo "────────────────────────────────────────────────────────────"
    printf "%-20s %-20s %-20s\n" "日產影片數量" "3-5 則" "20-50 則"
    printf "%-20s %-20s %-20s\n" "併發處理數" "2 個" "8 個"
    printf "%-20s %-20s %-20s\n" "影片品質" "Medium" "High"
    printf "%-20s %-20s %-20s\n" "日預算" "\$10" "\$200"
    printf "%-20s %-20s %-20s\n" "記憶體使用" "8GB" "32GB"
    printf "%-20s %-20s %-20s\n" "支援平台" "2 個" "4 個"
    printf "%-20s %-20s %-20s\n" "運行時間" "18:00-22:00" "24/7"
    printf "%-20s %-20s %-20s\n" "監控功能" "基礎" "完整"
    printf "%-20s %-20s %-20s\n" "適用場景" "個人測試" "商業運營"
    echo ""
}

# 主函數
main() {
    command="${1:-help}"
    
    # 檢查配置檔案
    check_config_files
    
    case "$command" in
        "startup")
            switch_to_startup_mode
            ;;
        "enterprise")
            switch_to_enterprise_mode
            ;;
        "status")
            show_status
            ;;
        "start")
            quick_start
            ;;
        "compare")
            show_comparison
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

# 執行主函數
main "$@"