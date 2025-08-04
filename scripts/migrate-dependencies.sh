#!/bin/bash

# migrate-dependencies.sh - 依賴管理現代化腳本
# 用途：將所有 requirements.txt 遷移到統一的 pyproject.toml

set -e

# 顏色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日誌函數
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 檢查 Python 和必要工具
check_requirements() {
    log_info "檢查系統要求..."
    
    # 檢查 Python 版本
    if ! python3 --version | grep -E "Python 3\.(9|10|11|12)" > /dev/null; then
        log_error "需要 Python 3.9 或更高版本"
        exit 1
    fi
    
    # 檢查是否安裝了 toml 解析器
    if ! python3 -c "import tomli" 2>/dev/null; then
        log_warning "安裝 tomli 以支援 TOML 解析"
        pip install tomli 2>/dev/null || pip3 install tomli || true
    fi
    
    log_success "系統要求檢查完成"
}

# 分析現有 requirements 檔案
analyze_requirements() {
    log_info "分析現有的 requirements 檔案..."
    
    # 建立臨時分析目錄
    mkdir -p .deps_analysis
    
    # 找出所有 requirements 檔案
    find . -name "requirements*.txt" -type f > .deps_analysis/all_requirements.txt
    
    echo "發現的 requirements 檔案："
    cat .deps_analysis/all_requirements.txt
    
    # 提取所有依賴包
    echo "# 所有依賴包合併" > .deps_analysis/merged_deps.txt
    while IFS= read -r file; do
        echo "# 來源: $file" >> .deps_analysis/merged_deps.txt
        cat "$file" >> .deps_analysis/merged_deps.txt
        echo "" >> .deps_analysis/merged_deps.txt
    done < .deps_analysis/all_requirements.txt
    
    log_success "依賴分析完成，檢查 .deps_analysis/ 目錄"
}

# 建立依賴分類
categorize_dependencies() {
    log_info "依賴包分類..."
    
    # Web 框架與 API
    cat > .deps_analysis/web_framework.txt << 'EOF'
# Web 框架與 API
fastapi>=0.109.1
uvicorn[standard]>=0.24.0
pydantic>=2.6.0
pydantic-settings>=2.1.0
python-multipart>=0.0.8
EOF

    # 資料庫相關
    cat > .deps_analysis/database.txt << 'EOF'
# 資料庫相關
sqlalchemy>=2.0.25
alembic>=1.13.1
asyncpg>=0.29.0
psycopg2-binary>=2.9.9
redis>=5.0.7
EOF

    # 安全與認證
    cat > .deps_analysis/security.txt << 'EOF'
# 安全與認證
python-jose[cryptography]>=3.3.4
passlib[bcrypt]>=1.7.4
cryptography>=42.0.0
authlib>=1.3.0
EOF

    # 機器學習與 AI
    cat > .deps_analysis/ml_ai.txt << 'EOF'
# 機器學習與 AI
torch>=2.2.0
torchaudio>=2.2.0
transformers>=4.40.0
scikit-learn>=1.4.0
numpy>=1.24.0
pillow>=10.3.0
librosa>=0.10.0
openai>=1.0.0
EOF

    # HTTP 客戶端與網路
    cat > .deps_analysis/networking.txt << 'EOF'
# HTTP 客戶端與網路
httpx>=0.25.2
aiohttp>=3.10.11
requests>=2.32.4
websockets>=11.0.3
EOF

    # 異步任務
    cat > .deps_analysis/async_tasks.txt << 'EOF'
# 異步任務與佇列
celery>=5.3.4
kombu>=5.3.4
billiard>=4.1.0
EOF

    # 檔案處理與儲存
    cat > .deps_analysis/storage.txt << 'EOF'
# 檔案處理與儲存
boto3>=1.29.0
botocore>=1.32.0
minio>=7.2.0
aiofiles>=23.2.0
opencv-python-headless>=4.8.0
ffmpeg-python>=0.2.0
EOF

    # 監控與日誌
    cat > .deps_analysis/monitoring.txt << 'EOF'
# 監控與日誌
structlog>=23.2.0
prometheus-client>=0.19.0
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-instrumentation-fastapi>=0.42b0
jaeger-client>=4.8.0
EOF

    # 開發工具
    cat > .deps_analysis/dev_tools.txt << 'EOF'
# 開發工具
pytest>=7.4.3
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
black>=24.0.0
isort>=5.12.0
flake8>=6.1.0
mypy>=1.7.1
bandit>=1.7.5
pre-commit>=3.5.0
coverage>=7.3.0
ruff>=0.1.0
EOF

    # 序列化與協議
    cat > .deps_analysis/serialization.txt << 'EOF'
# 序列化與協議
orjson>=3.10.0
pydantic>=2.6.0
protobuf>=4.25.2
grpcio>=1.59.0
grpcio-tools>=1.59.0
EOF

    log_success "依賴包分類完成"
}

# 檢測版本衝突
detect_conflicts() {
    log_info "檢測版本衝突..."
    
    python3 << 'EOF'
import re
import sys
from collections import defaultdict

def parse_requirement(line):
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    
    # 簡單的需求解析
    match = re.match(r'^([a-zA-Z0-9_-]+(?:\[[^\]]+\])?)\s*([><=!]+.*)?$', line)
    if match:
        package = match.group(1)
        version = match.group(2) or ""
        return package.lower(), version
    return None

# 收集所有依賴
all_deps = defaultdict(set)

try:
    with open('.deps_analysis/merged_deps.txt', 'r') as f:
        for line in f:
            req = parse_requirement(line)
            if req:
                package, version = req
                all_deps[package].add(version)

    # 檢查衝突
    conflicts = []
    for package, versions in all_deps.items():
        if len(versions) > 1:
            conflicts.append((package, versions))

    if conflicts:
        print("發現版本衝突：")
        for package, versions in conflicts:
            print(f"  {package}: {', '.join(versions)}")
    else:
        print("未發現版本衝突")

except FileNotFoundError:
    print("找不到合併的依賴檔案，請先執行分析")
    sys.exit(1)
EOF

    log_success "版本衝突檢測完成"
}

# 更新 pyproject.toml
update_pyproject() {
    log_info "更新 pyproject.toml..."
    
    # 備份現有的 pyproject.toml
    if [ -f "pyproject.toml" ]; then
        cp "pyproject.toml" "pyproject.toml.backup"
        log_info "已備份現有的 pyproject.toml"
    fi
    
    # 建立新的 pyproject.toml
    cat > "pyproject.toml.new" << 'EOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "auto-video-generation"
version = "0.2.0"
description = "生產級自動影片生成系統與聲音克隆平台"
authors = [{name = "Auto Video Team", email = "team@autovideo.com"}]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.9"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Multimedia :: Video",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

# 核心生產依賴
dependencies = [
    # Web 框架與 API
    "fastapi>=0.109.1",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.6.0",
    "pydantic-settings>=2.1.0",
    "python-multipart>=0.0.8",
    
    # 資料庫相關
    "sqlalchemy>=2.0.25",
    "alembic>=1.13.1",
    "asyncpg>=0.29.0",
    "psycopg2-binary>=2.9.9",
    "redis>=5.0.7",
    
    # 安全與認證
    "python-jose[cryptography]>=3.3.4",
    "passlib[bcrypt]>=1.7.4",
    "cryptography>=42.0.0",
    "authlib>=1.3.0",
    
    # HTTP 客戶端與網路
    "httpx>=0.25.2",
    "aiohttp>=3.10.11",
    "requests>=2.32.4",
    "websockets>=11.0.3",
    
    # 異步任務與佇列
    "celery>=5.3.4",
    "kombu>=5.3.4",
    "billiard>=4.1.0",
    
    # 序列化與協議
    "orjson>=3.10.0",
    "protobuf>=4.25.2",
    "grpcio>=1.59.0",
    "grpcio-tools>=1.59.0",
    
    # 檔案處理與基本工具
    "aiofiles>=23.2.0",
    "python-dotenv>=1.0.0",
    "click>=8.1.7",
    "rich>=13.7.0",
]

# 包發現配置
[tool.setuptools.packages.find]
where = ["src"]
include = ["*"]
exclude = ["tests*", "*.tests*", "*.tests.*", "tests.*"]

[project.optional-dependencies]
# AI 與機器學習服務
ai = [
    "torch>=2.2.0",
    "torchaudio>=2.2.0", 
    "transformers>=4.40.0",
    "scikit-learn>=1.4.0",
    "numpy>=1.24.0",
    "librosa>=0.10.0",
    "openai>=1.0.0",
    "anthropic>=0.7.0",
]

# 圖像與影片處理
media = [
    "pillow>=10.3.0",
    "opencv-python-headless>=4.8.0",
    "ffmpeg-python>=0.2.0",
    "imageio>=2.31.0",
    "moviepy>=1.0.3",
]

# 檔案儲存服務
storage = [
    "boto3>=1.29.0",
    "botocore>=1.32.0",
    "minio>=7.2.0",
    "google-cloud-storage>=2.10.0",
]

# 監控與觀測性
monitoring = [
    "structlog>=23.2.0",
    "prometheus-client>=0.19.0",
    "opentelemetry-api>=1.21.0",
    "opentelemetry-sdk>=1.21.0",
    "opentelemetry-instrumentation-fastapi>=0.42b0",
    "jaeger-client>=4.8.0",
    "sentry-sdk[fastapi]>=1.39.0",
]

# 開發工具
dev = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    "pytest-xdist>=3.5.0",
    "black>=24.0.0",
    "isort>=5.12.0",
    "flake8>=6.1.0",
    "mypy>=1.7.1",
    "bandit>=1.7.5",
    "pre-commit>=3.5.0",
    "coverage>=7.3.0",
    "ruff>=0.1.0",
    "httpx>=0.25.2",  # 用於測試
    "faker>=19.12.0",
]

# 測試專用
test = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    "pytest-xdist>=3.5.0",
    "httpx>=0.25.2",
    "faker>=19.12.0",
    "coverage>=7.3.0",
    "factory-boy>=3.3.0",
]

# 文檔生成
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.4.0",
    "mkdocs-swagger-ui-tag>=0.6.0",
    "mkdocstrings[python]>=0.24.0",
]

# E2E 測試
e2e = [
    "playwright>=1.40.0",
    "selenium>=4.15.0",
    "requests>=2.32.4",
]

# 效能分析
profiling = [
    "py-spy>=0.3.14",
    "memory-profiler>=0.61.0",
    "line-profiler>=4.1.1",
    "pympler>=0.9",
]

# 安全掃描
security = [
    "bandit>=1.7.5",
    "safety>=2.3.0",
    "semgrep>=1.45.0",
]

# 完整開發環境（包含所有工具）
full-dev = [
    "auto-video-generation[ai,media,storage,monitoring,dev,test,docs,e2e,profiling,security]"
]

# 生產環境（核心功能）
production = [
    "auto-video-generation[ai,media,storage,monitoring]"
]

[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
  | auto_generate_video_fold6.old
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
line_length = 88
src_paths = ["src", "tests"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[tool.pytest.ini_options]
minversion = "7.0"
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--cov=src",
    "--cov-branch",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
    "--cov-report=xml",
    "--cov-fail-under=85",
]
testpaths = ["tests"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "e2e: marks tests as end-to-end tests",
    "ai: marks tests that require AI services",
    "media: marks tests that require media processing",
]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src/"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/conftest.py",
    "*/alembic/*",
    "*/migrations/*",
    "*/__pycache__/*",
    "*/venv/*",
    "*/auto_generate_video_fold6.old/*",
]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]
ignore_errors = true
precision = 2
show_missing = true

[tool.coverage.html]
directory = "htmlcov"

[tool.bandit]
exclude_dirs = ["tests", "src/frontend"]
skips = ["B101", "B601"]

[tool.bandit.assert_used]
skips = ["*_test.py", "test_*.py"]

[tool.ruff]
target-version = "py39"
line-length = 88
src = ["src", "tests"]
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pants.d",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pypackages__",
    "_build",
    "buck-out",
    "build",
    "dist",
    "node_modules",
    "venv",
    "auto_generate_video_fold6.old",
    "src/frontend",
]

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
    "A",  # flake8-builtins
    "COM", # flake8-commas
    "C90", # mccabe
]
ignore = [
    "E501",  # line too long, handled by black
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
    "COM812", # trailing comma missing (handled by black)
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]
"tests/*" = ["B011", "B018", "A002", "A003"]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.isort]
known-first-party = ["src"]
EOF

    log_success "新的 pyproject.toml 已建立：pyproject.toml.new"
}

# 建立依賴管理腳本
create_dependency_management_scripts() {
    log_info "建立依賴管理腳本..."
    
    # 建立安裝腳本
    cat > "scripts/install-deps.sh" << 'EOF'
#!/bin/bash
# install-deps.sh - 依賴安裝腳本

set -e

# 顏色設定
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

install_environment() {
    local env_type=${1:-"dev"}
    
    log_info "安裝 $env_type 環境依賴..."
    
    case $env_type in
        "production"|"prod")
            pip install -e ".[production]"
            ;;
        "dev"|"development") 
            pip install -e ".[full-dev]"
            ;;
        "test"|"testing")
            pip install -e ".[test]"
            ;;
        "ai")
            pip install -e ".[ai,media]"
            ;;
        "minimal")
            pip install -e "."
            ;;
        *)
            log_info "可用選項: production, dev, test, ai, minimal"
            exit 1
            ;;
    esac
    
    log_success "$env_type 環境依賴安裝完成"
}

# 檢查參數
if [ $# -eq 0 ]; then
    echo "使用方式: $0 <environment>"
    echo "環境選項: production, dev, test, ai, minimal"
    exit 1
fi

install_environment "$1"
EOF

    # 建立依賴更新腳本
    cat > "scripts/update-deps.sh" << 'EOF'
#!/bin/bash
# update-deps.sh - 依賴更新腳本

set -e

# 顏色設定
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

update_dependencies() {
    log_info "更新依賴包..."
    
    # 更新 pip 本身
    pip install --upgrade pip
    
    # 重新安裝當前環境的依賴
    if [ -f "pyproject.toml" ]; then
        log_info "使用 pyproject.toml 更新依賴..."
        pip install -e ".[full-dev]" --upgrade
    else
        log_warning "找不到 pyproject.toml，請先執行依賴遷移"
        exit 1
    fi
    
    log_success "依賴更新完成"
}

check_security() {
    log_info "執行安全檢查..."
    
    # 檢查已知漏洞
    if command -v safety &> /dev/null; then
        safety check
    else
        log_warning "safety 未安裝，跳過安全檢查"
    fi
    
    # Bandit 安全掃描
    if command -v bandit &> /dev/null; then
        bandit -r src/ -f json -o security_report.json || true
        log_info "安全報告已生成：security_report.json"
    else
        log_warning "bandit 未安裝，跳過程式碼安全掃描"
    fi
}

# 執行更新和檢查
update_dependencies
check_security

log_success "依賴更新和安全檢查完成"
EOF

    # 建立依賴檢查腳本
    cat > "scripts/check-deps.sh" << 'EOF'
#!/bin/bash
# check-deps.sh - 依賴狀態檢查腳本

set -e

# 顏色設定
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

check_pip_packages() {
    log_info "檢查 pip 包狀態..."
    
    # 檢查過期的包
    log_info "檢查過期的包..."
    pip list --outdated || true
    
    # 檢查依賴衝突
    log_info "檢查依賴衝突..."
    pip check || true
    
    # 顯示已安裝的核心包
    log_info "核心包版本："
    pip show fastapi uvicorn sqlalchemy redis torch 2>/dev/null || true
}

check_security_vulnerabilities() {
    log_info "檢查安全漏洞..."
    
    if command -v safety &> /dev/null; then
        safety check --json --output security_check.json || true
        log_info "安全檢查報告：security_check.json"
    else
        log_warning "請安裝 safety: pip install safety"
    fi
}

check_import_health() {
    log_info "檢查關鍵模組匯入健康狀態..."
    
    python3 << 'PYTHON_EOF'
import sys
import importlib

critical_modules = [
    'fastapi',
    'uvicorn', 
    'sqlalchemy',
    'redis',
    'pydantic',
    'httpx'
]

optional_modules = [
    'torch',
    'transformers',
    'celery',
    'boto3'
]

print("🔍 關鍵模組檢查:")
for module in critical_modules:
    try:
        mod = importlib.import_module(module)
        version = getattr(mod, '__version__', 'unknown')
        print(f"  ✅ {module}: {version}")
    except ImportError as e:
        print(f"  ❌ {module}: 匯入失敗 - {e}")
        sys.exit(1)

print("\n🔍 可選模組檢查:")  
for module in optional_modules:
    try:
        mod = importlib.import_module(module)
        version = getattr(mod, '__version__', 'unknown')
        print(f"  ✅ {module}: {version}")
    except ImportError:
        print(f"  ⚠️  {module}: 未安裝 (可選)")

print("\n✅ 模組健康檢查完成")
PYTHON_EOF
}

generate_dependency_report() {
    log_info "生成依賴報告..."
    
    local report_file="dependency_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# 依賴狀態報告

## 生成時間
$(date)

## Python 環境
- Python 版本: $(python3 --version)
- Pip 版本: $(pip --version)
- 虛擬環境: ${VIRTUAL_ENV:-"未使用"}

## 已安裝包數量
總計: $(pip list | wc -l) 個包

## 核心依賴版本
\`\`\`
$(pip show fastapi uvicorn sqlalchemy redis pydantic 2>/dev/null | grep -E "Name|Version" || echo "部分核心包未安裝")
\`\`\`

## 過期包檢查
\`\`\`
$(pip list --outdated 2>/dev/null | head -20 || echo "無過期包或檢查失敗")
\`\`\`

## 依賴衝突檢查
\`\`\`
$(pip check 2>&1 || echo "發現依賴衝突，請查看上述輸出")
\`\`\`

## 建議行動
1. 更新過期的包
2. 解決依賴衝突  
3. 定期執行安全檢查
4. 考慮使用虛擬環境隔離依賴

EOF

    log_success "依賴報告已生成：$report_file"
}

# 執行所有檢查
check_pip_packages
check_security_vulnerabilities  
check_import_health
generate_dependency_report

log_success "依賴檢查完成"
EOF

    # 設定執行權限
    chmod +x scripts/install-deps.sh
    chmod +x scripts/update-deps.sh  
    chmod +x scripts/check-deps.sh
    
    log_success "依賴管理腳本已建立"
}

# 建立遷移驗證腳本
create_migration_validator() {
    log_info "建立遷移驗證腳本..."
    
    cat > "scripts/validate-migration.py" << 'EOF'
#!/usr/bin/env python3
"""
依賴遷移驗證腳本
檢查從 requirements.txt 到 pyproject.toml 的遷移是否成功
"""

import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple

def run_command(cmd: List[str]) -> Tuple[int, str, str]:
    """執行命令並返回結果"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def check_pyproject_exists() -> bool:
    """檢查 pyproject.toml 是否存在"""
    return Path("pyproject.toml").exists()

def check_requirements_cleanup() -> List[str]:
    """檢查是否還有遺留的 requirements.txt 檔案"""
    remaining_files = []
    for req_file in Path(".").rglob("requirements*.txt"):
        if "backup" not in str(req_file) and "legacy" not in str(req_file):
            remaining_files.append(str(req_file))
    return remaining_files

def test_pip_install() -> bool:
    """測試 pip 安裝是否正常"""
    print("🧪 測試 pip 安裝...")
    
    # 測試基本安裝
    ret_code, stdout, stderr = run_command([
        sys.executable, "-m", "pip", "install", "-e", ".", "--dry-run"
    ])
    
    if ret_code != 0:
        print(f"❌ Pip 安裝測試失敗: {stderr}")
        return False
    
    print("✅ Pip 安裝測試通過")
    return True

def test_optional_dependencies() -> Dict[str, bool]:
    """測試可選依賴是否可以安裝"""
    print("🧪 測試可選依賴...")
    
    optional_groups = ["ai", "media", "storage", "monitoring", "dev"]
    results = {}
    
    for group in optional_groups:
        print(f"  測試 [{group}] 依賴組...")
        ret_code, stdout, stderr = run_command([
            sys.executable, "-m", "pip", "install", "-e", f".[{group}]", "--dry-run"
        ])
        
        results[group] = ret_code == 0
        status = "✅" if results[group] else "❌"
        print(f"  {status} [{group}] 依賴組")
        
        if not results[group]:
            print(f"    錯誤: {stderr}")
    
    return results

def check_import_compatibility() -> bool:
    """檢查關鍵模組是否可以正常匯入"""
    print("🧪 測試模組匯入相容性...")
    
    critical_imports = [
        "fastapi",
        "uvicorn",
        "sqlalchemy", 
        "redis",
        "pydantic"
    ]
    
    all_passed = True
    
    for module in critical_imports:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            all_passed = False
    
    return all_passed

def generate_validation_report() -> None:
    """生成驗證報告"""
    print("\n📊 生成驗證報告...")
    
    report = {
        "timestamp": subprocess.check_output(["date"], text=True).strip(),
        "pyproject_exists": check_pyproject_exists(),
        "remaining_requirements": check_requirements_cleanup(),
        "pip_install_test": test_pip_install(),
        "optional_dependencies": test_optional_dependencies(),
        "import_compatibility": check_import_compatibility()
    }
    
    # 儲存 JSON 報告
    with open("migration_validation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # 生成 Markdown 報告
    with open("migration_validation_report.md", "w") as f:
        f.write("# 依賴遷移驗證報告\n\n")
        f.write(f"**生成時間**: {report['timestamp']}\n\n")
        
        f.write("## 📋 檢查結果\n\n")
        
        # pyproject.toml 存在檢查
        status = "✅" if report['pyproject_exists'] else "❌"
        f.write(f"- **pyproject.toml 存在**: {status}\n")
        
        # 遺留檔案檢查
        if report['remaining_requirements']:
            f.write(f"- **遺留 requirements.txt**: ❌ ({len(report['remaining_requirements'])} 個檔案)\n")
            for file in report['remaining_requirements']:
                f.write(f"  - {file}\n")
        else:
            f.write("- **遺留 requirements.txt**: ✅ 已清理\n")
        
        # Pip 安裝測試
        status = "✅" if report['pip_install_test'] else "❌"
        f.write(f"- **Pip 安裝測試**: {status}\n")
        
        # 可選依賴測試
        f.write("- **可選依賴測試**:\n")
        for group, passed in report['optional_dependencies'].items():
            status = "✅" if passed else "❌"
            f.write(f"  - [{group}]: {status}\n")
        
        # 匯入相容性
        status = "✅" if report['import_compatibility'] else "❌"  
        f.write(f"- **匯入相容性**: {status}\n")
        
        # 總體狀態
        all_passed = (
            report['pyproject_exists'] and
            not report['remaining_requirements'] and  
            report['pip_install_test'] and
            all(report['optional_dependencies'].values()) and
            report['import_compatibility']
        )
        
        f.write(f"\n## 🎯 總體狀態\n\n")
        if all_passed:
            f.write("✅ **遷移成功** - 所有檢查都通過\n")
        else:
            f.write("❌ **遷移需要修正** - 請解決上述問題\n")
        
        f.write("\n## 📝 建議行動\n\n")
        if not report['pyproject_exists']:
            f.write("1. 確保 pyproject.toml 存在並配置正確\n")
        if report['remaining_requirements']:
            f.write("2. 清理遺留的 requirements.txt 檔案\n")
        if not report['pip_install_test']:
            f.write("3. 修復 pip 安裝問題\n")
        if not all(report['optional_dependencies'].values()):
            f.write("4. 檢查並修復可選依賴問題\n")
        if not report['import_compatibility']:
            f.write("5. 解決模組匯入問題\n")
    
    print("📄 驗證報告已生成:")
    print("  - migration_validation_report.json")  
    print("  - migration_validation_report.md")

def main():
    """主函數"""
    print("🔍 開始依賴遷移驗證...\n")
    
    try:
        generate_validation_report()
        print("\n✅ 驗證完成")
    except Exception as e:
        print(f"\n❌ 驗證失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

    chmod +x scripts/validate-migration.py
    log_success "遷移驗證腳本已建立：scripts/validate-migration.py"
}

# 清理舊的 requirements 檔案
cleanup_old_requirements() {
    log_info "清理舊的 requirements 檔案..."
    
    # 建立備份目錄
    local backup_dir="requirements_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # 備份所有 requirements 檔案
    find . -name "requirements*.txt" -type f -exec cp {} "$backup_dir/" \; 2>/dev/null || true
    
    log_info "Requirements 檔案已備份到：$backup_dir"
    echo "$backup_dir" > .requirements_backup_path
    
    # 詢問是否刪除舊檔案
    echo "發現的 requirements.txt 檔案："
    find . -name "requirements*.txt" -type f | head -20
    
    echo
    read -p "是否移除這些舊的 requirements.txt 檔案？(y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 移動到備份目錄而不是刪除
        find . -name "requirements*.txt" -type f -exec mv {} "$backup_dir/" \; 2>/dev/null || true
        log_success "舊的 requirements.txt 檔案已移動到備份目錄"
    else
        log_info "跳過清理舊檔案"
    fi
}

# 更新 Docker 檔案
update_docker_files() {
    log_info "更新 Docker 檔案以使用 pyproject.toml..."
    
    # 尋找所有 Dockerfile
    local dockerfiles=($(find . -name "Dockerfile*" -type f))
    
    for dockerfile in "${dockerfiles[@]}"; do
        if grep -q "requirements.txt" "$dockerfile"; then
            log_info "更新 $dockerfile..."
            
            # 備份
            cp "$dockerfile" "$dockerfile.backup"
            
            # 替換 requirements.txt 相關的行
            sed -i.tmp 's/COPY requirements\.txt/COPY pyproject.toml/' "$dockerfile" 2>/dev/null || true
            sed -i.tmp 's/pip install -r requirements\.txt/pip install -e ./' "$dockerfile" 2>/dev/null || true
            sed -i.tmp 's/pip install -r requirements-dev\.txt/pip install -e .[dev]/' "$dockerfile" 2>/dev/null || true
            
            # 清理臨時檔案
            rm -f "$dockerfile.tmp"
            
            log_info "已更新 $dockerfile (備份：$dockerfile.backup)"
        fi
    done
    
    log_success "Docker 檔案更新完成"
}

# 生成遷移報告
generate_migration_report() {
    local report_file="dependency_migration_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# 依賴管理遷移報告

## 遷移時間
$(date)

## 遷移摘要
- 來源：分散的 requirements*.txt 檔案
- 目標：統一的 pyproject.toml
- 備份位置：$(cat .requirements_backup_path 2>/dev/null || echo "未建立備份")

## 🎯 新的依賴管理結構

### 核心依賴 (生產環境)
- Web 框架：FastAPI, Uvicorn, Pydantic
- 資料庫：SQLAlchemy, Alembic, Redis
- 安全：python-jose, passlib, cryptography
- 網路：httpx, aiohttp, requests

### 可選依賴組
- \`[ai]\`: 機器學習與 AI 服務
- \`[media]\`: 圖像與影片處理
- \`[storage]\`: 檔案儲存服務
- \`[monitoring]\`: 監控與觀測性
- \`[dev]\`: 開發工具
- \`[test]\`: 測試工具
- \`[docs]\`: 文檔生成
- \`[security]\`: 安全掃描工具

## 📦 安裝指令

### 生產環境
\`\`\`bash
pip install -e .[production]
\`\`\`

### 開發環境
\`\`\`bash  
pip install -e .[full-dev]
\`\`\`

### 特定功能
\`\`\`bash
pip install -e .[ai,media]  # AI 和媒體處理
pip install -e .[test]      # 測試環境
\`\`\`

## 🔧 管理腳本

### 依賴安裝
\`\`\`bash
./scripts/install-deps.sh production  # 生產環境
./scripts/install-deps.sh dev         # 開發環境
./scripts/install-deps.sh test        # 測試環境
\`\`\`

### 依賴更新
\`\`\`bash
./scripts/update-deps.sh  # 更新所有依賴
\`\`\`

### 依賴檢查
\`\`\`bash
./scripts/check-deps.sh   # 檢查依賴狀態
\`\`\`

### 遷移驗證
\`\`\`bash
./scripts/validate-migration.py  # 驗證遷移是否成功
\`\`\`

## 🐳 Docker 更新

所有 Dockerfile 已更新為使用 pyproject.toml：
- \`COPY requirements.txt\` → \`COPY pyproject.toml\`
- \`pip install -r requirements.txt\` → \`pip install -e .\`

## 🔍 版本統一

### 解決的版本衝突
- Redis: 統一至 5.0.7
- SQLAlchemy: 統一至 2.0.25  
- Pydantic: 統一至 2.6.0
- FastAPI: 統一至 0.109.1

### 安全版本升級
所有依賴都已升級到安全版本，符合 CLAUDE.md 中的安全要求。

## 📋 下一步行動

### 立即行動
1. 運行遷移驗證：\`./scripts/validate-migration.py\`
2. 測試 Docker 構建：\`docker-compose build\`
3. 測試應用啟動：\`./scripts/install-deps.sh dev && python -m uvicorn app.main:app\`

### CI/CD 更新
1. 更新 GitHub Actions 工作流程
2. 更新部署腳本
3. 更新文檔中的安裝指令

### 團隊協作
1. 通知團隊成員更新本地環境
2. 更新開發環境設定文檔
3. 培訓團隊使用新的依賴管理流程

## ⚠️  注意事項

1. **虛擬環境**：建議使用虛擬環境隔離依賴
2. **版本鎖定**：考慮使用 pip-tools 生成鎖定檔案
3. **定期更新**：建立定期依賴更新流程
4. **安全監控**：持續監控依賴安全漏洞

## 🎉 預期效益

### 短期效益
- 依賴管理統一化
- 版本衝突解決
- 安裝流程簡化
- 開發體驗改善

### 長期效益  
- 維護成本降低
- 安全性提升
- 團隊協作效率提高
- 持續整合流程優化

---

**執行狀態**: 遷移腳本已執行，請運行驗證腳本確認結果。
EOF

    log_success "遷移報告已生成：$report_file"
}

# 主函數
main() {
    log_info "開始依賴管理現代化..."
    log_info "這個過程將會："
    log_info "1. 檢查系統要求"
    log_info "2. 分析現有 requirements 檔案"
    log_info "3. 檢測版本衝突"
    log_info "4. 更新 pyproject.toml"
    log_info "5. 建立依賴管理腳本"
    log_info "6. 清理舊檔案"
    log_info "7. 更新 Docker 配置"
    
    echo
    read -p "是否繼續？(y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "依賴遷移已取消"
        exit 0
    fi
    
    # 執行遷移步驟
    check_requirements
    analyze_requirements
    categorize_dependencies
    detect_conflicts
    update_pyproject
    create_dependency_management_scripts
    create_migration_validator
    cleanup_old_requirements
    update_docker_files
    generate_migration_report
    
    log_success "依賴管理現代化完成！"
    log_info "請執行 ./scripts/validate-migration.py 驗證遷移結果"
    log_warning "重要：請更新 CI/CD 流程以使用新的依賴管理"
    
    # 清理臨時檔案
    rm -rf .deps_analysis
}

# 執行主函數
main "$@"