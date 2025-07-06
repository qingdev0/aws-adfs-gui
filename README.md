# AWS ADFS GUI

A modern Python web application for AWS ADFS integration with multi-profile
command execution.

## Features

- **🚀 Modern Python Development Setup**

  - Python 3.12 with type hints and mypy
  - Linting and formatting with ruff
  - Testing with pytest and coverage
  - Pre-commit hooks for code quality
  - CI/CD with GitHub Actions
  - Automated dependency updates with Dependabot

- **🌐 Web-based GUI for AWS Multi-Profile Commands**

  - Execute AWS commands across multiple profiles simultaneously
  - Smart error handling (dev profiles first, then others)
  - Real-time results streaming via WebSocket
  - Command history (last 100 commands)
  - Export results in JSON, CSV, or text formats
  - Profile grouping (dev, non-production, production)

- **🔐 Secure Configuration Management**
  - Encrypted credential storage with Fernet encryption
  - Configuration stored in `~/.aws/gui/` directory
  - Automatic credential validation and testing
  - ADFS authentication integration

## Requirements

- **Python 3.12** (pinned version)
- **uv** (for fast dependency management)
- **AWS CLI** (for profile management)

## Installation

1. **Clone the repository:**

```bash
git clone https://github.com/qingdev0/aws-adfs-gui.git
cd aws-adfs-gui
```

1. **Install uv if you haven't already:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

1. **Quick setup (recommended):**

```bash
just setup
```

This will install dependencies, set up pre-commit hooks, and run initial checks.

1. **Manual setup:**

```bash
# Install dependencies
uv sync --dev

# Install pre-commit hooks
just pre-commit-install
```

## Development

### Project Structure

```text
aws-adfs-gui/
├── src/
│   └── aws_adfs_gui/
│       ├── __init__.py
│       ├── main.py              # CLI entry point
│       ├── web_app.py           # FastAPI web application
│       ├── models.py            # Data models
│       ├── config.py            # Configuration management
│       ├── secure_config.py     # Secure credential storage
│       ├── aws_credentials.py   # AWS credential management
│       ├── adfs_auth.py         # ADFS authentication
│       └── command_executor.py  # Command execution engine
├── tests/                       # Comprehensive test suite
├── static/                      # Web UI assets
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── .github/
│   ├── workflows/ci.yml         # GitHub Actions CI
│   └── dependabot.yml          # Automated dependency updates
├── pyproject.toml               # Python project configuration
├── justfile                     # Project commands
└── README.md
```

### Available Commands

**Just commands (recommended):**

```bash
# Setup and Installation
just setup              # Complete project setup
just install-dev         # Install development dependencies
just install             # Install production dependencies

# Development
just web-open            # Start web app and open browser automatically
just web-dev-open        # Start web app in dev mode and open browser
just web                 # Start web application
just web-dev             # Start web application in development mode

# Testing and Quality
just test                # Run tests
just test-cov            # Run tests with coverage
just lint                # Check code quality
just lint-fix            # Fix linting issues automatically
just format              # Format code
just format-check        # Check code formatting
just type-check          # Run type checking
just all                 # Run all quality checks

# Utilities
just kill-server         # Kill any running web server processes
just clean               # Clean up generated files
just pre-commit-install  # Install pre-commit hooks
just pre-commit-run      # Run pre-commit hooks on all files
```

**Direct uv commands:**

```bash
# Install dependencies
uv sync --dev

# Run tests
uv run pytest
uv run pytest --cov=src

# Code quality
uv run ruff check .
uv run ruff format .
uv run mypy src/

# Start web application
uv run python -m aws_adfs_gui.main web
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
just pre-commit-install
```

This automatically runs on every commit:

- **ruff** (linting and formatting)
- **mypy** (type checking)
- **pytest** (tests)
- **File checks** (trailing whitespace, end of files, YAML syntax)

### Adding Dependencies

```bash
# Add runtime dependency
uv add package-name

# Add development dependency
uv add --dev package-name
```

## Web GUI Usage

### Quick Start

```bash
# Start the web application and open browser automatically
just web-open

# Or for development with auto-reload
just web-dev-open
```

The application will:

1. **Start the server** on `http://127.0.0.1:8000`
1. **Automatically open your browser** to the application
1. **Kill any existing server processes** to prevent port conflicts

### Manual Start

```bash
# Start the server
just web

# Then open http://127.0.0.1:8000 in your browser
```

### Using the GUI

1. **📱 Open Browser**: Navigate to `http://127.0.0.1:8000`
1. **🔧 Configure Settings**: Set up ADFS credentials in the configuration panel
1. **👥 Select AWS Profiles**: Choose from the left panel (grouped by environment)
1. **⚡ Execute Commands**: Enter AWS CLI commands in the center panel
1. **📊 View Results**: Real-time results appear in separate tabs
1. **💾 Export Data**: Download results in JSON, CSV, or text format

### Key Features

- **🎯 Smart Error Handling**: Dev profiles execute first; failures skip other profiles
- **📺 Real-time Updates**: WebSocket streaming for live results
- **📚 Command History**: Easily reuse previous commands (last 100)
- **🏷️ Profile Grouping**:
  - **Dev**: `aws-dev-eu`, `aws-dev-sg`
  - **Non-Production**: `kds-ets-np`, `kds-gps-np`, `kds-iss-np`
  - **Production**: `kds-ets-pd`, `kds-gps-pd`, `kds-iss-pd`
- **📤 Export Options**: Multiple output formats available

## Testing

Comprehensive test suite with pytest:

```bash
# Run all tests
just test

# Run tests with coverage report
just test-cov

# Run specific test file
uv run pytest tests/test_web_app.py

# Run with verbose output
uv run pytest -v
```

**Test Coverage**: 166 tests covering all major functionality including:

- Web application endpoints
- AWS credential management
- ADFS authentication
- Command execution
- Configuration management
- Security features

## Code Quality

### Linting and Formatting

Using **ruff** for fast linting and formatting:

```bash
# Check for issues
just lint

# Fix issues automatically
just lint-fix

# Format code
just format

# Check formatting
just format-check
```

### Type Checking

Using **mypy** for static type checking:

```bash
# Run type checker
just type-check

# All quality checks at once
just all
```

## CI/CD

- **GitHub Actions**: Automated testing on push and pull requests
- **Python 3.12**: Consistent version across development and CI
- **Quality Gates**: Linting, formatting, type checking, and tests
- **Dependabot**: Automated dependency updates
- **Coverage Reporting**: Test coverage tracking

## Security

- **🔐 Encrypted Storage**: Credentials encrypted with Fernet
- **🏠 Local Storage**: Configuration in `~/.aws/gui/` directory
- **🔒 Secure Defaults**: No credentials stored in plain text
- **✅ Validation**: Automatic credential testing and validation

## Contributing

1. **Fork the repository**
1. **Create a feature branch**: `git checkout -b feature-name`
1. **Make your changes**
1. **Run quality checks**: `just all`
1. **Commit with conventional commits**: `git commit -m "feat: add new feature"`
1. **Push to your fork**: `git push origin feature-name`
1. **Create a pull request**

## License

[Add your license here]

## Troubleshooting

### Common Issues

**Port already in use:**

```bash
just kill-server
```

**Dependencies out of sync:**

```bash
uv sync --dev
```

**Pre-commit hooks failing:**

```bash
just pre-commit-run
```

**Browser doesn't open automatically:**

- Manual access: `http://127.0.0.1:8000`
- Check OS compatibility in justfile

### Getting Help

- **View available commands**: `just --list`
- **Project setup**: `just setup`
- **Clean start**: `just clean && just setup`
