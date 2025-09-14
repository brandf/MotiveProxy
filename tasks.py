"""Modern Python task runner using invoke."""

from invoke import task
import subprocess
import sys
from pathlib import Path


@task
def install(c):
    """Install dependencies and the package in development mode."""
    print("📚 Installing dependencies...")
    c.run("pip install -r requirements.txt")
    c.run("pip install -e '.[dev]'")


@task
def test(c, verbose=False):
    """Run tests with pytest."""
    cmd = "pytest"
    if verbose:
        cmd += " -v"
    print("🧪 Running tests...")
    c.run(cmd)


@task
def test_cov(c):
    """Run tests with coverage reporting."""
    print("🧪 Running tests with coverage...")
    c.run("pytest --cov=src/motive_proxy --cov-report=html --cov-report=term")


@task
def lint(c):
    """Run linting tools."""
    print("🔍 Running linters...")
    c.run("flake8 src/ tests/")
    c.run("mypy src/")


@task
def format_code(c):
    """Format code with black and isort."""
    print("🎨 Formatting code...")
    c.run("black src/ tests/")
    c.run("isort src/ tests/")


@task
def clean(c):
    """Clean up build artifacts and cache files."""
    print("🧹 Cleaning up...")
    c.run("rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/")
    c.run("find . -type d -name __pycache__ -exec rm -rf {} +", warn=True)
    c.run("find . -type f -name '*.pyc' -delete", warn=True)


@task
def run(c, host="127.0.0.1", port=8000, reload=False):
    """Run the proxy server."""
    cmd = f"motive-proxy --host {host} --port {port}"
    if reload:
        cmd += " --reload --log-level debug"
    print(f"🚀 Starting MotiveProxy server on http://{host}:{port}")
    c.run(cmd)


@task
def dev(c):
    """Run the proxy server in development mode."""
    run(c, reload=True)


@task
def setup(c):
    """Set up the development environment."""
    print("🚀 Setting up MotiveProxy development environment...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return
    
    print(f"✅ Python {python_version.major}.{python_version.minor} detected")
    
    # Create virtual environment if it doesn't exist
    venv_path = Path("venv")
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        c.run("python -m venv venv")
    else:
        print("✅ Virtual environment already exists")
    
    print("🔧 Activating virtual environment and installing dependencies...")
    if sys.platform == "win32":
        activate_cmd = "venv\\Scripts\\activate && "
    else:
        activate_cmd = "source venv/bin/activate && "
    
    c.run(f"{activate_cmd}pip install --upgrade pip")
    c.run(f"{activate_cmd}pip install -r requirements.txt")
    c.run(f"{activate_cmd}pip install -e '.[dev]'")
    
    print("🧪 Running initial tests...")
    c.run(f"{activate_cmd}pytest tests/ -v")
    
    print("\n🎉 Setup complete! Your MotiveProxy development environment is ready.")
    print("\nCommon commands:")
    print("  inv test          - Run tests")
    print("  inv format        - Format code")
    print("  inv lint          - Run linters")
    print("  inv run           - Start the server")
    print("  inv dev           - Start the server in development mode")


@task
def pre_commit_install(c):
    """Install pre-commit hooks."""
    print("🔧 Installing pre-commit hooks...")
    c.run("pre-commit install")


@task
def pre_commit_run(c):
    """Run pre-commit on all files."""
    print("🔍 Running pre-commit on all files...")
    c.run("pre-commit run --all-files")
