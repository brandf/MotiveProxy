# Development Guide

This guide covers the modern Python development practices used in MotiveProxy.

## Modern Python Project Structure

MotiveProxy follows current Python best practices:

- **`pyproject.toml`** - Modern Python packaging standard (PEP 518/621)
- **`src/` layout** - Clean separation of source code from tests
- **`invoke` tasks** - Python-native task runner (replaces Makefiles)
- **Pre-commit hooks** - Automated code quality checks
- **Type hints** - Full type annotation support
- **Modern testing** - pytest with async support

## Quick Start

1. **Set up the environment:**
   ```bash
   # Windows PowerShell
   .\setup.ps1
   
   # Unix/macOS/Linux
   ./setup.sh
   ```

2. **Activate the virtual environment:**
   ```bash
   # Windows
   .\venv\Scripts\Activate.ps1
   
   # Unix/macOS/Linux
   source venv/bin/activate
   ```

## Development Commands

All development tasks are managed through `invoke`:

```bash
# See all available tasks
inv --list

# Run tests
inv test

# Run tests with coverage
inv test-cov

# Format code (black + isort)
inv format

# Run linters (flake8 + mypy)
inv lint

# Run the server
inv run

# Run in development mode (with auto-reload)
inv dev

# Clean up build artifacts
inv clean

# Set up pre-commit hooks
inv pre-commit-install

# Run E2E tests with real LLMs
motive-proxy-e2e --use-llms --turns 5
```

## Project Structure

```
MotiveProxy/
├── src/motive_proxy/          # Source code
│   ├── __init__.py
│   ├── app.py                 # FastAPI application
│   ├── cli.py                 # Command-line interface
│   ├── session_manager.py     # Session management
│   ├── routes/                # API routes
│   └── testing/               # E2E testing tools
│       ├── e2e_cli.py         # E2E test runner
│       ├── test_client_runner.py # LLM test client
│       └── llm_client.py      # LLM integration
├── tests/                     # Test code
├── pyproject.toml             # Project configuration
├── requirements.txt           # Core dependencies
├── tasks.py                   # Invoke task definitions
├── .pre-commit-config.yaml    # Pre-commit hooks
└── setup.ps1/setup.sh         # Setup scripts
```

## Key Modern Python Features

### 1. pyproject.toml Configuration
- Single source of truth for project metadata
- Modern dependency management
- Tool configuration (black, isort, pytest, mypy)

### 2. Type Hints
All functions include type annotations:
```python
def create_session(self, session_id: str) -> Session:
    """Create a new session with the given ID."""
```

### 3. Async/Await Support
Built with FastAPI and asyncio for modern async Python:
```python
@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Handle async chat completions."""
```

### 4. Pre-commit Hooks
Automated code quality checks on every commit:
- Code formatting (black, isort)
- Linting (flake8, mypy)
- Security checks
- YAML validation

## Testing Strategy

Following Test-Driven Development (TDD):

1. **Write tests first** - Define expected behavior
2. **Run tests** - See them fail (Red)
3. **Write minimal code** - Make tests pass (Green)
4. **Refactor** - Improve code while keeping tests green

### Test Structure
- `tests/conftest.py` - Shared fixtures and configuration
- `tests/test_*.py` - Test modules for each component
- Async test support with `pytest-asyncio`

### Running Tests
```bash
# Run all tests
inv test

# Run with verbose output
inv test --verbose

# Run with coverage
inv test-cov
```

## Code Quality

### Formatting
- **Black** - Consistent code formatting
- **isort** - Import sorting

### Linting
- **flake8** - Style guide enforcement
- **mypy** - Static type checking

### Pre-commit
Automatically runs quality checks before commits:
```bash
inv pre-commit-install  # One-time setup
# Now all commits automatically run checks
```

## E2E Testing with Real LLMs

MotiveProxy includes advanced E2E testing capabilities that validate real AI-to-AI conversations:

### Setup
1. **Configure API keys:**
   ```bash
   python setup_env.py  # Creates .env template
   # Edit .env with your API keys
   ```

2. **Run LLM-to-LLM tests:**
   ```bash
   # Basic 5-turn conversation
   motive-proxy-e2e --use-llms --turns 5
   
   # Advanced configuration
   motive-proxy-e2e --use-llms \
     --llm-provider-a google --llm-model-a gemini-2.5-flash \
     --llm-provider-b anthropic --llm-model-b claude-3-sonnet \
     --conversation-prompt "Discuss AI safety" \
     --turns 10 --max-context-messages 12
   ```

### Features
- **Real AI Models**: Uses actual LLM APIs (Google Gemini, OpenAI, Anthropic, Cohere)
- **Context Management**: Smart conversation history truncation
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Comprehensive Logging**: Detailed conversation analysis
- **Performance Metrics**: Response times and throughput tracking

## Why This Approach?

1. **Standards Compliance** - Follows PEP 518/621 for modern Python packaging
2. **Developer Experience** - Clear, consistent commands and workflows
3. **Code Quality** - Automated checks prevent common issues
4. **Maintainability** - Type hints and tests make code self-documenting
5. **Cross-platform** - Works on Windows, macOS, and Linux

This setup provides a professional, maintainable foundation for the MotiveProxy project.
