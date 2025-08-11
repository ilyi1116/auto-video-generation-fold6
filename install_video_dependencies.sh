#!/bin/bash

# 高級視頻處理依賴安裝腳本
# 安裝所有必要的視頻處理庫和依賴

echo "🎬 Installing Advanced Video Processing Dependencies"
echo "=" * 60

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

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

# 檢查 Python 版本
log_info "Checking Python version..."
python3_version=$(python3 --version 2>&1)
if [[ $? -eq 0 ]]; then
    log_success "Python3 available: $python3_version"
else
    log_error "Python3 not found. Please install Python 3.8+ first."
    exit 1
fi

# 檢查 pip
log_info "Checking pip..."
if command -v pip3 &> /dev/null; then
    log_success "pip3 is available"
    pip_cmd="pip3"
elif command -v pip &> /dev/null; then
    log_success "pip is available"
    pip_cmd="pip"
else
    log_error "pip not found. Please install pip first."
    exit 1
fi

# 升級 pip
log_info "Upgrading pip..."
$pip_cmd install --upgrade pip

# 核心視頻處理依賴
log_info "Installing core video processing dependencies..."

core_packages=(
    "moviepy>=1.0.3"
    "pillow>=10.3.0"
    "numpy>=1.24.0"
    "opencv-python>=4.8.0"
)

for package in "${core_packages[@]}"; do
    log_info "Installing $package..."
    if $pip_cmd install "$package"; then
        log_success "✅ $package installed successfully"
    else
        log_error "❌ Failed to install $package"
    fi
done

# 高級音頻處理依賴
log_info "Installing advanced audio processing dependencies..."

audio_packages=(
    "librosa>=0.10.0"
    "soundfile>=0.12.0"
    "scipy>=1.10.0"
)

for package in "${audio_packages[@]}"; do
    log_info "Installing $package..."
    if $pip_cmd install "$package"; then
        log_success "✅ $package installed successfully"
    else
        log_warning "⚠️  Failed to install $package (optional for advanced features)"
    fi
done

# Web 服務依賴
log_info "Installing web service dependencies..."

web_packages=(
    "fastapi>=0.104.0"
    "uvicorn>=0.24.0"
    "aiofiles>=23.0.0"
    "python-multipart>=0.0.8"
)

for package in "${web_packages[@]}"; do
    log_info "Installing $package..."
    if $pip_cmd install "$package"; then
        log_success "✅ $package installed successfully"
    else
        log_error "❌ Failed to install $package"
    fi
done

# 可選的高性能依賴
log_info "Installing optional high-performance dependencies..."

optional_packages=(
    "numba"          # JIT compiler for numerical functions
    "imageio-ffmpeg" # FFmpeg support for MoviePy
    "psutil"         # System and process utilities
)

for package in "${optional_packages[@]}"; do
    log_info "Installing $package..."
    if $pip_cmd install "$package"; then
        log_success "✅ $package installed successfully"
    else
        log_warning "⚠️  Failed to install $package (optional)"
    fi
done

# 檢查系統依賴
log_info "Checking system dependencies..."

# 檢查 FFmpeg
if command -v ffmpeg &> /dev/null; then
    ffmpeg_version=$(ffmpeg -version | head -n1)
    log_success "FFmpeg available: $ffmpeg_version"
else
    log_warning "FFmpeg not found. Some video processing features may be limited."
    log_info "To install FFmpeg:"
    log_info "  macOS: brew install ffmpeg"
    log_info "  Ubuntu: sudo apt install ffmpeg"
    log_info "  CentOS: sudo yum install ffmpeg"
fi

# 檢查系統字體（用於文字渲染）
log_info "Checking system fonts..."

font_paths=(
    "/System/Library/Fonts/PingFang.ttc"     # macOS Chinese
    "/System/Library/Fonts/Helvetica.ttc"   # macOS English
    "/usr/share/fonts/truetype/dejavu/"      # Linux
    "/Windows/Fonts/"                        # Windows
)

found_fonts=0
for font_path in "${font_paths[@]}"; do
    if [[ -e "$font_path" ]]; then
        log_success "Found font path: $font_path"
        ((found_fonts++))
    fi
done

if [[ $found_fonts -eq 0 ]]; then
    log_warning "No system fonts found. Text rendering may use default fonts only."
fi

# 創建測試腳本
log_info "Creating dependency verification script..."

cat > verify_dependencies.py << 'EOF'
#!/usr/bin/env python3
"""
依賴驗證腳本
檢查所有已安裝的視頻處理依賴
"""

import sys
import importlib

def check_dependency(name, description):
    try:
        module = importlib.import_module(name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {description}: v{version}")
        return True
    except ImportError:
        print(f"❌ {description}: Not available")
        return False

def main():
    print("🔍 Verifying Video Processing Dependencies")
    print("=" * 50)
    
    dependencies = [
        ("moviepy", "MoviePy (Video Processing)"),
        ("PIL", "Pillow (Image Processing)"),
        ("numpy", "NumPy (Numerical Computing)"),
        ("cv2", "OpenCV (Computer Vision)"),
        ("librosa", "librosa (Audio Analysis)"),
        ("soundfile", "SoundFile (Audio I/O)"),
        ("scipy", "SciPy (Scientific Computing)"),
        ("fastapi", "FastAPI (Web Framework)"),
        ("uvicorn", "Uvicorn (ASGI Server)"),
        ("aiofiles", "aiofiles (Async File I/O)"),
    ]
    
    available_count = 0
    total_count = len(dependencies)
    
    for name, description in dependencies:
        if check_dependency(name, description):
            available_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Summary: {available_count}/{total_count} dependencies available")
    
    if available_count >= 6:  # Core dependencies
        print("✅ System ready for advanced video processing!")
        return 0
    else:
        print("⚠️  Missing critical dependencies. Please install them.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x verify_dependencies.py

# 運行依賴驗證
log_info "Verifying installed dependencies..."
python3 verify_dependencies.py

verification_result=$?

echo ""
echo "=" * 60
if [[ $verification_result -eq 0 ]]; then
    log_success "🎉 Advanced Video Processing Dependencies Installation Complete!"
    echo ""
    log_info "Next steps:"
    log_info "1. Run 'python3 verify_dependencies.py' to verify installation"
    log_info "2. Run 'python3 test_advanced_video_system.py' to test the system"
    log_info "3. Start the advanced video service with 'python3 src/services/video-service/advanced_video_service.py'"
else
    log_warning "⚠️  Installation completed with some missing dependencies."
    echo ""
    log_info "Some features may be limited. Check the verification output above."
fi

echo ""
log_info "Installation log and verification script saved in current directory."
log_info "For troubleshooting, check the specific error messages above."

# 創建啟動腳本
log_info "Creating convenience scripts..."

cat > start_advanced_video_service.sh << 'EOF'
#!/bin/bash
# 啟動高級視頻服務

echo "🚀 Starting Advanced Video Service..."

# 檢查依賴
if ! python3 verify_dependencies.py; then
    echo "❌ Dependencies check failed. Please run install_video_dependencies.sh first."
    exit 1
fi

# 啟動服務
cd src/services/video-service
python3 advanced_video_service.py
EOF

chmod +x start_advanced_video_service.sh

log_success "Created start_advanced_video_service.sh"
log_info "Use './start_advanced_video_service.sh' to start the advanced video service"