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

MotiveProxy includes advanced E2E testing capabilities that validate real AI-to-AI conversations through the proxy. This is crucial for ensuring MotiveProxy works correctly with actual LLM APIs, not just simulated clients.

### 🚀 Quick Setup
1. **Configure API keys:**
   ```bash
   python setup_env.py  # Creates .env template
   # Edit .env with your API keys
   ```

2. **Run LLM-to-LLM tests:**
   ```bash
   # Basic 5-turn conversation
   motive-proxy-e2e --use-llms --turns 5
   
   # Advanced configuration with performance optimization
   motive-proxy-e2e --use-llms \
     --llm-provider-a google --llm-model-a gemini-2.5-flash \
     --llm-provider-b anthropic --llm-model-b claude-3-sonnet \
     --conversation-prompt "Discuss AI safety" \
     --turns 20 --max-context-messages 6 --max-response-length 1000
   ```

### ⚡ Performance Features
- **Smart Context Management**: Automatically truncates conversation history to prevent token limit issues
- **Response Caching**: Caches identical responses to reduce API calls and improve performance
- **Retry Logic**: Exponential backoff for transient failures (timeouts, network issues)
- **Response Length Limits**: Prevents overly verbose LLM responses that slow down testing
- **Real-time Metrics**: Tracks response times, throughput, and performance bottlenecks

### 🔑 Supported LLM Providers
- **Google Gemini** (recommended - free credits available, fast responses)
- **OpenAI GPT** (comprehensive API support)
- **Anthropic Claude** (high-quality responses)
- **Cohere Command** (alternative provider)

### 🧪 Advanced Testing Scenarios
```bash
# Test different model combinations
motive-proxy-e2e --use-llms \
  --llm-provider-a google --llm-model-a gemini-2.5-flash \
  --llm-provider-b anthropic --llm-model-b claude-3-sonnet \
  --conversation-prompt "Debate the ethics of AI development" \
  --turns 10

# Test with performance optimization
motive-proxy-e2e --use-llms \
  --llm-provider-a google --llm-model-a gemini-2.5-flash \
  --llm-provider-b google --llm-model-b gemini-2.5-flash \
  --conversation-prompt "Discuss machine learning" \
  --turns 20 --max-context-messages 6 --max-response-length 1000 \
  --system-prompt "Be concise and focused"

# Test concurrent sessions
motive-proxy-e2e --use-llms --concurrent 3 --turns 5
```

### 📊 Test Results & Analysis
E2E tests generate comprehensive reports including:
- **Complete conversation logs** with all messages exchanged
- **Performance metrics** (response times, throughput, error rates)
- **Context usage statistics** (token usage, truncation events)
- **Error analysis** and debugging information
- **LLM response quality** assessment
- **Cross-platform compatibility** validation

### 🔧 Technical Architecture
- **Independent Subprocesses**: Real MotiveProxy server + real LLM client processes
- **Network Communication**: Actual HTTP/WebSocket connections (not mocked)
- **Cross-Platform**: Windows (`CREATE_NEW_PROCESS_GROUP`) and Unix subprocess handling
- **Comprehensive Logging**: All processes log to centralized `/logs/` directory
- **Cleanup Management**: Proper process termination and resource cleanup

## 🎨 Human Chat Client UI Integration

MotiveProxy is designed to work with **any LLM-compatible chat interface**. For human players, we recommend these modern, embeddable chat client packages:

### 🏆 **Recommended Chat Client Packages**

#### **LobeChat** ⭐ **Best Overall**
- **Framework**: SvelteKit (embeddable in React/Vue)
- **Features**: Modern UI, multi-provider support, Knowledge Base for RAG
- **Integration**: Component embedding or iframe
- **Benefits**: Voice interaction, file uploads, conversation history

#### **LibreChat** ⭐ **Most Feature-Rich**
- **Framework**: React-based
- **Features**: ChatGPT-like interface, multi-user support, agent system
- **Integration**: Full React app embedding
- **Benefits**: Enterprise features, conversation persistence, user authentication

#### **Open WebUI** ⭐ **Lightweight & Fast**
- **Framework**: Cross-platform, mobile-friendly
- **Features**: Minimalist design, offline capabilities
- **Integration**: Widget embedding
- **Benefits**: Fast, lightweight, multi-language support

### 🔧 **Integration Approaches**

#### **Component Embedding**
```jsx
// React example
import { LobeChat } from '@lobechat/react'

function MyWebsite() {
  return (
    <LobeChat 
      apiEndpoint="https://your-motive-proxy.com/v1/chat/completions"
      apiKey="your-api-key"
      model="your-session-id"
    />
  )
}
```

#### **Custom Integration**
```jsx
// Custom chat component using existing libraries
import { ChatContainer, MessageList, Message, MessageInput } from '@chatscope/chat-ui-kit-react'

function MotiveProxyChat() {
  const [messages, setMessages] = useState([])
  
  const sendMessage = async (message) => {
    const response = await fetch('https://your-motive-proxy.com/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [...messages, { role: 'user', content: message }],
        model: 'your-session-id'
      })
    })
    // Handle response...
  }
  
  return (
    <ChatContainer>
      <MessageList>
        {messages.map(msg => <Message key={msg.id} model={msg} />)}
      </MessageList>
      <MessageInput onSend={sendMessage} />
    </ChatContainer>
  )
}
```

### 📦 **Embeddable Component Libraries**

- **React**: `@chatscope/chat-ui-kit-react`, `react-chat-elements`, `@microsoft/fluentui-react-chat`
- **Vue**: `vue-chat-scroll`, `vue-chat-component`

## Why This Approach?

1. **Standards Compliance** - Follows PEP 518/621 for modern Python packaging
2. **Developer Experience** - Clear, consistent commands and workflows
3. **Code Quality** - Automated checks prevent common issues
4. **Maintainability** - Type hints and tests make code self-documenting
5. **Cross-platform** - Works on Windows, macOS, and Linux
6. **Generic Design** - Works with any LLM-compatible client, not just specific applications

This setup provides a professional, maintainable foundation for the MotiveProxy project.
