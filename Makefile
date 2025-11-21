.PHONY: lint lint-fix test install dev clean help

help:
	@echo "Available targets:"
	@echo "  make lint      - Run ruff linter (check only)"
	@echo "  make lint-fix  - Run ruff linter and auto-fix issues"
	@echo "  make test      - Run pytest tests"
	@echo "  make install   - Install package in development mode"
	@echo "  make dev       - Install package with dev dependencies"
	@echo "  make clean     - Remove build artifacts and cache files"

lint:
	@echo "Running ruff linter..."
	uv run ruff check src/

lint-fix:
	@echo "Running ruff linter with auto-fix..."
	uv run ruff check --fix src/
	uv run ruff format src/

test:
	@echo "Running tests..."
	uv run pytest

install:
	@echo "Installing package in development mode..."
	uv pip install -e .

dev:
	@echo "Installing with dev dependencies..."
	uv sync --group dev

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
