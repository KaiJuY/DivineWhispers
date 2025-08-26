# Divine Whispers Backend - UV-based Development Commands

.PHONY: help install install-dev update clean test lint format docker-build docker-up docker-down migrate

help: ## Show this help message
	@echo "Divine Whispers Backend - UV Commands"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies with uv
	uv pip install --system -r requirements.txt

install-dev: ## Install all dependencies including dev dependencies with uv
	uv pip install --system -r requirements.txt
	uv pip install --system -e ".[dev]"

update: ## Update dependencies to latest compatible versions
	uv pip compile pyproject.toml -o requirements.txt
	uv pip install --system -r requirements.txt

clean: ## Clean up build artifacts and cache
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/

test: ## Run tests with pytest
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=app --cov-report=html --cov-report=term

lint: ## Run linting with flake8
	flake8 app/ tests/
	mypy app/

format: ## Format code with black and isort
	black app/ tests/
	isort app/ tests/

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start development environment with Docker
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

docker-up-prod: ## Start production environment with Docker
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

migrate: ## Run database migrations
	docker-compose exec app python -m alembic upgrade head

migrate-local: ## Run database migrations locally
	python -m alembic upgrade head

create-migration: ## Create new database migration
	@read -p "Enter migration message: " msg; \
	python -m alembic revision --autogenerate -m "$$msg"

dev-server: ## Start development server locally
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# UV-specific commands
uv-sync: ## Sync dependencies with uv
	uv pip sync requirements.txt

uv-lock: ## Generate lock file with uv
	uv pip freeze > requirements-lock.txt

uv-audit: ## Check for security vulnerabilities
	uv pip check