.PHONY: help install dev-install run dev test clean docker-build docker-up docker-down docker-logs migrate upgrade downgrade lint format

help:
	@echo "CV Parser API - Available Commands:"
	@echo "  make install        - Install production dependencies"
	@echo "  make dev-install    - Install dev dependencies"
	@echo "  make run            - Run the application"
	@echo "  make dev            - Run in development mode with reload"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linters"
	@echo "  make format         - Format code"
	@echo "  make clean          - Clean cache and temp files"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make docker-up      - Start Docker containers"
	@echo "  make docker-down    - Stop Docker containers"
	@echo "  make docker-logs    - View Docker logs"
	@echo "  make migrate        - Create new migration"
	@echo "  make upgrade        - Apply migrations"
	@echo "  make downgrade      - Rollback last migration"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black ruff mypy

run:
	python run.py

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term

lint:
	ruff check app/
	mypy app/

format:
	black app/
	ruff check --fix app/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app

docker-restart:
	docker-compose restart app

migrate:
	alembic revision --autogenerate -m "$(message)"

upgrade:
	alembic upgrade head

downgrade:
	alembic downgrade -1

db-init:
	alembic upgrade head

docker-shell:
	docker-compose exec app /bin/bash

docker-db-shell:
	docker-compose exec postgres psql -U cvparser -d cv_parser_db