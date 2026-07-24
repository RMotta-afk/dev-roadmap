.PHONY: help install dev test lint seed format

.DEFAULT_GOAL := help

help: ## Print available targets
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies for frontend and backend
	pnpm install
	cd apps/api && uv sync

dev: ## Run frontend and backend dev servers in parallel
	@echo "Starting dev servers. Press Ctrl+C to stop both."
	@trap 'kill %1' EXIT; \
		(cd apps/api && uv run uvicorn app.main:app --reload) & \
		(pnpm --filter web dev) & \
		wait

test: ## Run tests across workspaces and pytest in apps/api
	pnpm --filter './apps/*' --filter './packages/*' test
	cd apps/api && uv run pytest

lint: ## Run lint across workspaces and ruff check in apps/api
	pnpm --filter './apps/*' --filter './packages/*' lint
	cd apps/api && uv run ruff check .

seed: ## Run seed script for Qdrant and admin user creation
	cd apps/api && uv run python -m app.seed

format: ## Run prettier for JS and ruff format for Python
	pnpm --filter './apps/*' --filter './packages/*' format
	cd apps/api && uv run ruff format .
