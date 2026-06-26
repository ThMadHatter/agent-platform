.PHONY: help install test lint run migrate build up down

VENV=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

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
	apt install python3-venv -y
	python3 -m venv $(VENV)
	$(PIP) install -e ".[dev,test]"

test:
	PYTHONPATH=. $(VENV)/bin/pytest tests/

lint:
	$(VENV)/bin/black .
	$(VENV)/bin/isort .
	$(VENV)/bin/mypy .

run:
	$(VENV)/bin/uvicorn apps.api.main:app --reload

migrate:
	$(VENV)/bin/alembic upgrade head

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down
