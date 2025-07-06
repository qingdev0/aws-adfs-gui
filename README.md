# AWS ADFS

A Python project for AWS ADFS integration.

## Features

- Modern Python development setup
- Type hints with mypy
- Linting and formatting with ruff
- Testing with pytest
- Pre-commit hooks
- CI/CD with GitHub Actions
- **Web-based GUI for AWS multi-profile command execution**
  - Execute AWS commands across multiple profiles simultaneously
  - Smart error handling (dev profiles first, then others)
  - Real-time results streaming
  - Command history (last 100 commands)
  - Export results in JSON, CSV, or text formats
  - Profile grouping (dev, non-production, production)

## Requirements

- Python 3.8+
- uv (for dependency management)

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd aws-adfs
```

2. Install uv if you haven't already:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Install dependencies:

```bash
uv sync --dev
```

4. Activate the virtual environment:

```bash
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate     # On Windows
```

## Development

### Project Structure

```
aws-adfs/
├── src/
│   └── aws_adfs/
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── pyproject.toml
├── .pre-commit-config.yaml
├── .github/
│   └── workflows/
│       └── ci.yml
└── README.md
```

### Available Commands

- **Install dependencies**: `uv sync --dev`
- **Run tests**: `uv run pytest`
- **Run tests with coverage**: `uv run pytest --cov=src`
- **Lint code**: `uv run ruff check .`
- **Format code**: `uv run ruff format .`
- **Type check**: `uv run mypy src/`
- **Install pre-commit hooks**: `uv run pre-commit install`
- **Start web GUI**: `just web` or `uv run python -m aws_adfs.main web`
- **Start web GUI (dev mode)**: `just web-dev`

**Or use Just commands (recommended):**
- `just install-dev` - Install development dependencies
- `just test` - Run tests
- `just test-cov` - Run tests with coverage
- `just lint` - Check code quality
- `just format` - Format code
- `just type-check` - Run type checking
- `just all` - Run all quality checks
- `just web` - Start web application
- `just web-dev` - Start web application in development mode
- `just setup` - Complete project setup

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality. Install them with:

```bash
uv run pre-commit install
```

This will automatically run:

- ruff (linting and formatting)
- mypy (type checking)
- pytest (tests)
- Various file checks

### Adding Dependencies

To add a new dependency:

```bash
uv add package-name
```

To add a development dependency:

```bash
uv add --dev package-name
```

## Testing

The project uses pytest for testing. Tests are located in the `tests/` directory.

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_main.py

# Run tests with verbose output
uv run pytest -v
```

## Web GUI

The project includes a web-based GUI for executing AWS commands across multiple profiles.

### Starting the GUI

```bash
# Start the web application
just web

# Or directly
uv run python -m aws_adfs.main web

# For development with auto-reload
just web-dev
```

### Using the GUI

1. **Open your browser** to `http://127.0.0.1:8000`
2. **Select AWS profiles** from the left panel (grouped by dev, non-production, production)
3. **Enter a command** in the center panel (e.g., `aws s3 ls`, `aws ec2 describe-instances`)
4. **Click Execute** to run the command across selected profiles
5. **View results** in separate tabs on the right panel
6. **Export results** in JSON, CSV, or text format

### Features

- **Smart Error Handling**: Dev profiles execute first. If they fail, other profiles are skipped
- **Real-time Results**: See results as they complete
- **Command History**: Reuse previous commands (last 100)
- **Profile Groups**:
  - **Dev**: `aws-dev-eu`, `aws-dev-sg`
  - **Non-Production**: `kds-ets-np`, `kds-gps-np`, `kds-iss-np`
  - **Production**: `kds-ets-pd`, `kds-gps-pd`, `kds-iss-pd`
- **Export Options**: Download results in multiple formats

## Code Quality

### Linting and Formatting

The project uses ruff for both linting and formatting:

```bash
# Check for linting issues
uv run ruff check .

# Fix linting issues automatically
uv run ruff check . --fix

# Format code
uv run ruff format .

# Check formatting without making changes
uv run ruff format . --check
```

### Type Checking

Type checking is done with mypy:

```bash
# Run type checker
uv run mypy src/

# Run type checker with more verbose output
uv run mypy src/ --verbose
```

## CI/CD

The project includes GitHub Actions workflows that run on push and pull requests:

- Tests on multiple Python versions (3.8-3.12)
- Linting and formatting checks
- Type checking
- Coverage reporting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks:
   ```bash
   just all
   ```
5. Commit your changes
6. Push to your fork
7. Create a pull request

## License

[Add your license here]
