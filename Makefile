# ============================================
# Voice Platform - Makefile
# ============================================
# Quick commands for development. Run `make help` to see all options.

.PHONY: help setup backend frontend docker-up docker-down test lint clean

# Default target
help: ## Show this help message
	@echo "🎤 Voice Platform - Available Commands"
	@echo "======================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---- Setup ----
setup: ## First-time setup (install all dependencies)
	@echo "📦 Setting up backend..."
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	@echo "📦 Setting up frontend..."
	cd frontend && npm install
	@echo ""
	@echo "✅ Setup complete! Next steps:"
	@echo "  1. Copy backend/.env.example to backend/.env"
	@echo "  2. Add your OpenAI API key to backend/.env"
	@echo "  3. Run 'make backend' to start the API"
	@echo "  4. Run 'make frontend' in another terminal"

# ---- Development ----
backend: ## Start backend dev server
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend: ## Start frontend dev server
	cd frontend && npm run dev

# ---- Docker ----
docker-up: ## Start all services with Docker (requires Colima)
	@echo "🐳 Starting services..."
	@colima status 2>/dev/null || (echo "Starting Colima..." && colima start)
	docker compose up --build

docker-down: ## Stop all Docker services
	docker compose down

# ---- Testing ----
test: ## Run backend tests
	cd backend && . .venv/bin/activate && pytest --cov=app --cov-report=term-missing

test-watch: ## Run backend tests in watch mode
	cd backend && . .venv/bin/activate && pytest --cov=app -f

# ---- Code Quality ----
lint: ## Lint and format check
	cd backend && . .venv/bin/activate && ruff check app/ && ruff format --check app/

format: ## Auto-format code
	cd backend && . .venv/bin/activate && ruff format app/ tests/

# ---- Cleanup ----
clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .venv -exec rm -rf {} + 2>/dev/null || true
	@echo "🧹 Cleaned!"
