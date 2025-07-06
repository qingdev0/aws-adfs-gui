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
    uv run python -m src.aws_adfs_gui.main web

# Start the web application and open in browser
web-open:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🚀 Starting AWS ADFS GUI web application..."
    echo "📱 Opening browser at: http://127.0.0.1:8000"

    # Kill any existing server processes
    just kill-server || true

    # Start the web server in background
    uv run python -m src.aws_adfs_gui.main web &
    SERVER_PID=$!

    # Wait a moment for server to start
    sleep 2

    # Open browser based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open "http://127.0.0.1:8000"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        xdg-open "http://127.0.0.1:8000"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows
        start "http://127.0.0.1:8000"
    else
        echo "⚠️  Could not detect OS. Please open http://127.0.0.1:8000 manually"
    fi

    # Wait for server process
    wait $SERVER_PID

# Start the web application in development mode
web-dev:
    uv run uvicorn src.aws_adfs_gui.web_app:app --reload --host 127.0.0.1 --port 8000

# Start the web application in development mode and open in browser
web-dev-open:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🚀 Starting AWS ADFS GUI web application in development mode..."
    echo "📱 Opening browser at: http://127.0.0.1:8000"

    # Kill any existing server processes
    just kill-server || true

    # Start the web server in background
    uv run uvicorn src.aws_adfs_gui.web_app:app --reload --host 127.0.0.1 --port 8000 &
    SERVER_PID=$!

    # Wait a moment for server to start
    sleep 2

    # Open browser based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open "http://127.0.0.1:8000"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        xdg-open "http://127.0.0.1:8000"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows
        start "http://127.0.0.1:8000"
    else
        echo "⚠️  Could not detect OS. Please open http://127.0.0.1:8000 manually"
    fi

    # Wait for server process
    wait $SERVER_PID

# Kill any running web server processes
kill-server:
    #!/usr/bin/env bash
    echo "🔪 Stopping any running web server processes..."

    # Kill processes using port 8000
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true

    # Kill any python processes running the web app
    pkill -f "src.aws_adfs_gui.main web" 2>/dev/null || true
    pkill -f "src.aws_adfs_gui.web_app:app" 2>/dev/null || true

    echo "✅ Server processes stopped"

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
    @echo "2. Start coding in src/aws_adfs_gui/"
    @echo "3. Run tests: just test"
    @echo "4. Check code quality: just all"
    @echo "5. Start web GUI: just web-open"
