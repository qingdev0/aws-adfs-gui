#!/bin/bash

# AWS ADFS Project Setup Script

set -e

echo "🚀 Setting up AWS ADFS project..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv is installed"

# Install dependencies
echo "📦 Installing dependencies..."
uv sync --dev

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
uv run pre-commit install

# Run initial checks
echo "🔍 Running initial quality checks..."
uv run pre-commit run --all-files

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Start coding in src/aws_adfs_gui/"
echo "3. Run tests: just test"
echo "4. Check code quality: just all"
echo "5. Start web GUI: just web"
echo ""
echo "Available just commands:"
just --list
