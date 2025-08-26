#!/bin/bash
# Development Environment Setup Script using UV

set -e

echo "🚀 Setting up Divine Whispers Backend Development Environment with UV"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
else
    echo "✅ uv is already installed"
fi

# Create virtual environment with uv
echo "🐍 Creating virtual environment..."
uv venv --python 3.11

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies with uv..."
uv pip install -r requirements.txt

# Install development dependencies
echo "🛠️ Installing development dependencies..."
uv pip install -e ".[dev]"

# Setup pre-commit hooks
echo "🔗 Setting up pre-commit hooks..."
pre-commit install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
fi

echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source .venv/bin/activate"
echo "2. Edit .env file with your configuration"
echo "3. Start the development server: uvicorn app.main:app --reload"
echo "4. Or use Docker: docker-compose -f docker-compose.yml -f docker-compose.dev.yml up"