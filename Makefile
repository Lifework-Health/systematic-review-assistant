.PHONY: help bootstrap python python.list install install.prod format lint ruff.fix typecheck clean clean.lean security supabase.cli supabase.dbdev submodules docker.build docker.test run run.prototype test.unit test.integration test.all

.DEFAULT_GOAL := help

SHELL := /bin/bash

# Get the short Git SHA
GIT_SHA := $(shell git rev-parse --short HEAD)

DOCKER_IMAGE_NAME := mph-sra
DOCKER_IMAGE_TAG_LATEST := latest

bootstrap:  ## How to install the `uv` project managent tool
	@echo "Pick your poison:"
	@echo
	@echo "    brew install uv"
	@echo "    pipx install uv"
	@echo "    pip install uv"
	@echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"
	@echo "    cargo install --git https://github.com/astral-sh/uv uv"
	@echo "    winget install --id=astral-sh.uv  -e"
	@echo "    scoop install main/uv"
	@echo "    powershell -ExecutionPolicy ByPass -c 'irm https://astral.sh/uv/install.ps1 | iex'"
	@echo
	@echo "Or go container:  docker run ghcr.io/astral-sh/uv ..."

docker.build: ## Build the Docker image
	@echo "Building Docker image $(DOCKER_IMAGE_NAME):$(GIT_SHA) and tagging as $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG_LATEST)..."
	docker build -t $(DOCKER_IMAGE_NAME):$(GIT_SHA) -t $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG_LATEST) .

python.install: ## Install project local Python managed by uv
	uv python install

python.list: ## Show Python versions available with uv
	uv python list

install.prod: python  ## Install runtime dependencies
	uv sync --no-dev

deno.cli: ## Install Deno CLI, required by the VSCode extension used to develop edge function
	# Goes in $DXG_DATA_HOME/deno/bin, add to path, let the installer do it, or
	# symlink to $HOME/.local/bin or whatever it's on macoS.
	curl -fsSL https://deno.land/install.sh | sh
	deno --version
	@echo "Install the deno vscode extension (canary), use the egde-functions workspace"

install: python.install ## Install all dependencies for development
	uv sync
	uv run pre-commit install
	uv run pre-commit install --hook-type pre-push
	@echo "If needed, also run 'make deno.cli' if developing edge functions"

# Default run uses .env (prototype)
run: run.prototype

run.prototype: docker.build ## Run the development server using Docker (prototype environment with .env)
	@echo "Running application in Docker container (prototype environment)..."
	@printf "\n\033[0;32m#####################################################################\033[0m\n"
	@printf "\033[0;32m#                                                                   #\033[0m\n"
	@printf "\033[0;32m#   Access the Streamlit app at: http://localhost:8501              #\033[0m\n"
	@printf "\033[0;32m#   Or via:                       http://127.0.0.1:8501             #\033[0m\n"
	@printf "\033[0;32m#                                                                   #\033[0m\n"
	@printf "\033[0;32m#####################################################################\033[0m\n\n"
	docker run --rm -it \
		--env-file .env \
		-p 8501:8501 \
		-v $(shell pwd)/src:/app/src \
		-v $(shell pwd)/tests:/app/tests \
		-v $(shell pwd)/typings:/app/typings \
		-v $(shell pwd)/.pytest_cache:/app/.pytest_cache \
		-v $(shell pwd)/htmlcov:/app/htmlcov \
		$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG_LATEST)
	#-v $(shell pwd)/app.log:/app/app.log \ # TODO: fix this, it's a file but gets mounted as dir

# If you need to run the app with the test environment, you can add a similar target:
# run.test: docker.build ## Run the development server using Docker (test environment with .env.test)
# 	@echo "Running application in Docker container (test environment)..."
# 	docker run --rm -it \
# 		--env-file .env.test \
# 		-p 8501:8501 \
# 		-v $(shell pwd)/src:/app/src \
# 		-v $(shell pwd)/tests:/app/tests \
# 		-v $(shell pwd)/.pytest_cache:/app/.pytest_cache \
# 		-v $(shell pwd)/htmlcov:/app/htmlcov \
# 		-v $(shell pwd)/.coverage:/app/.coverage \
# 		$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG_LATEST)

format:  ## Format and fix code with ruff
	uv run ruff format
	uv run ruff check --fix

ruff.fix:
	uv run check --fix

lint:  ## Lint code with ruff
	uv run ruff check

typecheck:  ## Run MyPy
	uv run mypy

security:
	uv sync --group security
	uv run pip-audit
	uv run ruff --select="S"

docker.test: ## Base target to run tests in Docker (internal use with ENV_FILE and PYTEST_CMD args)
	@echo "Running tests in Docker container with $(ENV_FILE) environment..."
	docker run --rm -it \
		--env-file $(ENV_FILE) \
		-v $(shell pwd)/src:/app/src \
		-v $(shell pwd)/tests:/app/tests \
		-v $(shell pwd)/typings:/app/typings \
		-v $(shell pwd)/.pytest_cache:/app/.pytest_cache \
		-v $(shell pwd)/htmlcov:/app/htmlcov \
		$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG_LATEST) \
		sh -c "rm -rf /app/.coverage && uv run pytest $(PYTEST_CMD)"
# -v $(shell pwd)/.coverage:/app/.coverage \ # Temporarily commented out for debugging
	#-v $(shell pwd)/app.log:/app/app.log \ # FIXME

test.unit: docker.build ## Run unit tests with coverage using Docker (uses .env.test)
	@rm -rf .coverage
	$(MAKE) docker.test ENV_FILE=.env.test PYTEST_CMD="tests/unit --cov=src --cov-report=term --cov-report=html"
	@echo "Coverage report available at htmlcov/index.html"

test.integration: docker.build ## Run integration tests only using Docker (uses .env.test)
	@rm -rf .coverage
	$(MAKE) docker.test ENV_FILE=.env.test PYTEST_CMD="tests/integration -m integration"

test.all: docker.build ## Run all tests with coverage using Docker (uses .env.test)
	@rm -rf .coverage
	$(MAKE) docker.test ENV_FILE=.env.test PYTEST_CMD="tests --cov=src --cov-report=term --cov-report=html"
	@echo "Coverage report available at htmlcov/index.html"

pre-commit:  ## Run pre-commit on all files
	uv run pre-commit run --all-files

clean: clean.dev  ## Clean Python build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".eggs" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +


clean.dev: clean  ## Clean everything including development artifacts
	rm -rf .venv/
	rm -rf htmlcov/
	rm -rf .coverage*
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .pre-commit-cache/

supabase.cli:  ## Install Supabase CLI
	brew install supabase/tap/supabase

supabase.dbdev: ## Install dbdev DB package manager
	brew install supabase/tap/dbdev

submodules:  ## Sync git submodules (database-build, etc.)
	git submodule update --init --recursive
	@echo ">> tools/database-build synced: in-browser WASM AI assisted Postgres IDE"

help:  ## Show this help
	@grep -E '^[a-z/.:A-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
