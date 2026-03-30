.PHONY: install dev-backend dev-frontend dev-docs test lint format build \
        db-up db-down db-migrate db-seed

install:
	cd backend && uv sync --group dev
	cd frontend && npm install
	cd docs && npm install

# Dev servers
dev-backend:
	cd backend && fastapi dev app/main.py

dev-frontend:
	cd frontend && npm run dev

dev-docs:
	cd docs && npm run docs:dev

# Database
db-up:
	docker-compose up -d

db-down:
	docker-compose down

db-migrate:
	cd backend && alembic upgrade head

db-seed:
	cd backend && uv run python seeds/seed_data.py

# Quality
test:
	cd backend && uv run pytest --tb=short -q

lint:
	cd backend && uv run ruff check .
	cd frontend && npm run lint

format:
	cd backend && uv run ruff format .

# Build
build:
	cd frontend && npm run build
	cd docs && npm run docs:build
