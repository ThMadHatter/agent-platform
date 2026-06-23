.PHONY: help install test lint run migrate build up down

help:
	@echo "Available commands:"
	@echo "  install   Install dependencies"
	@echo "  test      Run tests"
	@echo "  lint      Run linter"
	@echo "  run       Run the API locally"
	@echo "  migrate   Run database migrations"
	@echo "  build     Build Docker images"
	@echo "  up        Start services with Docker Compose"
	@echo "  down      Stop services"

install:
	pip install -e ".[dev,test]"

test:
	PYTHONPATH=. pytest tests/

lint:
	black .
	isort .
	mypy .

run:
	uvicorn apps.api.main:app --reload

migrate:
	alembic upgrade head

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down
