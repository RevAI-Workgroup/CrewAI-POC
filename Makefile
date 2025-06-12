.PHONY: help test test-fast test-unit test-integration test-coverage test-performance \
        build build-backend build-frontend build-dev build-prod \
        docker-test docker-test-up docker-test-down \
        clean clean-cache clean-docker \
        lint format check

# Default target
help: ## Show this help message
	@echo "CrewAI Test & Build Optimization Commands"
	@echo "========================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Test Commands
test: ## Run all tests (unit + integration)
	@echo "🧪 Running all tests..."
	cd backend && pytest
	cd frontend && bun run test:run

test-fast: ## Run fast unit tests only
	@echo "⚡ Running fast unit tests..."
	cd backend && chmod +x scripts/test-fast.sh && ./scripts/test-fast.sh
	cd frontend && chmod +x scripts/test-fast.sh && ./scripts/test-fast.sh

test-unit: ## Run unit tests with coverage
	@echo "🔬 Running unit tests..."
	cd backend && pytest -m "unit" --cov=. --cov-report=term-missing
	cd frontend && bun run test:run --coverage

test-integration: ## Run integration tests
	@echo "🔧 Running integration tests..."
	cd backend && chmod +x scripts/test-integration.sh && ./scripts/test-integration.sh

test-coverage: ## Run tests with full coverage report
	@echo "📊 Running tests with coverage..."
	cd backend && pytest --cov=. --cov-report=html --cov-report=xml
	cd frontend && bun run test:coverage

test-performance: ## Run performance tests
	@echo "🚀 Running performance tests..."
	cd backend && pytest -m "performance" --benchmark-only

test-changed: ## Run tests for changed files only
	@echo "🔍 Running tests for changed files..."
	cd backend && pytest --picked --mode=branch
	cd frontend && bun run test:run --changed

# Docker Test Commands
docker-test-up: ## Start test environment with Docker
	@echo "🐳 Starting test environment..."
	docker-compose -f docker/docker-compose.test.yml up -d
	@echo "⏳ Waiting for services to be ready..."
	sleep 10

docker-test-down: ## Stop test environment
	@echo "🛑 Stopping test environment..."
	docker-compose -f docker/docker-compose.test.yml down -v

docker-test: docker-test-up ## Run tests in Docker environment
	@echo "🐳 Running tests in Docker..."
	docker-compose -f docker/docker-compose.test.yml exec backend-test pytest
	docker-compose -f docker/docker-compose.test.yml exec frontend-test bun run test:run
	$(MAKE) docker-test-down

# Build Commands
build: build-backend build-frontend ## Build all Docker images

build-backend: ## Build backend Docker image
	@echo "🏗️  Building backend image..."
	docker build \
		--target production \
		--cache-from crewai-backend:latest \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		-t crewai-backend:latest \
		-t crewai-backend:$(shell git rev-parse --short HEAD) \
		backend/

build-frontend: ## Build frontend Docker image
	@echo "🏗️  Building frontend image..."
	docker build \
		--target production \
		--cache-from crewai-frontend:latest \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		-t crewai-frontend:latest \
		-t crewai-frontend:$(shell git rev-parse --short HEAD) \
		frontend/

build-dev: ## Build development Docker images
	@echo "🏗️  Building development images..."
	docker build --target development -t crewai-backend:dev backend/
	docker build --target development -t crewai-frontend:dev frontend/

build-prod: ## Build production Docker images with optimizations
	@echo "🏗️  Building production images..."
	DOCKER_BUILDKIT=1 docker build \
		--target production \
		--cache-from crewai-backend:latest \
		-t crewai-backend:prod \
		backend/
	DOCKER_BUILDKIT=1 docker build \
		--target production \
		--cache-from crewai-frontend:latest \
		-t crewai-frontend:prod \
		frontend/

# Smart build targets (build only if changed)
build-backend-if-changed: ## Build backend only if code changed
	@echo "🔍 Checking if backend needs rebuilding..."
	@if git diff --quiet HEAD~1 HEAD -- backend/; then \
		echo "⏭️  No backend changes detected, skipping build"; \
	else \
		echo "🏗️  Backend changes detected, building..."; \
		$(MAKE) build-backend; \
	fi

build-frontend-if-changed: ## Build frontend only if code changed
	@echo "🔍 Checking if frontend needs rebuilding..."
	@if git diff --quiet HEAD~1 HEAD -- frontend/; then \
		echo "⏭️  No frontend changes detected, skipping build"; \
	else \
		echo "🏗️  Frontend changes detected, building..."; \
		$(MAKE) build-frontend; \
	fi

# Code Quality Commands
lint: ## Run linting for all code
	@echo "🧹 Running linters..."
	cd backend && python -m flake8 . --max-line-length=100 --ignore=E203,W503
	cd frontend && bun run lint

format: ## Format all code
	@echo "✨ Formatting code..."
	cd backend && python -m black . && python -m isort .
	cd frontend && bun run format

check: lint test-fast ## Run quick checks (lint + fast tests)

# Cleanup Commands
clean: clean-cache clean-docker ## Clean all caches and temporary files

clean-cache: ## Clean test caches and temporary files
	@echo "🧹 Cleaning caches..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules/.vitest" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf backend/htmlcov/ backend/coverage.xml frontend/coverage/ 2>/dev/null || true

clean-docker: ## Clean Docker test resources
	@echo "🐳 Cleaning Docker test resources..."
	docker-compose -f docker/docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
	docker system prune -f --filter label=com.docker.compose.project=crewai-test

# Development Commands
dev-setup: ## Set up development environment
	@echo "🔧 Setting up development environment..."
	cd backend && pip install -r requirements.txt
	cd frontend && bun install

dev-test-watch: ## Run tests in watch mode for development
	@echo "👀 Starting test watchers..."
	cd backend && pytest-watch --runner "pytest -m unit --tb=short"
	cd frontend && bun run test &

# CI/CD Helper Commands
ci-test-fast: ## CI: Run fast tests suitable for PR checks
	@echo "🚀 CI: Running fast test suite..."
	$(MAKE) test-fast

ci-test-full: ## CI: Run full test suite for main branch
	@echo "🔬 CI: Running full test suite..."
	$(MAKE) test-coverage
	$(MAKE) test-integration

ci-build-and-test: ## CI: Build and test everything
	@echo "🏗️  CI: Building and testing..."
	$(MAKE) build-dev
	$(MAKE) docker-test

# Performance optimization check
perf-check: ## Check test performance and suggest optimizations
	@echo "📈 Analyzing test performance..."
	cd backend && pytest --durations=10 -m "not performance"
	cd frontend && bun run test:run --reporter=verbose | grep -E "(slow|ms)" 