.PHONY: help install dev test lint format clean docker docker-run docker-logs

PYTHON := python3
VENV := venv
PYTHON_VENV := $(VENV)/bin/python
PIP_VENV := $(VENV)/bin/pip

help:
	@echo "Salla MCP Server - Development Tasks"
	@echo "====================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make dev          - Setup development environment"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean generated files"
	@echo "  make docker       - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo "  make docker-logs  - View Docker logs"

install:
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	$(PYTHON) -m pip install -e .

dev: install
	$(PYTHON) -m pip install -e .[dev,test,docs]
	pre-commit install

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src/salla_mcp --cov-report=html --cov-report=term-missing

lint:
	flake8 src tests --max-line-length=100
	pylint src/salla_mcp --exit-zero
	mypy src/salla_mcp --ignore-missing-imports

format:
	black src tests
	isort src tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

run:
	$(PYTHON) server.py

docker:
	docker build -f deployment/Dockerfile -t salla-mcp:latest .

docker-run:
	docker-compose -f deployment/docker-compose.yml up

docker-logs:
	docker-compose -f deployment/docker-compose.yml logs -f

docker-stop:
	docker-compose -f deployment/docker-compose.yml down

docs:
	cd docs && sphinx-build -W -b html -d _build/doctrees . _build/html
	@echo "Documentation built to docs/_build/html"

.PHONY: $(MAKECMDGOALS)
