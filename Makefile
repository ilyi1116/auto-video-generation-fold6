# Voice Cloning System - Unified Development Makefile
# 統一開發指令，標準化開發流程

.PHONY: help dev test lint format security build deploy clean install setup-hooks validate status

# 預設目標
.DEFAULT_GOAL := help

# 顏色定義
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m
WHITE := \033[37m
RESET := \033[0m

# 專案變數
PROJECT_NAME := voice-cloning-system
PYTHON := python3
PIP := pip3
COMPOSE := docker-compose
FRONTEND_DIR := src/frontend
PYTHON_SRC := src

##@ 幫助
help: ## 顯示幫助訊息
	@echo "$(CYAN)Voice Cloning System - Development Commands$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(CYAN)<target>$(RESET)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ 開發環境
install: ## 安裝所有依賴
	@echo "$(BLUE)📦 Installing dependencies...$(RESET)"
	@$(PIP) install -e .
	@cd $(FRONTEND_DIR) && npm install
	@echo "$(GREEN)✅ Dependencies installed$(RESET)"

setup-hooks: ## 設置 pre-commit hooks
	@echo "$(BLUE)🔧 Setting up pre-commit hooks...$(RESET)"
	@$(PIP) install pre-commit
	@pre-commit install
	@pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✅ Pre-commit hooks installed$(RESET)"

dev: ## 啟動開發環境
	@echo "$(BLUE)🚀 Starting development environment...$(RESET)"
	@chmod +x scripts/start-dev.sh
	@./scripts/start-dev.sh

dev-up: ## 啟動開發服務 (Docker)
	@echo "$(BLUE)🐋 Starting services with Docker...$(RESET)"
	@$(COMPOSE) up -d
	@echo "$(GREEN)✅ Services started$(RESET)"

dev-down: ## 停止開發服務
	@echo "$(YELLOW)⏹️  Stopping services...$(RESET)"
	@$(COMPOSE) down
	@echo "$(GREEN)✅ Services stopped$(RESET)"

dev-restart: ## 重啟開發服務
	@echo "$(YELLOW)🔄 Restarting services...$(RESET)"
	@$(COMPOSE) restart
	@echo "$(GREEN)✅ Services restarted$(RESET)"

logs: ## 查看服務日誌
	@echo "$(BLUE)📋 Viewing service logs...$(RESET)"
	@$(COMPOSE) logs -f

status: ## 檢查服務狀態
	@echo "$(BLUE)📊 Checking service status...$(RESET)"
	@$(COMPOSE) ps
	@echo "\n$(BLUE)🔍 Health checks:$(RESET)"
	@curl -f http://localhost:8000/health 2>/dev/null && echo "$(GREEN)✅ API Gateway$(RESET)" || echo "$(RED)❌ API Gateway$(RESET)"
	@curl -f http://localhost:8001/health 2>/dev/null && echo "$(GREEN)✅ Auth Service$(RESET)" || echo "$(RED)❌ Auth Service$(RESET)"

##@ 測試
test: ## 運行所有測試
	@echo "$(BLUE)🧪 Running all tests...$(RESET)"
	@$(PYTHON) -m pytest tests/ --cov=$(PYTHON_SRC) --cov-report=term-missing --cov-report=html
	@cd $(FRONTEND_DIR) && npm run test
	@echo "$(GREEN)✅ All tests completed$(RESET)"

test-python: ## 運行 Python 測試
	@echo "$(BLUE)🐍 Running Python tests...$(RESET)"
	@$(PYTHON) -m pytest tests/ --cov=$(PYTHON_SRC) --cov-report=term-missing
	@echo "$(GREEN)✅ Python tests completed$(RESET)"

test-frontend: ## 運行前端測試
	@echo "$(BLUE)🌐 Running frontend tests...$(RESET)"
	@cd $(FRONTEND_DIR) && npm run test
	@echo "$(GREEN)✅ Frontend tests completed$(RESET)"

test-coverage: ## 生成測試覆蓋率報告
	@echo "$(BLUE)📊 Generating coverage report...$(RESET)"
	@$(PYTHON) -m pytest tests/ --cov=$(PYTHON_SRC) --cov-report=html --cov-report=term
	@cd $(FRONTEND_DIR) && npm run test:coverage
	@echo "$(GREEN)✅ Coverage reports generated$(RESET)"
	@echo "$(CYAN)📁 Python coverage: htmlcov/index.html$(RESET)"
	@echo "$(CYAN)📁 Frontend coverage: $(FRONTEND_DIR)/coverage/index.html$(RESET)"

test-services: ## 測試個別微服務
	@echo "$(BLUE)🔬 Testing individual services...$(RESET)"
	@for service in src/services/*/; do \
		if [ -d "$$service/tests" ]; then \
			echo "$(YELLOW)Testing $$service$(RESET)"; \
			$(PYTHON) -m pytest "$$service/tests" --cov="$$service" --cov-report=term-missing; \
		fi; \
	done
	@echo "$(GREEN)✅ Service tests completed$(RESET)"

##@ 程式碼品質
lint: ## 運行所有 linting 檢查
	@echo "$(BLUE)🔍 Running linting checks...$(RESET)"
	@$(PYTHON) -m flake8 $(PYTHON_SRC)
	@$(PYTHON) -m mypy $(PYTHON_SRC) --ignore-missing-imports
	@cd $(FRONTEND_DIR) && npm run lint
	@echo "$(GREEN)✅ Linting completed$(RESET)"

format: ## 格式化程式碼
	@echo "$(BLUE)✨ Formatting code...$(RESET)"
	@$(PYTHON) -m black $(PYTHON_SRC) --line-length=100
	@$(PYTHON) -m isort $(PYTHON_SRC) --profile black --line-length=100
	@cd $(FRONTEND_DIR) && npm run format
	@echo "$(GREEN)✅ Code formatted$(RESET)"

format-check: ## 檢查程式碼格式
	@echo "$(BLUE)📏 Checking code format...$(RESET)"
	@$(PYTHON) -m black $(PYTHON_SRC) --check --line-length=100
	@$(PYTHON) -m isort $(PYTHON_SRC) --check --profile black --line-length=100
	@cd $(FRONTEND_DIR) && npm run format:check
	@echo "$(GREEN)✅ Format check completed$(RESET)"

quality: ## 運行程式碼品質檢查
	@echo "$(BLUE)🎯 Running code quality checks...$(RESET)"
	@$(PYTHON) -m radon cc $(PYTHON_SRC) --min B --show-complexity
	@$(PYTHON) -m vulture $(PYTHON_SRC) --min-confidence 80
	@echo "$(GREEN)✅ Quality checks completed$(RESET)"

##@ 安全性
security: ## 運行安全性掃描
	@echo "$(BLUE)🛡️  Running security scans...$(RESET)"
	@$(PYTHON) -m bandit -r $(PYTHON_SRC) -f json -o bandit-report.json
	@$(PYTHON) -m safety check --json --output safety-report.json || echo "$(YELLOW)⚠️  Security warnings found$(RESET)"
	@cd $(FRONTEND_DIR) && npm audit --audit-level=moderate || echo "$(YELLOW)⚠️  NPM audit warnings found$(RESET)"
	@echo "$(GREEN)✅ Security scans completed$(RESET)"

audit: ## 執行完整安全審計
	@echo "$(BLUE)🔒 Running comprehensive security audit...$(RESET)"
	@$(MAKE) security
	@echo "$(CYAN)📊 Security reports:$(RESET)"
	@echo "$(CYAN)📁 Python: bandit-report.json, safety-report.json$(RESET)"
	@echo "$(GREEN)✅ Security audit completed$(RESET)"

##@ 建置與部署
build: ## 建置 Docker 映像
	@echo "$(BLUE)🔨 Building Docker images...$(RESET)"
	@$(COMPOSE) build
	@echo "$(GREEN)✅ Build completed$(RESET)"

build-prod: ## 建置生產環境映像
	@echo "$(BLUE)🏭 Building production images...$(RESET)"
	@$(COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml build
	@echo "$(GREEN)✅ Production build completed$(RESET)"

deploy-dev: ## 部署到開發環境
	@echo "$(BLUE)🚀 Deploying to development...$(RESET)"
	@$(COMPOSE) up -d --build
	@echo "$(GREEN)✅ Development deployment completed$(RESET)"

deploy-prod: ## 部署到生產環境
	@echo "$(BLUE)🏭 Deploying to production...$(RESET)"
	@chmod +x scripts/deploy-production.sh
	@./scripts/deploy-production.sh
	@echo "$(GREEN)✅ Production deployment completed$(RESET)"

##@ 驗證
validate: ## 驗證專案配置
	@echo "$(BLUE)✅ Validating project configuration...$(RESET)"
	@$(PYTHON) scripts/validate-configs.py || echo "$(YELLOW)⚠️  Configuration warnings found$(RESET)"
	@for file in docker-compose*.yml; do \
		echo "Validating $$file..."; \
		$(COMPOSE) -f "$$file" config > /dev/null; \
	done
	@echo "$(GREEN)✅ Validation completed$(RESET)"

validate-openapi: ## 驗證 OpenAPI 規範
	@echo "$(BLUE)📖 Validating OpenAPI schemas...$(RESET)"
	@$(PYTHON) scripts/validate-openapi-schemas.py || echo "$(YELLOW)⚠️  OpenAPI warnings found$(RESET)"
	@echo "$(GREEN)✅ OpenAPI validation completed$(RESET)"

##@ 清理
clean: ## 清理建置快取和暫存檔案
	@echo "$(BLUE)🧹 Cleaning up...$(RESET)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .coverage htmlcov/ .pytest_cache/
	@rm -rf bandit-report.json safety-report.json
	@cd $(FRONTEND_DIR) && rm -rf node_modules/.cache coverage/
	@echo "$(GREEN)✅ Cleanup completed$(RESET)"

clean-docker: ## 清理 Docker 資源
	@echo "$(BLUE)🐋 Cleaning Docker resources...$(RESET)"
	@$(COMPOSE) down -v --remove-orphans
	@docker system prune -f
	@docker volume prune -f
	@echo "$(GREEN)✅ Docker cleanup completed$(RESET)"

clean-all: clean clean-docker ## 清理所有快取和資源
	@echo "$(GREEN)✅ Complete cleanup finished$(RESET)"

##@ 實用工具
shell: ## 開啟 API Gateway 容器 shell
	@echo "$(BLUE)🐚 Opening API Gateway shell...$(RESET)"
	@$(COMPOSE) exec api-gateway bash

shell-db: ## 開啟資料庫 shell
	@echo "$(BLUE)🗄️  Opening database shell...$(RESET)"
	@$(COMPOSE) exec postgres psql -U postgres -d voice_cloning

backup-db: ## 備份資料庫
	@echo "$(BLUE)💾 Backing up database...$(RESET)"
	@mkdir -p backups
	@$(COMPOSE) exec postgres pg_dump -U postgres voice_cloning > backups/db_backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Database backup completed$(RESET)"

migrate: ## 執行資料庫遷移
	@echo "$(BLUE)📊 Running database migrations...$(RESET)"
	@$(COMPOSE) exec api-gateway alembic upgrade head
	@echo "$(GREEN)✅ Database migrations completed$(RESET)"

reset-db: ## 重置資料庫
	@echo "$(YELLOW)⚠️  Resetting database...$(RESET)"
	@$(COMPOSE) down
	@docker volume rm $$(docker volume ls -q | grep postgres) || true
	@$(COMPOSE) up -d postgres
	@sleep 5
	@$(MAKE) migrate
	@echo "$(GREEN)✅ Database reset completed$(RESET)"

##@ 監控
monitor: ## 開啟監控儀表板
	@echo "$(BLUE)📊 Opening monitoring dashboards...$(RESET)"
	@echo "$(CYAN)🔗 Prometheus: http://localhost:9090$(RESET)"
	@echo "$(CYAN)🔗 Grafana: http://localhost:3000$(RESET)"
	@echo "$(CYAN)🔗 API Docs: http://localhost:8000/docs$(RESET)"

health: ## 檢查所有服務健康狀態
	@echo "$(BLUE)🏥 Checking service health...$(RESET)"
	@$(PYTHON) scripts/check-service-health.py
	@echo "$(GREEN)✅ Health check completed$(RESET)"

##@ 開發輔助
docs: ## 生成專案文檔
	@echo "$(BLUE)📚 Generating documentation...$(RESET)"
	@$(PYTHON) scripts/generate-service-docs.py
	@echo "$(GREEN)✅ Documentation generated$(RESET)"

update-deps: ## 更新依賴版本
	@echo "$(BLUE)⬆️  Updating dependencies...$(RESET)"
	@$(PIP) install --upgrade pip
	@$(PIP) install pip-tools
	@pip-compile --upgrade pyproject.toml
	@cd $(FRONTEND_DIR) && npm update
	@echo "$(GREEN)✅ Dependencies updated$(RESET)"

pre-commit: ## 手動執行 pre-commit 檢查
	@echo "$(BLUE)🔍 Running pre-commit checks...$(RESET)"
	@pre-commit run --all-files
	@echo "$(GREEN)✅ Pre-commit checks completed$(RESET)"

##@ CI/CD
ci-setup: install setup-hooks ## 設置 CI 環境
	@echo "$(GREEN)✅ CI environment setup completed$(RESET)"

ci-test: lint security test ## 執行 CI 測試套件
	@echo "$(GREEN)✅ CI test suite completed$(RESET)"

ci-build: validate build ## 執行 CI 建置流程
	@echo "$(GREEN)✅ CI build process completed$(RESET)"

##@ 資訊
info: ## 顯示專案資訊
	@echo "$(CYAN)=== Voice Cloning System Information ===$(RESET)"
	@echo "$(YELLOW)Project:$(RESET) $(PROJECT_NAME)"
	@echo "$(YELLOW)Python:$(RESET) $(shell $(PYTHON) --version)"
	@echo "$(YELLOW)Node.js:$(RESET) $(shell node --version 2>/dev/null || echo 'Not installed')"
	@echo "$(YELLOW)Docker:$(RESET) $(shell docker --version 2>/dev/null || echo 'Not installed')"
	@echo "$(YELLOW)Docker Compose:$(RESET) $(shell $(COMPOSE) --version 2>/dev/null || echo 'Not installed')"
	@echo "$(CYAN)===============================================$(RESET)"

env: ## 顯示環境變數
	@echo "$(CYAN)=== Environment Variables ===$(RESET)"
	@echo "$(YELLOW)ENVIRONMENT:$(RESET) $(shell echo $$ENVIRONMENT || echo 'development')"
	@echo "$(YELLOW)DATABASE_URL:$(RESET) $(shell echo $$DATABASE_URL || echo 'Not set')"
	@echo "$(YELLOW)REDIS_URL:$(RESET) $(shell echo $$REDIS_URL || echo 'Not set')"
	@echo "$(CYAN)==============================$(RESET)"