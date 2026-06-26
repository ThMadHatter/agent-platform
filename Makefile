.PHONY: help install test lint run migrate build up down

VENV=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip
BLACK=$(VENV)/bin/black
ISORT=$(VENV)/bin/isort
MYPY=$(VENV)/bin/mypy

help:
	@echo "Available commands:"
	@echo "  install      Install dependencies and setup venv"
	@echo "  test         Run tests"
	@echo "  lint         Run linter"
	@echo "  run          Run the API locally"
	@echo "  migrate      Run database migrations"
	@echo "  migration    Create a new migration (usage: make migration MSG='description')"
	@echo "  db-current   Show current migration revision"
	@echo "  db-history   Show migration history"
	@echo "  build        Build Docker images"
	@echo "  up           Start services with Docker Compose"
	@echo "  down         Stop services"

install:
	python3 -m venv $(VENV)
	$(PIP) install -e ".[dev,test]"

test:
	PYTHONPATH=. $(PYTHON) -m pytest tests/

lint:
	$(BLACK) .
	$(ISORT) .
	$(MYPY) .

run:
	PYTHONPATH=. $(VENV)/bin/uvicorn apps.api.main:app --reload

migrate:
	PYTHONPATH=. $(VENV)/bin/alembic upgrade head

migration:
	PYTHONPATH=. $(VENV)/bin/alembic revision --autogenerate -m "$(MSG)"

db-current:
	PYTHONPATH=. $(VENV)/bin/alembic current

db-history:
	PYTHONPATH=. $(VENV)/bin/alembic history

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down
