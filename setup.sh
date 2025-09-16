#!/bin/bash

# MotiveProxy Setup Script for Bash/Linux/macOS
# This script sets up a Python virtual environment and installs dependencies

set -e  # Exit on any error

echo "🚀 Setting up MotiveProxy development environment..."

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION detected. Python $REQUIRED_VERSION or higher is required."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "🛠️  Installing development dependencies..."
pip install -e ".[dev]"

# Install invoke for task running
echo "📋 Installing invoke task runner..."
pip install invoke

# Run initial tests to verify setup
echo "🧪 Running initial tests..."
python -m pytest tests/ -v

# Set up environment template for E2E testing
echo "🔧 Setting up E2E testing environment..."
python setup_env.py

echo ""
echo "🎉 Setup complete! Your MotiveProxy development environment is ready."
echo ""
echo "To activate the environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests:"
echo "  inv test"
echo ""
echo "To format code:"
echo "  inv format"
echo ""
echo "To run the proxy server:"
echo "  inv run"
echo ""
echo "To see all available tasks:"
echo "  inv --list"
echo ""
echo "To run E2E tests with real LLMs:"
echo "  # Edit .env file with your API keys"
echo "  motive-proxy-e2e --use-llms --turns 5"
echo ""
echo "To run advanced LLM-to-LLM testing:"
echo "  motive-proxy-e2e --use-llms --turns 20 --max-context-messages 6"
echo ""
