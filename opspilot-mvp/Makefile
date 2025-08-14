.PHONY: help setup dev build test clean docker-build docker-up docker-down

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Initial project setup
	@echo "Setting up OpsPilot MVP..."
	cp infra/.env.example .env
	@echo "Environment file created. Please update .env with your settings."
	@echo "Run 'make docker-up' to start the application."

dev: ## Start development environment
	docker-compose -f infra/docker-compose.yml up --build

build: ## Build all containers
	docker-compose -f infra/docker-compose.yml build

test: ## Run tests
	@echo "Running backend tests..."
	cd apps/backend && python -m pytest tests/ -v
	@echo "Running frontend tests..."
	cd apps/frontend && npm test

clean: ## Clean up containers and volumes
	docker-compose -f infra/docker-compose.yml down -v
	docker system prune -f

docker-build: ## Build Docker images
	docker-compose -f infra/docker-compose.yml build

docker-up: ## Start Docker containers
	docker-compose -f infra/docker-compose.yml up -d

docker-down: ## Stop Docker containers
	docker-compose -f infra/docker-compose.yml down

logs: ## View application logs
	docker-compose -f infra/docker-compose.yml logs -f

backend-shell: ## Access backend container shell
	docker-compose -f infra/docker-compose.yml exec backend bash

db-migrate: ## Run database migrations
	docker-compose -f infra/docker-compose.yml exec backend alembic upgrade head

db-reset: ## Reset database (WARNING: destroys data)
	docker-compose -f infra/docker-compose.yml exec db psql -U postgres -c "DROP DATABASE IF EXISTS opspilot;"
	docker-compose -f infra/docker-compose.yml exec db psql -U postgres -c "CREATE DATABASE opspilot;"
	make db-migrate

seed-data: ## Load sample data
	@echo "Loading sample data..."
	curl -X POST -F "file=@sample_data/internal_trades.csv" -F "kind=internal" http://localhost:8000/api/v1/files/upload
	curl -X POST -F "file=@sample_data/cleared_trades.csv" -F "kind=cleared" http://localhost:8000/api/v1/files/upload
	curl -X POST -F "file=@sample_data/span_margins.csv" -F "kind=span" http://localhost:8000/api/v1/files/upload
	@echo "Sample data loaded successfully!"

demo: ## Full demo setup
	make setup
	make docker-up
	sleep 10
	make db-migrate
	make seed-data
	@echo ""
	@echo "🚀 OpsPilot MVP is ready!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
