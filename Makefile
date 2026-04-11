.PHONY: help dev down up test test-int test-all lint lint-fix format build logs clean lock install shell health

COMPOSE_DEV := docker compose -f docker-compose.dev.yml
COMPOSE_PROD := docker compose -f docker-compose.prod.yml
VENV := .venv/bin
PYTHON := $(VENV)/python
IMAGE := agents-api

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

dev: ## Start full dev stack (Qdrant + API + Chainlit) in Docker
	$(COMPOSE_DEV) up -d

down: ## Stop all dev services
	$(COMPOSE_DEV) down

up: dev ## Alias for dev

logs: ## Follow dev service logs
	$(COMPOSE_DEV) logs -f

shell: ## Open a shell in the agents-api container
	docker exec -it agents-api-dev bash

health: ## Curl the /health endpoint
	@curl -s http://localhost:8060/health | $(PYTHON) -m json.tool

install: ## Create venv and install all deps with uv
	uv venv --python 3.13 .venv
	uv pip install -e ".[dev]"

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: ## Run unit tests (fast, mocked — no Docker required)
	$(PYTHON) -m pytest -m unit -v

test-int: ## Run integration tests (requires Docker services)
	$(PYTHON) -m pytest -m integration -v

test-all: ## Run all tests with coverage
	$(PYTHON) -m pytest --cov=src --cov-report=term -v

# ---------------------------------------------------------------------------
# Code Quality
# ---------------------------------------------------------------------------

lint: ## Run ruff linter
	$(PYTHON) -m ruff check src/ tests/

lint-fix: ## Run ruff linter with auto-fix
	$(PYTHON) -m ruff check --fix src/ tests/

format: ## Run ruff formatter
	$(PYTHON) -m ruff format src/ tests/

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

build: ## Build the Docker image
	docker build -t $(IMAGE) .

lock: ## Generate uv.lock from pyproject.toml
	uv lock

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ dist/ build/
