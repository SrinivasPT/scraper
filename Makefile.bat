# Development Commands for RegScraper

## Setup
install-dev:
	py -m pip install -e .
	py -m pip install ruff pytest pytest-asyncio

## Code Quality
lint:
	py -m ruff check src/ tests/

lint-fix:
	py -m ruff check --fix --unsafe-fixes src/ tests/

format:
	py -m ruff format src/ tests/

check: lint format
	py -m ruff check src/ tests/

## Testing
test:
	py -m pytest tests/ -v

test-cov:
	py -m pytest tests/ -v --cov=regscraper --cov-report=html --cov-report=term

## Clean
clean:
	rmdir /s /q __pycache__ 2>nul || echo "No __pycache__ to clean"
	rmdir /s /q .pytest_cache 2>nul || echo "No .pytest_cache to clean"
	rmdir /s /q .ruff_cache 2>nul || echo "No .ruff_cache to clean"
	rmdir /s /q htmlcov 2>nul || echo "No htmlcov to clean"
	for /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

## All-in-one
dev-setup: install-dev lint-fix test

.PHONY: install-dev lint lint-fix format check test test-cov clean dev-setup
