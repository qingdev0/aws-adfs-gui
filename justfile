# AWS ADFS Project Justfile

# Default recipe to show help
default:
    @just --list

# Install production dependencies
install:
    uv sync

# Install development dependencies
install-dev:
    uv sync --dev

# Run tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=src --cov-report=term-missing --cov-report=html

# Run linting
lint:
    uv run ruff check .

# Fix linting issues
lint-fix:
    uv run ruff check . --fix

# Format code
format:
    uv run ruff format .

# Check code formatting
format-check:
    uv run ruff format . --check

# Run type checking
type-check:
    uv run mypy src/

# Install pre-commit hooks
pre-commit-install:
    uv run pre-commit install

# Run pre-commit hooks on all files
pre-commit-run:
    uv run pre-commit run --all-files

# Start the web application
web:
    uv run python -m aws_adfs.main web

# Start the web application in development mode
web-dev:
    uv run uvicorn aws_adfs.web_app:app --reload --host 127.0.0.1 --port 8000

# Clean up generated files
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    find . -type d -name "*.egg-info" -exec rm -rf {} +
    find . -type d -name ".pytest_cache" -exec rm -rf {} +
    find . -type d -name ".mypy_cache" -exec rm -rf {} +
    find . -type d -name "htmlcov" -exec rm -rf {} +
    find . -type f -name ".coverage" -delete
    find . -type f -name "coverage.xml" -delete

# Run all quality checks
all: lint format type-check test

# Setup the project (install deps, pre-commit hooks, and run initial checks)
setup: install-dev pre-commit-install
    @echo "✅ Setup complete!"
    @echo "Next steps:"
    @echo "1. Activate the virtual environment: source .venv/bin/activate"
    @echo "2. Start coding in src/aws_adfs/"
    @echo "3. Run tests: just test"
    @echo "4. Check code quality: just all"
    @echo "5. Start web GUI: just web"
