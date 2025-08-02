#!/bin/bash

# Auto Video 開發環境快速設置腳本
# 自動配置開發工具、依賴項和環境變數

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 檢查系統要求
check_system_requirements() {
    log_info "檢查系統要求..."
    
    # 檢查 Python 版本
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version | cut -d' ' -f2)
        log_success "Python 版本: $python_version"
    else
        log_error "Python 3 未安裝"
        exit 1
    fi
    
    # 檢查 Node.js 版本
    if command -v node &> /dev/null; then
        node_version=$(node --version)
        log_success "Node.js 版本: $node_version"
    else
        log_error "Node.js 未安裝"
        exit 1
    fi
    
    # 檢查 Docker
    if command -v docker &> /dev/null; then
        docker_version=$(docker --version | cut -d' ' -f3 | sed 's/,//')
        log_success "Docker 版本: $docker_version"
    else
        log_warning "Docker 未安裝，建議安裝以便容器化開發"
    fi
    
    # 檢查 Git
    if command -v git &> /dev/null; then
        git_version=$(git --version | cut -d' ' -f3)
        log_success "Git 版本: $git_version"
    else
        log_error "Git 未安裝"
        exit 1
    fi
}

# 設置 Python 虛擬環境
setup_python_env() {
    log_info "設置 Python 虛擬環境..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "虛擬環境已創建"
    else
        log_info "虛擬環境已存在"
    fi
    
    # 激活虛擬環境
    source venv/bin/activate || {
        log_error "無法激活虛擬環境"
        exit 1
    }
    
    # 升級 pip
    pip install --upgrade pip
    
    # 安裝開發依賴
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
        log_success "開發依賴已安裝"
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "基本依賴已安裝"
    else
        log_warning "未找到 requirements 文件"
    fi
    
    # 安裝測試和品質保證工具
    pip install pytest pytest-cov black isort flake8 mypy bandit safety
    log_success "測試和品質工具已安裝"
}

# 設置 Node.js 環境
setup_nodejs_env() {
    log_info "設置 Node.js 環境..."
    
    if [ -d "frontend" ]; then
        cd frontend
        
        # 安裝依賴
        if [ -f "package.json" ]; then
            npm install
            log_success "前端依賴已安裝"
        else
            log_warning "前端目錄未找到 package.json"
        fi
        
        cd ..
    else
        log_warning "前端目錄不存在"
    fi
}

# 創建開發配置文件
create_dev_config() {
    log_info "創建開發配置文件..."
    
    # 創建 .env.dev 文件
    if [ ! -f ".env.dev" ]; then
        cat > .env.dev << EOF
# 開發環境配置
DEBUG=true
ENVIRONMENT=development

# 資料庫
DATABASE_URL=postgresql://postgres:password@localhost:5432/autovideo_dev
REDIS_URL=redis://localhost:6379/0

# JWT 設定
JWT_SECRET_KEY=dev-secret-key-change-in-production-32chars
JWT_ALGORITHM=RS256
JWT_EXPIRE_MINUTES=60

# AI 服務 (開發用測試 API Key)
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# 社群媒體 API
TIKTOK_CLIENT_ID=your-tiktok-client-id
TIKTOK_CLIENT_SECRET=your-tiktok-client-secret
YOUTUBE_API_KEY=your-youtube-api-key
INSTAGRAM_ACCESS_TOKEN=your-instagram-token

# 監控
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001

# 開發工具
HOT_RELOAD=true
LOG_LEVEL=DEBUG
ENABLE_CORS=true
EOF
        log_success "開發環境配置文件已創建: .env.dev"
    else
        log_info "開發環境配置文件已存在"
    fi
    
    # 創建測試配置
    if [ ! -f ".env.test" ]; then
        cat > .env.test << EOF
# 測試環境配置
DEBUG=false
ENVIRONMENT=test

# 測試資料庫
DATABASE_URL=postgresql://postgres:password@localhost:5432/autovideo_test
REDIS_URL=redis://localhost:6379/1

# JWT 設定
JWT_SECRET_KEY=test-secret-key-32chars-for-testing
JWT_ALGORITHM=RS256
JWT_EXPIRE_MINUTES=15

# 禁用外部 API 調用
DISABLE_EXTERNAL_APIS=true
MOCK_AI_SERVICES=true

# 測試設定
RUN_INTEGRATION_TESTS=true
TEST_COVERAGE_MIN=80
EOF
        log_success "測試環境配置文件已創建: .env.test"
    else
        log_info "測試環境配置文件已存在"
    fi
}

# 設置 Git hooks
setup_git_hooks() {
    log_info "設置 Git hooks..."
    
    # 創建 pre-commit hook
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for Auto Video project

echo "🔍 執行代碼檢查..."

# 激活虛擬環境
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Python 代碼格式檢查
if [ -n "$(find . -name '*.py' -not -path './venv/*' -not -path './.git/*')" ]; then
    echo "🐍 檢查 Python 代碼格式..."
    
    # Black 格式化
    black --check . || {
        echo "❌ Black 格式化失敗，請執行: black ."
        exit 1
    }
    
    # isort 導入排序
    isort --check-only . || {
        echo "❌ isort 檢查失敗，請執行: isort ."
        exit 1
    }
    
    # Flake8 代碼品質
    flake8 . || {
        echo "❌ Flake8 檢查失敗"
        exit 1
    }
fi

# 前端代碼檢查
if [ -d "frontend" ]; then
    echo "🌐 檢查前端代碼..."
    cd frontend
    
    # ESLint 檢查
    npm run lint || {
        echo "❌ ESLint 檢查失敗"
        exit 1
    }
    
    # Prettier 格式檢查
    npm run format:check || {
        echo "❌ Prettier 格式檢查失敗，請執行: npm run format"
        exit 1
    }
    
    cd ..
fi

# 運行快速測試
echo "🧪 執行快速測試..."
python -m pytest tests/ -x --tb=short -q || {
    echo "❌ 測試失敗"
    exit 1
}

echo "✅ 代碼檢查通過"
EOF
    
    chmod +x .git/hooks/pre-commit
    log_success "Git pre-commit hook 已設置"
    
    # 創建 commit-msg hook
    cat > .git/hooks/commit-msg << 'EOF'
#!/bin/bash
# Commit message validation

commit_regex='^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "❌ 提交消息格式錯誤"
    echo "正確格式: type(scope): description"
    echo "類型: feat, fix, docs, style, refactor, test, chore"
    echo "例如: feat(auth): add OAuth login support"
    exit 1
fi
EOF
    
    chmod +x .git/hooks/commit-msg
    log_success "Git commit-msg hook 已設置"
}

# 創建開發工具腳本
create_dev_scripts() {
    log_info "創建開發工具腳本..."
    
    mkdir -p scripts
    
    # 測試腳本
    cat > scripts/test.sh << 'EOF'
#!/bin/bash
# 測試執行腳本

set -e

echo "🧪 執行完整測試套件..."

# 激活虛擬環境
source venv/bin/activate

# 設置測試環境
export PYTHONPATH=$PWD
export ENV_FILE=.env.test

# 運行 Python 測試
echo "🐍 執行 Python 測試..."
python -m pytest tests/ \
    --cov=. \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-fail-under=80 \
    -v

# 運行前端測試
if [ -d "frontend" ]; then
    echo "🌐 執行前端測試..."
    cd frontend
    npm test
    cd ..
fi

echo "✅ 所有測試通過"
EOF
    
    chmod +x scripts/test.sh
    
    # 代碼品質檢查腳本
    cat > scripts/quality-check.sh << 'EOF'
#!/bin/bash
# 代碼品質檢查腳本

set -e

echo "🔍 執行代碼品質檢查..."

# 激活虛擬環境
source venv/bin/activate

# Python 代碼檢查
echo "🐍 Python 代碼品質檢查..."

# 格式化
black .
isort .

# 代碼品質
flake8 .
mypy . --ignore-missing-imports

# 安全檢查
bandit -r . -x tests/,venv/
safety check

# 前端代碼檢查
if [ -d "frontend" ]; then
    echo "🌐 前端代碼品質檢查..."
    cd frontend
    npm run lint -- --fix
    npm run format
    cd ..
fi

echo "✅ 代碼品質檢查完成"
EOF
    
    chmod +x scripts/quality-check.sh
    
    # 開發服務器啟動腳本
    cat > scripts/dev-server.sh << 'EOF'
#!/bin/bash
# 開發服務器啟動腳本

set -e

echo "🚀 啟動開發服務器..."

# 激活虛擬環境
source venv/bin/activate

# 設置開發環境
export ENV_FILE=.env.dev

# 啟動後端服務 (背景執行)
echo "🔧 啟動後端服務..."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 啟動前端服務
if [ -d "frontend" ]; then
    echo "🌐 啟動前端服務..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
fi

echo "✅ 開發服務器已啟動"
echo "🔧 後端: http://localhost:8000"
echo "🌐 前端: http://localhost:3000"
echo ""
echo "按 Ctrl+C 停止服務器"

# 等待中斷信號
trap 'kill $BACKEND_PID $FRONTEND_PID; exit' INT
wait
EOF
    
    chmod +x scripts/dev-server.sh
    
    log_success "開發工具腳本已創建"
}

# 設置 IDE 配置
setup_ide_config() {
    log_info "設置 IDE 配置..."
    
    # VS Code 配置
    mkdir -p .vscode
    
    cat > .vscode/settings.json << 'EOF'
{
    "python.pythonPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/venv": true,
        "**/node_modules": true,
        "**/.pytest_cache": true,
        "**/htmlcov": true
    },
    "search.exclude": {
        "**/venv": true,
        "**/node_modules": true,
        "**/.git": true
    }
}
EOF
    
    cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": ["main:app", "--reload"],
            "envFile": "${workspaceFolder}/.env.dev",
            "console": "integratedTerminal"
        },
        {
            "name": "Python: Pytest",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "envFile": "${workspaceFolder}/.env.test",
            "console": "integratedTerminal"
        }
    ]
}
EOF
    
    cat > .vscode/extensions.json << 'EOF'
{
    "recommendations": [
        "ms-python.python",
        "ms-python.flake8",
        "ms-python.mypy-type-checker",
        "ms-python.black-formatter",
        "ms-python.isort",
        "bradlc.vscode-tailwindcss",
        "svelte.svelte-vscode",
        "ms-vscode.vscode-typescript-next",
        "esbenp.prettier-vscode",
        "ms-vscode.vscode-eslint",
        "formulahendry.auto-rename-tag",
        "ms-vscode.vscode-json"
    ]
}
EOF
    
    log_success "VS Code 配置已設置"
}

# 執行初始化測試
run_initial_tests() {
    log_info "執行初始化測試..."
    
    # 激活虛擬環境
    source venv/bin/activate
    
    # 檢查 Python 導入
    python -c "import fastapi, pydantic, sqlalchemy" 2>/dev/null && {
        log_success "Python 依賴檢查通過"
    } || {
        log_warning "部分 Python 依賴缺失"
    }
    
    # 檢查前端依賴
    if [ -d "frontend/node_modules" ]; then
        log_success "前端依賴檢查通過"
    else
        log_warning "前端依賴未安裝完成"
    fi
    
    # 運行基本測試
    if [ -d "tests" ]; then
        python -m pytest tests/ --tb=short -q && {
            log_success "基本測試通過"
        } || {
            log_warning "部分測試失敗，請檢查代碼"
        }
    else
        log_info "測試目錄不存在，跳過測試"
    fi
}

# 顯示完成信息
show_completion_info() {
    echo ""
    echo "🎉 開發環境設置完成！"
    echo ""
    echo "📋 快速開始："
    echo "  1. 激活虛擬環境: source venv/bin/activate"
    echo "  2. 設置環境變數: cp .env.dev .env"
    echo "  3. 啟動開發服務器: ./scripts/dev-server.sh"
    echo "  4. 執行測試: ./scripts/test.sh"
    echo "  5. 代碼品質檢查: ./scripts/quality-check.sh"
    echo ""
    echo "🔧 開發工具："
    echo "  • 後端 API: http://localhost:8000"
    echo "  • 前端應用: http://localhost:3000"
    echo "  • API 文檔: http://localhost:8000/docs"
    echo "  • Grafana 監控: http://localhost:3001"
    echo ""
    echo "📚 更多信息請查看 README.md 和文檔目錄"
}

# 主函數
main() {
    echo "🚀 Auto Video 開發環境設置"
    echo "=============================="
    echo ""
    
    check_system_requirements
    setup_python_env
    setup_nodejs_env
    create_dev_config
    setup_git_hooks
    create_dev_scripts
    setup_ide_config
    run_initial_tests
    show_completion_info
}

# 執行主函數
main "$@"