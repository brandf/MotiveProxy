# MotiveProxy Setup Script for PowerShell/Windows
# This script sets up a Python virtual environment and installs dependencies

# Set error action preference to stop on errors
$ErrorActionPreference = "Stop"

Write-Host "🚀 Setting up MotiveProxy development environment..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "✅ $pythonVersion detected" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Check Python version (extract version number)
$versionString = python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))"
$versionParts = $versionString.Split('.')
$majorVersion = [int]$versionParts[0]
$minorVersion = [int]$versionParts[1]

if ($majorVersion -lt 3 -or ($majorVersion -eq 3 -and $minorVersion -lt 8)) {
    Write-Host "❌ Python $versionString detected. Python 3.8 or higher is required." -ForegroundColor Red
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "⬆️  Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "📚 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Install development dependencies
Write-Host "🛠️  Installing development dependencies..." -ForegroundColor Yellow
pip install -e ".[dev]"

# Install invoke for task running
Write-Host "📋 Installing invoke task runner..." -ForegroundColor Yellow
pip install invoke

# Run initial tests to verify setup
Write-Host "🧪 Running initial tests..." -ForegroundColor Yellow
python -m pytest tests/ -v

Write-Host ""
Write-Host "🎉 Setup complete! Your MotiveProxy development environment is ready." -ForegroundColor Green
Write-Host ""
Write-Host "To activate the environment in the future, run:" -ForegroundColor Cyan
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To run tests:" -ForegroundColor Cyan
Write-Host "  inv test" -ForegroundColor White
Write-Host ""
Write-Host "To format code:" -ForegroundColor Cyan
Write-Host "  inv format" -ForegroundColor White
Write-Host ""
Write-Host "To run the proxy server:" -ForegroundColor Cyan
Write-Host "  inv run" -ForegroundColor White
Write-Host ""
Write-Host "To see all available tasks:" -ForegroundColor Cyan
Write-Host "  inv --list" -ForegroundColor White
Write-Host ""