#!/bin/bash
# MacBook Pro M4 環境設置腳本
# 自動配置 M4 架構的最佳化環境

set -e

echo "🚀 開始設置 MacBook Pro M4 開發環境..."

# 檢查是否在 M4 Mac 上運行
if [[ $(uname -m) != "arm64" ]]; then
    echo "❌ 警告：此腳本針對 ARM64 (M4) 架構優化"
    echo "當前架構：$(uname -m)"
    read -p "是否繼續？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 檢查並安裝 Homebrew
if ! command -v brew &> /dev/null; then
    echo "📦 安裝 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # 設置 PATH
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo "✅ Homebrew 已安裝"
fi

# 更新 Homebrew
echo "🔄 更新 Homebrew..."
brew update

# 安裝必要的工具
echo "📦 安裝必要的系統依賴..."
brew install --formula \
    postgresql@15 \
    redis \
    node@18 \
    python@3.11 \
    ffmpeg \
    imagemagick \
    docker \
    docker-compose \
    git \
    curl \
    jq \
    htop

# 檢查 Docker Desktop
if ! command -v docker &> /dev/null; then
    echo "❌ Docker Desktop 未安裝"
    echo "請從 https://docs.docker.com/desktop/install/mac-install/ 下載並安裝 Docker Desktop for Mac (Apple Silicon)"
    exit 1
else
    echo "✅ Docker Desktop 已安裝"
fi

# 設置環境變數
echo "🔧 配置環境變數..."
ENV_FILE="$HOME/.zshrc"

# 備份現有配置
if [[ -f "$ENV_FILE" ]]; then
    cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
fi

# 添加 M4 優化環境變數
cat >> "$ENV_FILE" << 'EOF'

# ===== MacBook Pro M4 優化配置 =====
# Homebrew 路徑
export PATH="/opt/homebrew/bin:$PATH"

# Docker M4 優化
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_DEFAULT_PLATFORM=linux/arm64

# Python 性能優化
export PYTHONOPTIMIZE=2
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
export OPENBLAS_NUM_THREADS=8

# Node.js 性能優化
export NODE_OPTIONS="--max-old-space-size=4096"
export UV_THREADPOOL_SIZE=8

# 開發工具優化
export FFMPEG_THREADS=8

# 記憶體優化
export MAX_MEMORY_USAGE_MB=8192
export CACHE_SIZE_MB=2048

EOF

echo "✅ 環境變數配置完成"

# 重新載入環境變數
source "$ENV_FILE"

# 安裝 Python 依賴
echo "🐍 安裝 Python 開發依賴..."
python3 -m pip install --upgrade pip
python3 -m pip install \
    bandit \
    pytest \
    pytest-cov \
    black \
    isort \
    flake8 \
    mypy

# 安裝 Node.js 全域套件
echo "📦 安裝 Node.js 全域套件..."
npm install -g \
    pnpm \
    @sveltejs/kit \
    vite \
    eslint \
    prettier

# 驗證 ARM64 版本
echo "🔍 驗證安裝的工具架構..."
echo "Python: $(file $(which python3) | grep -o 'arm64\|x86_64')"
echo "Node.js: $(file $(which node) | grep -o 'arm64\|x86_64')"
echo "Docker: $(docker version --format '{{.Client.Arch}}')"

# 檢查 Docker 配置
echo "🐳 檢查 Docker 配置..."
if docker info > /dev/null 2>&1; then
    echo "✅ Docker 運行正常"
    
    # 測試 ARM64 支援
    if docker run --rm --platform linux/arm64 alpine uname -m | grep -q arm64; then
        echo "✅ Docker ARM64 支援正常"
    else
        echo "❌ Docker ARM64 支援異常"
    fi
else
    echo "❌ Docker 未運行，請啟動 Docker Desktop"
fi

# 創建 M4 優化的 Docker Compose 覆蓋文件
echo "📝 創建本地 Docker Compose 覆蓋文件..."
cat > docker-compose.override.yml << 'EOF'
# 本地開發環境覆蓋配置 (M4 優化)
version: '3.8'

services:
  # 所有服務預設使用 ARM64 平台
  frontend:
    platform: linux/arm64
    environment:
      - NODE_OPTIONS=--max-old-space-size=4096
      - UV_THREADPOOL_SIZE=8
    
  api-gateway:
    platform: linux/arm64
    
  auth-service:
    platform: linux/arm64
    environment:
      - PYTHONOPTIMIZE=2
      - OMP_NUM_THREADS=8
    
  data-service:
    platform: linux/arm64
    environment:
      - PYTHONOPTIMIZE=2
      - OMP_NUM_THREADS=8
    
  video-service:
    platform: linux/arm64
    environment:
      - PYTHONOPTIMIZE=2
      - FFMPEG_THREADS=8
    
  ai-service:
    platform: linux/arm64
    environment:
      - PYTHONOPTIMIZE=2
      - OMP_NUM_THREADS=8
      - MKL_NUM_THREADS=8
    
  postgres:
    platform: linux/arm64
    
  redis:
    platform: linux/arm64
    
  minio:
    platform: linux/arm64

EOF

echo "✅ Docker Compose 覆蓋文件已創建"

# 設置專案環境變數
if [[ -f ".env.example" ]] && [[ ! -f ".env" ]]; then
    echo "📋 創建 .env 文件..."
    cp .env.example .env
    echo "請編輯 .env 文件並設置適當的值"
fi

# 測試環境設置
echo "🧪 測試環境設置..."

# 測試 Python
if python3 -c "import sys; print(f'Python {sys.version} on {sys.platform}')" > /dev/null 2>&1; then
    echo "✅ Python 環境正常"
else
    echo "❌ Python 環境異常"
fi

# 測試 Node.js
if node --version > /dev/null 2>&1; then
    echo "✅ Node.js 環境正常 ($(node --version))"
else
    echo "❌ Node.js 環境異常"
fi

# 測試 Docker
if docker --version > /dev/null 2>&1; then
    echo "✅ Docker 環境正常 ($(docker --version))"
else
    echo "❌ Docker 環境異常"
fi

echo ""
echo "🎉 MacBook Pro M4 環境設置完成！"
echo ""
echo "📋 後續步驟："
echo "1. 重新啟動終端或執行：source ~/.zshrc"
echo "2. 確保 Docker Desktop 正在運行"
echo "3. 編輯 .env 文件設置環境變數"
echo "4. 運行：docker-compose -f docker/docker-compose.m4.yml up --build"
echo ""
echo "📚 更多資訊請參考：docs/M4_OPTIMIZATION_GUIDE.md"
echo ""
echo "⚡ M4 特定的優化已啟用，享受更快的開發體驗！"