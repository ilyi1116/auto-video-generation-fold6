# ====================================================================
# Auto Video 系統開發工作流程自動化 Makefile
# ====================================================================

.PHONY: help install build test deploy clean dev prod

# 預設目標
.DEFAULT_GOAL := help

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Project variables
PROJECT_NAME := auto-video
VERSION := 1.0.0
DOCKER_REGISTRY := auto-video
NAMESPACE := auto-video

help: ## 📖 顯示所有可用的命令
	@echo "$(GREEN)Auto Video System - Available Commands$(NC)"
	@echo "======================================"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""

# ================================
# Development Environment
# ================================

install: ## 📦 安裝所有依賴
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "Installing development dependencies..."
	find services -name requirements-dev.txt -exec pip install -r {} \;
	@echo "$(GREEN)✅ Dependencies installed successfully$(NC)"

setup: ## 🔧 初始化開發環境
	@echo "$(GREEN)Setting up development environment...$(NC)"
	@cp .env.example .env
	@echo "Generating SSL certificates..."
	@./security/ssl/generate-certs.sh
	@echo "Setting up pre-commit hooks..."
	@pre-commit install
	@echo "$(GREEN)✅ Development environment ready$(NC)"

# ================================
# Code Quality
# ================================

lint: ## 🔍 執行程式碼檢查
	@echo "$(GREEN)Running linters...$(NC)"
	@echo "Linting Python code..."
	@ruff check services/
	@flake8 services/
	@mypy services/
	@echo "Linting frontend code..."
	@cd frontend && npm run lint
	@echo "$(GREEN)✅ All linting checks passed$(NC)"

format: ## 🎨 格式化程式碼
	@echo "$(GREEN)Formatting code...$(NC)"
	@echo "Formatting Python code..."
	@black services/
	@isort services/
	@ruff --fix services/
	@echo "Formatting frontend code..."
	@cd frontend && npm run format
	@echo "$(GREEN)✅ Code formatted successfully$(NC)"

# ================================
# Testing
# ================================

test: ## 🧪 執行所有測試
	@echo "$(GREEN)Running tests...$(NC)"
	@echo "Running Python tests..."
	@pytest services/ --cov=. --cov-report=html --cov-report=term
	@echo "Running frontend tests..."
	@cd frontend && npm test
	@echo "$(GREEN)✅ All tests passed$(NC)"

test-unit: ## 🔬 執行單元測試
	@echo "$(GREEN)Running unit tests...$(NC)"
	@pytest services/ -m "not integration"
	@cd frontend && npm run test:unit

test-integration: ## 🔗 執行整合測試
	@echo "$(GREEN)Running integration tests...$(NC)"
	@pytest services/ -m integration
	@cd frontend && npm run test:integration

test-e2e: ## 🎭 執行端對端測試
	@echo "$(GREEN)Running E2E tests...$(NC)"
	@cd frontend && npm run test:e2e

coverage: ## 📊 生成測試覆蓋率報告
	@echo "$(GREEN)Generating coverage report...$(NC)"
	@pytest services/ --cov=. --cov-report=html
	@cd frontend && npm run test:coverage
	@echo "$(GREEN)📊 Coverage report generated$(NC)"

# ================================
# Docker Operations
# ================================

docker-build: ## 🐳 構建所有 Docker 映像
	@echo "$(GREEN)Building Docker images...$(NC)"
	@docker-compose build
	@echo "$(GREEN)✅ Docker images built successfully$(NC)"

docker-build-prod: ## 🚀 構建生產環境 Docker 映像
	@echo "$(GREEN)Building production Docker images...$(NC)"
	@docker-compose -f docker-compose.prod.yml build
	@echo "$(GREEN)✅ Production images built successfully$(NC)"

docker-up: ## ⬆️ 啟動開發環境
	@echo "$(GREEN)Starting development environment...$(NC)"
	@docker-compose -f docker-compose.dev.yml up -d
	@echo "$(GREEN)✅ Development environment started$(NC)"
	@echo "Frontend: http://localhost:3000"
	@echo "API: http://localhost:8000"
	@echo "Grafana: http://localhost:3001"

docker-up-prod: ## 🌟 啟動生產環境
	@echo "$(GREEN)Starting production environment...$(NC)"
	@docker-compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)✅ Production environment started$(NC)"

docker-down: ## ⬇️ 停止 Docker 環境
	@echo "$(YELLOW)Stopping Docker environment...$(NC)"
	@docker-compose down
	@docker-compose -f docker-compose.dev.yml down
	@docker-compose -f docker-compose.prod.yml down
	@echo "$(GREEN)✅ Docker environment stopped$(NC)"

docker-logs: ## 📋 查看 Docker 日誌
	@docker-compose logs -f

docker-clean: ## 🧹 清理 Docker 資源
	@echo "$(YELLOW)Cleaning Docker resources...$(NC)"
	@docker system prune -f
	@docker volume prune -f
	@echo "$(GREEN)✅ Docker resources cleaned$(NC)"

# ================================
# Monitoring
# ================================

monitoring-up: ## 📊 啟動監控系統
	@echo "$(GREEN)Starting monitoring system...$(NC)"
	@./scripts/start-monitoring.sh
	@echo "$(GREEN)✅ Monitoring system started$(NC)"

monitoring-down: ## 📉 停止監控系統
	@echo "$(YELLOW)Stopping monitoring system...$(NC)"
	@./scripts/stop-monitoring.sh
	@echo "$(GREEN)✅ Monitoring system stopped$(NC)"

# ================================
# Database Operations
# ================================

db-migrate: ## 🗃️ 執行資料庫遷移
	@echo "$(GREEN)Running database migrations...$(NC)"
	@docker-compose exec api-gateway alembic upgrade head
	@echo "$(GREEN)✅ Database migrations completed$(NC)"

db-reset: ## 🔄 重置資料庫
	@echo "$(YELLOW)Resetting database...$(NC)"
	@docker-compose down
	@docker volume rm auto_generate_video_fold6_postgres_data
	@docker-compose up -d postgres
	@sleep 10
	@make db-migrate
	@echo "$(GREEN)✅ Database reset completed$(NC)"

db-backup: ## 💾 備份資料庫
	@echo "$(GREEN)Creating database backup...$(NC)"
	@./scripts/backup-system.sh
	@echo "$(GREEN)✅ Database backup completed$(NC)"

db-restore: ## 🔄 還原資料庫
	@echo "$(GREEN)Restoring database from backup...$(NC)"
	@if [ -z "$(BACKUP_ID)" ]; then \
		echo "$(RED)❌ Please specify BACKUP_ID: make db-restore BACKUP_ID=20250126_120000$(NC)"; \
		exit 1; \
	fi
	@./scripts/restore-system.sh $(BACKUP_ID)
	@echo "$(GREEN)✅ Database restored successfully$(NC)"

# ================================
# Kubernetes Deployment
# ================================

k8s-apply: ## ☸️ 部署到 Kubernetes
	@echo "$(GREEN)Deploying to Kubernetes...$(NC)"
	@kubectl apply -f k8s/namespace.yaml
	@kubectl apply -f k8s/configmap.yaml
	@kubectl apply -f k8s/secrets.yaml
	@kubectl apply -f k8s/deployments.yaml
	@kubectl apply -f k8s/services.yaml
	@kubectl apply -f k8s/ingress.yaml
	@kubectl apply -f k8s/hpa.yaml
	@echo "$(GREEN)✅ Deployed to Kubernetes$(NC)"

k8s-delete: ## 🗑️ 從 Kubernetes 刪除
	@echo "$(YELLOW)Deleting from Kubernetes...$(NC)"
	@kubectl delete -f k8s/ --ignore-not-found=true
	@echo "$(GREEN)✅ Deleted from Kubernetes$(NC)"

k8s-status: ## 📋 查看 Kubernetes 狀態
	@echo "$(GREEN)Kubernetes Status:$(NC)"
	@kubectl get pods -n $(NAMESPACE)
	@kubectl get services -n $(NAMESPACE)
	@kubectl get ingress -n $(NAMESPACE)

k8s-logs: ## 📖 查看 Kubernetes 日誌
	@kubectl logs -f deployment/api-gateway -n $(NAMESPACE)

# ================================
# Performance & Security
# ================================

benchmark: ## ⚡ 執行效能基準測試
	@echo "$(GREEN)Running performance benchmarks...$(NC)"
	@python performance/benchmarking/performance-tests.py
	@echo "$(GREEN)✅ Benchmarks completed$(NC)"

security-scan: ## 🔒 執行安全掃描
	@echo "$(GREEN)Running security scans...$(NC)"
	@echo "Scanning Python code..."
	@bandit -r services/ -f json -o bandit-report.json
	@echo "Scanning Python dependencies..."
	@safety check
	@echo "Scanning frontend dependencies..."
	@cd frontend && npm audit --audit-level=high
	@echo "Scanning Docker images..."
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image $(DOCKER_REGISTRY)/api-gateway:latest
	@echo "$(GREEN)✅ Security scans completed$(NC)"

# ================================
# Release Management
# ================================

build: ## 🏗️ 構建所有組件
	@echo "$(GREEN)Building all components...$(NC)"
	@make docker-build
	@cd frontend && npm run build
	@echo "$(GREEN)✅ Build completed$(NC)"

release: ## 🚀 創建發布版本
	@echo "$(GREEN)Creating release $(VERSION)...$(NC)"
	@make lint
	@make test
	@make build
	@git tag -a v$(VERSION) -m "Release version $(VERSION)"
	@echo "$(GREEN)✅ Release $(VERSION) created$(NC)"

deploy-staging: ## 🎭 部署到測試環境
	@echo "$(GREEN)Deploying to staging...$(NC)"
	@docker-compose -f docker-compose.staging.yml up -d
	@echo "$(GREEN)✅ Deployed to staging$(NC)"

deploy-production: ## 🌟 部署到生產環境
	@echo "$(GREEN)Deploying to production...$(NC)"
	@make k8s-apply
	@echo "$(GREEN)✅ Deployed to production$(NC)"

# ================================
# Utilities
# ================================

clean: ## 🧹 清理所有生成檔案
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@rm -rf .coverage htmlcov/ .pytest_cache/
	@cd frontend && npm run clean
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

health-check: ## 🏥 執行系統健康檢查
	@echo "$(GREEN)Running health checks...$(NC)"
	@./scripts/health-check.sh
	@echo "$(GREEN)✅ Health checks completed$(NC)"

logs: ## 📋 查看系統日誌
	@echo "$(GREEN)Displaying system logs...$(NC)"
	@docker-compose logs -f --tail=100

shell: ## 🐚 進入開發容器 Shell
	@docker-compose exec api-gateway /bin/bash

# ================================
# Documentation
# ================================

docs: ## 📚 生成文檔
	@echo "$(GREEN)Generating documentation...$(NC)"
	@cd frontend && npm run build-storybook
	@swagger-codegen generate -i docs/api/openapi.yaml -l html2 -o docs/api/html/
	@echo "$(GREEN)✅ Documentation generated$(NC)"

docs-serve: ## 🌐 啟動文檔服務器
	@echo "$(GREEN)Starting documentation server...$(NC)"
	@cd docs && python -m http.server 8080

# ================================
# Development Helpers
# ================================

install-tools: ## 🛠️ 安裝開發工具
	@echo "$(GREEN)Installing development tools...$(NC)"
	@pip install black isort flake8 pytest safety
	@npm install -g @commitlint/cli @commitlint/config-conventional
	@echo "$(GREEN)✅ Development tools installed$(NC)"

update-deps: ## 📦 更新依賴包
	@echo "$(GREEN)Updating dependencies...$(NC)"
	@cd frontend && npm update
	@pip-review --local --auto
	@echo "$(GREEN)✅ Dependencies updated$(NC)"

git-hooks: ## 🪝 安裝 Git hooks
	@echo "$(GREEN)Installing Git hooks...$(NC)"
	@pre-commit install
	@echo "$(GREEN)✅ Git hooks installed$(NC)"

# ================================
# Environment Management
# ================================

env-check: ## ✅ 檢查環境設定
	@echo "$(GREEN)Checking environment...$(NC)"
	@echo "Docker version: $$(docker --version)"
	@echo "Docker Compose version: $$(docker-compose --version)"
	@echo "Node.js version: $$(node --version)"
	@echo "Python version: $$(python --version)"
	@echo "$(GREEN)✅ Environment check completed$(NC)"

env-copy: ## 📋 複製環境設定檔案
	@if [ ! -f .env ]; then \
		echo "$(GREEN)Copying .env.example to .env...$(NC)"; \
		cp .env.example .env; \
		echo "$(YELLOW)⚠️  Please edit .env with your configuration$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi

# Help with colored output
info: ## ℹ️ 顯示專案資訊
	@echo "$(GREEN)Auto Video System$(NC)"
	@echo "版本: $(VERSION)"
	@echo "專案名稱: $(PROJECT_NAME)"
	@echo "命名空間: $(NAMESPACE)"
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  1. make setup"
	@echo "  2. make docker-up"
	@echo "  3. make health-check"
	@echo ""
	@echo "$(YELLOW)Useful Commands:$(NC)"
	@echo "  make test          # 執行測試"
	@echo "  make lint          # 程式碼檢查"
	@echo "  make docker-logs   # 查看日誌"
	@echo "  make monitoring-up # 啟動監控"