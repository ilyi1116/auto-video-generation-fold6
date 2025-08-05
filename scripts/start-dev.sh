#!/bin/bash

# Voice Cloning System - Development Startup Script
# 現代化微服務架構啟動腳本

set -euo pipefail

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# 檢查先決條件
check_prerequisites() {
    log_info "🔍 Checking prerequisites..."
    
    # 檢查 Docker
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    log_success "Docker is running"
    
    # 檢查 docker-compose
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "docker-compose is not installed. Please install docker-compose."
        exit 1
    fi
    log_success "docker-compose is available"
    
    # 檢查 Python
    if ! command -v python3 >/dev/null 2>&1; then
        log_warning "Python3 not found, some health checks may not work"
    fi
}

# 設置環境配置
setup_environment() {
    log_info "📄 Setting up environment configuration..."
    
    # 檢查並創建開發環境配置
    if [ ! -f .env ]; then
        if [ -f config/environments/development.env ]; then
            log_info "Creating .env from development.env..."
            cp config/environments/development.env .env
        elif [ -f .env.example ]; then
            log_info "Creating .env from .env.example..."
            cp .env.example .env
        else
            log_warning "No environment template found. Creating basic .env..."
            cat > .env << EOF
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_cloning
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=dev-secret-key-change-in-production
API_GATEWAY_PORT=8000
AUTH_SERVICE_PORT=8001
EOF
        fi
        log_success ".env file created. Please review and customize if needed."
    else
        log_success ".env file already exists"
    fi
}

# 安裝依賴
install_dependencies() {
    log_info "📦 Installing dependencies..."
    
    # Python 依賴
    if [ -f pyproject.toml ]; then
        log_info "Installing Python dependencies..."
        pip3 install -e . --quiet 2>/dev/null || log_warning "Failed to install Python dependencies"
    fi
    
    # 前端依賴
    if [ -d src/frontend ] && [ -f src/frontend/package.json ]; then
        log_info "Installing frontend dependencies..."
        cd src/frontend
        npm install --silent 2>/dev/null || log_warning "Failed to install frontend dependencies"
        cd ../..
    fi
    
    log_success "Dependencies installation completed"
}

# 啟動服務
start_services() {
    log_info "🚀 Starting Voice Cloning System Development Environment..."
    
    # 構建並啟動服務
    log_info "🔨 Building and starting services..."
    docker-compose up --build -d
    
    # 等待服務就緒
    log_info "⏳ Waiting for services to initialize..."
    sleep 15
}

# 執行健康檢查
health_check() {
    log_info "🔍 Performing health checks..."
    
    # 如果健康檢查腳本存在，使用它
    if [ -f scripts/check-service-health.py ]; then
        python3 scripts/check-service-health.py || log_warning "Health check script failed"
    else
        # 手動檢查核心服務
        services=("api-gateway:8000" "auth-service:8001" "data-service:8002" "inference-service:8003" "storage-service:8009")
        
        for service in "${services[@]}"; do
            IFS=':' read -r name port <<< "$service"
            if curl -f http://localhost:$port/health >/dev/null 2>&1; then
                log_success "$name is healthy"
            else
                log_warning "$name health check failed"
            fi
        done
        
        # 檢查基礎設施
        if docker-compose ps postgres | grep -q "Up"; then
            log_success "PostgreSQL is running"
        else
            log_warning "PostgreSQL might not be ready"
        fi
        
        if docker-compose ps redis | grep -q "Up"; then
            log_success "Redis is running"
        else
            log_warning "Redis might not be ready"
        fi
    fi
}

# 顯示系統資訊
show_system_info() {
    echo ""
    echo -e "${CYAN}🎉 Voice Cloning System Development Environment Ready!${NC}"
    echo ""
    echo -e "${CYAN}📊 Service URLs:${NC}"
    echo "   • 🌐 API Gateway:       http://localhost:8000"
    echo "   • 🔐 Auth Service:      http://localhost:8001"
    echo "   • 📊 Data Service:      http://localhost:8002"
    echo "   • 🤖 Inference Service: http://localhost:8003"
    echo "   • 🎥 Video Service:     http://localhost:8004"
    echo "   • 🧠 AI Service:        http://localhost:8005"
    echo "   • 📱 Social Service:    http://localhost:8006"
    echo "   • 📈 Trend Service:     http://localhost:8007"
    echo "   • ⏰ Scheduler Service: http://localhost:8008"
    echo "   • 💾 Storage Service:   http://localhost:8009"
    echo ""
    echo -e "${CYAN}📖 Documentation:${NC}"
    echo "   • 📚 API Docs:          http://localhost:8000/docs"
    echo "   • 🔍 Service Discovery: http://localhost:8000/services"
    echo ""
    echo -e "${CYAN}🔧 Infrastructure:${NC}"
    echo "   • 🐘 PostgreSQL:        localhost:5432"
    echo "   • 🔴 Redis:             localhost:6379"
    echo "   • 📊 Prometheus:        http://localhost:9090"
    echo "   • 📈 Grafana:           http://localhost:3000"
    echo ""
    echo -e "${CYAN}⚡ Quick Commands:${NC}"
    echo "   • View logs:           ${GREEN}make logs${NC} or ${GREEN}docker-compose logs -f${NC}"
    echo "   • Health check:        ${GREEN}make health${NC} or ${GREEN}python3 scripts/check-service-health.py${NC}"
    echo "   • Stop services:       ${GREEN}make dev-down${NC} or ${GREEN}docker-compose down${NC}"
    echo "   • Restart services:    ${GREEN}make dev-restart${NC} or ${GREEN}docker-compose restart${NC}"
    echo "   • Run tests:           ${GREEN}make test${NC}"
    echo "   • Format code:         ${GREEN}make format${NC}"
    echo "   • Clean up:            ${GREEN}make clean${NC}"
    echo ""
    echo -e "${CYAN}🚀 Next Steps:${NC}"
    echo "   1. Test the API:       ${GREEN}curl http://localhost:8000/health${NC}"
    echo "   2. View API docs:      ${GREEN}open http://localhost:8000/docs${NC}"
    echo "   3. Check service health: ${GREEN}make health${NC}"
    echo "   4. Run the test suite: ${GREEN}make test${NC}"
    echo ""
    echo -e "${CYAN}📝 For help:${NC} ${GREEN}make help${NC}"
    echo ""
}

# 主函數
main() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}🎵 Voice Cloning System - Development Environment Setup     ${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    
    check_prerequisites
    setup_environment
    install_dependencies
    start_services
    health_check
    show_system_info
    
    log_success "Development environment setup completed!"
}

# 執行主函數
main "$@"