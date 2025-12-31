# =============================================================================
# SCORPION Makefile
# =============================================================================
# Development commands for the SCORPION automation platform
# Usage: make <target>
# =============================================================================

.PHONY: help install test run clean docker-up docker-down backup restore \
        lint format check health logs shell db-shell redis-shell \
        pull-models dev prod

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker compose -f body/docker/docker-compose.yml
PROJECT_NAME := scorpion

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo ""
	@echo "$(BLUE)SCORPION v1.0.0 - TESTUDO Formation$(NC)"
	@echo "======================================"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# Installation
# =============================================================================

install: ## Install Python dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(PIP) install -r body/docker/requirements.txt
	@echo "$(GREEN)Dependencies installed!$(NC)"

install-dev: install ## Install development dependencies
	@echo "$(BLUE)Installing dev dependencies...$(NC)"
	$(PIP) install pytest pytest-cov black isort flake8 mypy
	@echo "$(GREEN)Dev dependencies installed!$(NC)"

setup: ## Complete project setup
	@echo "$(BLUE)Setting up SCORPION...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(YELLOW)Created .env from template - please configure it$(NC)"; \
	fi
	@mkdir -p data logs backups
	@make install
	@echo "$(GREEN)Setup complete!$(NC)"

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	$(PYTHON) -m pytest tests/ -v
	@echo "$(GREEN)Tests complete!$(NC)"

test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTHON) -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

test-imports: ## Run import tests only
	@echo "$(BLUE)Running import tests...$(NC)"
	$(PYTHON) -m pytest tests/test_imports.py -v

# =============================================================================
# Running
# =============================================================================

run: ## Start the API server
	@echo "$(BLUE)Starting SCORPION API...$(NC)"
	$(PYTHON) -m uvicorn mouth.api:app --reload --host 0.0.0.0 --port 8080

run-cli: ## Run CLI in interactive mode
	@echo "$(BLUE)Starting SCORPION CLI...$(NC)"
	$(PYTHON) -m integration.cli

run-scheduler: ## Start JARVIS scheduler
	@echo "$(BLUE)Starting JARVIS scheduler...$(NC)"
	$(PYTHON) -m integration.scheduler

status: ## Check system status
	@$(PYTHON) -m integration.cli status

health: ## Run health check
	@$(PYTHON) -m monitoring.health_check

# =============================================================================
# Docker
# =============================================================================

docker-up: ## Start all Docker services
	@echo "$(BLUE)Starting Docker services...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Services started!$(NC)"
	@make docker-status

docker-down: ## Stop all Docker services
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)Services stopped!$(NC)"

docker-restart: docker-down docker-up ## Restart Docker services

docker-status: ## Show Docker service status
	@echo "$(BLUE)Docker service status:$(NC)"
	$(DOCKER_COMPOSE) ps

docker-logs: ## Show Docker logs
	$(DOCKER_COMPOSE) logs -f

docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)Build complete!$(NC)"

docker-clean: ## Remove Docker containers and volumes
	@echo "$(RED)Removing Docker containers and volumes...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans
	@echo "$(GREEN)Cleanup complete!$(NC)"

# =============================================================================
# Database
# =============================================================================

db-shell: ## Open PostgreSQL shell
	$(DOCKER_COMPOSE) exec postgres psql -U scorpion -d scorpion

redis-shell: ## Open Redis CLI
	$(DOCKER_COMPOSE) exec redis redis-cli

db-migrate: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	@echo "$(YELLOW)Migrations not yet implemented$(NC)"

# =============================================================================
# AI Models
# =============================================================================

pull-models: ## Pull all Ollama models
	@echo "$(BLUE)Pulling AI models...$(NC)"
	ollama pull mistral
	ollama pull phi
	ollama pull codellama
	ollama pull llama2
	@echo "$(GREEN)Models pulled!$(NC)"

list-models: ## List available Ollama models
	ollama list

# =============================================================================
# Backup & Restore
# =============================================================================

backup: ## Create full backup
	@echo "$(BLUE)Creating backup...$(NC)"
	@bash scripts/backup.sh backup
	@echo "$(GREEN)Backup complete!$(NC)"

restore: ## Restore from latest backup
	@echo "$(YELLOW)Restoring from latest backup...$(NC)"
	@bash scripts/backup.sh restore
	@echo "$(GREEN)Restore complete!$(NC)"

backup-list: ## List available backups
	@bash scripts/backup.sh list

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linter
	@echo "$(BLUE)Running linter...$(NC)"
	$(PYTHON) -m flake8 . --max-line-length=100 --exclude=venv,__pycache__,.git
	@echo "$(GREEN)Linting complete!$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	$(PYTHON) -m black . --line-length=100 --exclude="venv|__pycache__|\.git"
	$(PYTHON) -m isort . --profile black --skip venv --skip __pycache__
	@echo "$(GREEN)Formatting complete!$(NC)"

typecheck: ## Run type checker
	@echo "$(BLUE)Running type checker...$(NC)"
	$(PYTHON) -m mypy . --ignore-missing-imports
	@echo "$(GREEN)Type check complete!$(NC)"

check: lint typecheck test ## Run all checks

# =============================================================================
# Logs
# =============================================================================

logs: ## Show application logs
	@tail -f logs/*.log 2>/dev/null || echo "No log files found"

logs-api: ## Show API logs
	@tail -f logs/api/*.log 2>/dev/null || echo "No API logs found"

logs-clear: ## Clear log files
	@echo "$(YELLOW)Clearing logs...$(NC)"
	@rm -rf logs/*.log logs/**/*.log
	@echo "$(GREEN)Logs cleared!$(NC)"

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean Python cache files
	@echo "$(BLUE)Cleaning cache files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .mypy_cache 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

clean-all: clean docker-clean logs-clear ## Full cleanup

# =============================================================================
# Development
# =============================================================================

dev: ## Start development environment
	@echo "$(BLUE)Starting development environment...$(NC)"
	@make docker-up
	@sleep 5
	@make status
	@echo "$(GREEN)Development environment ready!$(NC)"
	@echo "$(YELLOW)API: http://localhost:8080$(NC)"
	@echo "$(YELLOW)n8n: http://localhost:5678$(NC)"

shell: ## Open Python shell with project context
	$(PYTHON) -c "from core import *; import code; code.interact(local=locals())"

# =============================================================================
# Production
# =============================================================================

prod: ## Start production environment
	@echo "$(BLUE)Starting production environment...$(NC)"
	$(DOCKER_COMPOSE) -f body/docker/docker-compose.yml up -d
	@echo "$(GREEN)Production environment started!$(NC)"

prod-logs: ## Show production logs
	$(DOCKER_COMPOSE) logs -f --tail=100
