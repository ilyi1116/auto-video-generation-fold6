#!/bin/bash

# 單機部署腳本 - 簡化的 Auto Video Generation 系統部署解決方案
# 適用於開發環境和小規模生產環境的快速部署

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
DEPLOY_MODE="${1:-startup}"  # startup 或 enterprise
FORCE_REINSTALL="${2:-false}"
LOG_FILE="$PROJECT_ROOT/logs/deployment.log"

# 創建日誌目錄
mkdir -p "$PROJECT_ROOT/logs"

# 檢查系統需求
check_system_requirements() {
    log_step "檢查系統需求..."
    
    # 檢查 Python 版本
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安裝，請先安裝 Python 3.8 或更高版本"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc -l) -eq 0 ]]; then
        log_error "Python 版本過低 ($PYTHON_VERSION)，需要 3.8 或更高版本"
        exit 1
    fi
    log_success "Python 版本檢查通過: $PYTHON_VERSION"
    
    # 檢查 Node.js 版本
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安裝，請先安裝 Node.js 16 或更高版本"
        exit 1
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [[ $NODE_VERSION -lt 16 ]]; then
        log_error "Node.js 版本過低 (v$NODE_VERSION)，需要 v16 或更高版本"
        exit 1
    fi
    log_success "Node.js 版本檢查通過: v$NODE_VERSION"
    
    # 檢查磁盤空間 (至少需要 5GB)
    AVAILABLE_SPACE=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    if [[ $AVAILABLE_SPACE -lt 5242880 ]]; then  # 5GB in KB
        log_warning "可用磁盤空間不足 5GB，建議清理空間"
    fi
    
    # 檢查記憶體 (至少建議 4GB)
    TOTAL_MEM=$(free -m | awk 'NR==2{print $2}')
    if [[ $TOTAL_MEM -lt 4096 ]]; then
        log_warning "系統記憶體少於 4GB ($TOTAL_MEM MB)，可能影響效能"
    fi
    
    log_success "系統需求檢查完成"
}

# 安裝 Python 依賴
install_python_dependencies() {
    log_step "安裝 Python 依賴..."
    
    cd "$PROJECT_ROOT"
    
    # 檢查是否已有虛擬環境
    if [[ ! -d "venv" ]] || [[ "$FORCE_REINSTALL" == "true" ]]; then
        log_info "創建 Python 虛擬環境..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    # 升級 pip
    python -m pip install --upgrade pip
    
    # 安裝基礎依賴
    if [[ -f "pyproject.toml" ]]; then
        log_info "從 pyproject.toml 安裝依賴..."
        pip install -e .
    elif [[ -f "requirements.txt" ]]; then
        log_info "從 requirements.txt 安裝依賴..."
        pip install -r requirements.txt
    fi
    
    # 安裝額外的運行時依賴
    pip install uvicorn gunicorn python-multipart aiofiles aiohttp
    
    log_success "Python 依賴安裝完成"
}

# 安裝 Node.js 依賴
install_nodejs_dependencies() {
    log_step "安裝 Node.js 依賴..."
    
    cd "$PROJECT_ROOT/frontend"
    
    if [[ ! -d "node_modules" ]] || [[ "$FORCE_REINSTALL" == "true" ]]; then
        log_info "安裝前端依賴..."
        npm install
    else
        log_info "更新前端依賴..."
        npm update
    fi
    
    log_success "Node.js 依賴安裝完成"
}

# 設置配置文件
setup_configuration() {
    log_step "設置配置文件..."
    
    cd "$PROJECT_ROOT"
    
    # 創建 .env 文件
    if [[ ! -f ".env" ]]; then
        log_info "創建環境配置文件..."
        cp .env.example .env
        
        # 生成隨機密鑰
        if command -v openssl &> /dev/null; then
            JWT_SECRET=$(openssl rand -hex 32)
            sed -i "s/請使用64位隨機十六進制字符串/$JWT_SECRET/g" .env
        fi
        
        log_warning "請檢查並修改 .env 文件中的配置值"
    fi
    
    # 設置模式配置
    if [[ -f "scripts/switch_mode.sh" ]]; then
        log_info "設置系統模式為: $DEPLOY_MODE"
        bash scripts/switch_mode.sh "$DEPLOY_MODE"
    fi
    
    log_success "配置文件設置完成"
}

# 初始化資料庫
initialize_database() {
    log_step "初始化資料庫..."
    
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    
    # 檢查是否需要 SQLite
    if [[ ! -f "data/app.db" ]]; then
        log_info "創建 SQLite 資料庫..."
        mkdir -p data
        
        # 如果有資料庫遷移腳本，執行它
        if [[ -f "scripts/init_db.py" ]]; then
            python scripts/init_db.py
        else
            # 創建基本的 SQLite 資料庫
            python3 -c "
import sqlite3
import os

os.makedirs('data', exist_ok=True)
conn = sqlite3.connect('data/app.db')
cursor = conn.cursor()

# 創建基本表結構
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

conn.commit()
conn.close()
print('SQLite 資料庫初始化完成')
"
        fi
    fi
    
    # 初始化成本追蹤資料庫
    if [[ -f "monitoring/cost_tracker.py" ]]; then
        log_info "初始化成本追蹤資料庫..."
        python -c "
from monitoring.cost_tracker import CostTracker
tracker = CostTracker()
print('成本追蹤資料庫初始化完成')
"
    fi
    
    log_success "資料庫初始化完成"
}

# 構建前端
build_frontend() {
    log_step "構建前端應用..."
    
    cd "$PROJECT_ROOT/frontend"
    
    log_info "執行前端構建..."
    npm run build
    
    log_success "前端構建完成"
}

# 創建服務腳本
create_service_scripts() {
    log_step "創建服務管理腳本..."
    
    # 後端服務腳本
    cat > "$PROJECT_ROOT/scripts/start_backend.sh" << 'EOF'
#!/bin/bash

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"

source venv/bin/activate

# 設置環境變數
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 啟動後端服務
log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_info "啟動後端服務..."

# 檢查是否有主要的後端入口文件
if [[ -f "main.py" ]]; then
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
elif [[ -f "app/main.py" ]]; then
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
elif [[ -f "services/api-gateway/main.py" ]]; then
    cd services/api-gateway
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "找不到後端入口文件，請檢查專案結構"
    exit 1
fi
EOF

    # 前端服務腳本
    cat > "$PROJECT_ROOT/scripts/start_frontend.sh" << 'EOF'
#!/bin/bash

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT/frontend"

log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_info "啟動前端服務..."

# 檢查是否已構建
if [[ ! -d "build" ]] && [[ ! -d ".svelte-kit" ]]; then
    log_info "未找到構建文件，執行構建..."
    npm run build
fi

# 啟動預覽服務器
npm run preview -- --host 0.0.0.0 --port 3000
EOF

    # 完整系統啟動腳本
    cat > "$PROJECT_ROOT/scripts/start_system.sh" << 'EOF'
#!/bin/bash

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# 創建 PID 文件目錄
mkdir -p "$PROJECT_ROOT/logs/pids"

# 啟動後端
log_info "啟動後端服務..."
bash "$PROJECT_ROOT/scripts/start_backend.sh" > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$PROJECT_ROOT/logs/pids/backend.pid"

# 等待後端啟動
sleep 5

# 檢查後端是否正常啟動
if kill -0 $BACKEND_PID 2>/dev/null; then
    log_success "後端服務已啟動 (PID: $BACKEND_PID)"
else
    log_error "後端服務啟動失敗"
    exit 1
fi

# 啟動前端
log_info "啟動前端服務..."
bash "$PROJECT_ROOT/scripts/start_frontend.sh" > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$PROJECT_ROOT/logs/pids/frontend.pid"

# 等待前端啟動
sleep 3

if kill -0 $FRONTEND_PID 2>/dev/null; then
    log_success "前端服務已啟動 (PID: $FRONTEND_PID)"
else
    log_error "前端服務啟動失敗"
    exit 1
fi

log_success "系統啟動完成！"
echo ""
echo "服務地址："
echo "  前端: http://localhost:3000"
echo "  後端: http://localhost:8000"
echo ""
echo "日誌文件："
echo "  後端: $PROJECT_ROOT/logs/backend.log"
echo "  前端: $PROJECT_ROOT/logs/frontend.log"
echo ""
echo "停止服務: bash $PROJECT_ROOT/scripts/stop_system.sh"
EOF

    # 系統停止腳本
    cat > "$PROJECT_ROOT/scripts/stop_system.sh" << 'EOF'
#!/bin/bash

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

# 停止前端
if [[ -f "$PROJECT_ROOT/logs/pids/frontend.pid" ]]; then
    FRONTEND_PID=$(cat "$PROJECT_ROOT/logs/pids/frontend.pid")
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        log_info "停止前端服務 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm "$PROJECT_ROOT/logs/pids/frontend.pid"
        log_success "前端服務已停止"
    fi
fi

# 停止後端
if [[ -f "$PROJECT_ROOT/logs/pids/backend.pid" ]]; then
    BACKEND_PID=$(cat "$PROJECT_ROOT/logs/pids/backend.pid")
    if kill -0 $BACKEND_PID 2>/dev/null; then
        log_info "停止後端服務 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        rm "$PROJECT_ROOT/logs/pids/backend.pid"
        log_success "後端服務已停止"
    fi
fi

log_success "系統已完全停止"
EOF

    # 設置執行權限
    chmod +x "$PROJECT_ROOT/scripts/start_backend.sh"
    chmod +x "$PROJECT_ROOT/scripts/start_frontend.sh"
    chmod +x "$PROJECT_ROOT/scripts/start_system.sh"
    chmod +x "$PROJECT_ROOT/scripts/stop_system.sh"
    
    log_success "服務管理腳本創建完成"
}

# 執行系統驗證
run_system_validation() {
    log_step "執行系統驗證..."
    
    cd "$PROJECT_ROOT"
    
    # Python 環境驗證
    source venv/bin/activate
    python -c "
import sys
import subprocess

print(f'Python 版本: {sys.version}')

# 檢查關鍵套件
packages = ['fastapi', 'uvicorn', 'requests', 'openai']
for package in packages:
    try:
        __import__(package)
        print(f'✓ {package} 已安裝')
    except ImportError:
        print(f'✗ {package} 未安裝')
"
    
    # 前端驗證
    cd "$PROJECT_ROOT/frontend"
    if [[ -f "package.json" ]]; then
        log_info "檢查前端依賴..."
        npm list --depth=0 2>/dev/null | grep -E "(svelte|vite)" || log_warning "前端框架檢查異常"
    fi
    
    # 配置文件驗證
    cd "$PROJECT_ROOT"
    if [[ -f "config/config_manager.py" ]]; then
        python -c "
from config.config_manager import ConfigManager
cm = ConfigManager()
print('✓ 配置管理器正常')
print(f'✓ 當前模式: {cm.current_mode}')
errors = cm.validate_config()
if errors:
    print('配置驗證錯誤:')
    for error in errors:
        print(f'  - {error}')
else:
    print('✓ 配置驗證通過')
"
    fi
    
    log_success "系統驗證完成"
}

# 顯示部署總結
show_deployment_summary() {
    echo ""
    echo "========================================"
    echo "         部署完成總結"
    echo "========================================"
    echo ""
    echo "🎉 恭喜！Auto Video Generation 系統已成功部署"
    echo ""
    echo "📋 部署信息："
    echo "  • 模式: $DEPLOY_MODE"
    echo "  • 專案路徑: $PROJECT_ROOT"
    echo "  • Python 環境: $PROJECT_ROOT/venv"
    echo "  • 資料庫: SQLite (data/app.db)"
    echo ""
    echo "🚀 啟動系統："
    echo "  bash $PROJECT_ROOT/scripts/start_system.sh"
    echo ""
    echo "🛑 停止系統："
    echo "  bash $PROJECT_ROOT/scripts/stop_system.sh"
    echo ""
    echo "🔗 服務地址："
    echo "  • 前端: http://localhost:3000"
    echo "  • 後端: http://localhost:8000"
    echo "  • API 文檔: http://localhost:8000/docs"
    echo ""
    echo "📊 模式切換："
    echo "  bash $PROJECT_ROOT/scripts/switch_mode.sh [startup|enterprise]"
    echo ""
    echo "📝 日誌文件："
    echo "  • 部署日誌: $LOG_FILE"
    echo "  • 運行日誌: $PROJECT_ROOT/logs/"
    echo ""
    echo "⚙️  下一步建議："
    echo "  1. 檢查並修改 .env 文件中的 API 密鑰"
    echo "  2. 根據需要調整配置文件"
    echo "  3. 執行系統健康檢查: bash scripts/system-validation.sh"
    echo ""
    echo "========================================="
}

# 主函數
main() {
    echo ""
    echo "========================================"
    echo "   Auto Video Generation 單機部署工具"
    echo "========================================"
    echo ""
    echo "部署模式: $DEPLOY_MODE"
    echo "專案路徑: $PROJECT_ROOT"
    echo "強制重新安裝: $FORCE_REINSTALL"
    echo ""
    
    # 記錄開始時間
    START_TIME=$(date)
    echo "開始時間: $START_TIME" | tee -a "$LOG_FILE"
    
    # 執行部署步驟
    check_system_requirements 2>&1 | tee -a "$LOG_FILE"
    install_python_dependencies 2>&1 | tee -a "$LOG_FILE"
    install_nodejs_dependencies 2>&1 | tee -a "$LOG_FILE"
    setup_configuration 2>&1 | tee -a "$LOG_FILE"
    initialize_database 2>&1 | tee -a "$LOG_FILE"
    build_frontend 2>&1 | tee -a "$LOG_FILE"
    create_service_scripts 2>&1 | tee -a "$LOG_FILE"
    run_system_validation 2>&1 | tee -a "$LOG_FILE"
    
    # 記錄結束時間
    END_TIME=$(date)
    echo "結束時間: $END_TIME" | tee -a "$LOG_FILE"
    
    show_deployment_summary
    
    log_success "單機部署完成！系統已準備就緒。"
}

# 顯示使用方法
show_usage() {
    echo "使用方法: $0 [模式] [選項]"
    echo ""
    echo "模式:"
    echo "  startup     創業模式 (預設) - 輕量化配置"
    echo "  enterprise  企業模式 - 高效能配置"
    echo ""
    echo "選項:"
    echo "  true        強制重新安裝所有依賴"
    echo "  false       跳過已安裝的依賴 (預設)"
    echo ""
    echo "範例:"
    echo "  $0                    # 使用創業模式部署"
    echo "  $0 enterprise         # 使用企業模式部署"
    echo "  $0 startup true       # 創業模式 + 強制重新安裝"
}

# 檢查參數
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_usage
    exit 0
fi

if [[ "$DEPLOY_MODE" != "startup" ]] && [[ "$DEPLOY_MODE" != "enterprise" ]]; then
    log_error "無效的部署模式: $DEPLOY_MODE"
    show_usage
    exit 1
fi

# 執行主函數
main "$@"