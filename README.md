# MotiveProxy

> **A generic proxy server that enables bidirectional communication between any two OpenAI-compatible clients.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**MotiveProxy** is a production-ready, stateful proxy server that emulates multiple LLM API protocols (OpenAI, Anthropic, and more). It enables bidirectional communication between any two clients that can connect to LLM-compatible endpoints - perfect for human-in-the-loop testing, game development, agent frameworks, and more.

## 🎯 **What's New in v0.1.0**

✅ **Streaming Support** - Full Server-Sent Events (SSE) support for real-time streaming  
✅ **Multi-Protocol Support** - OpenAI and Anthropic Claude API compatibility  
✅ **Production Observability** - Structured logging, metrics, and correlation IDs  
✅ **Configuration Management** - Environment variables and CLI configuration  
✅ **Session Management** - Automatic cleanup, TTL, and admin endpoints  
✅ **Comprehensive Testing** - 109 tests with full coverage (Unit + Integration + E2E)  
✅ **LLM-to-LLM E2E Testing** - Real AI conversations through MotiveProxy for validation

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/your-username/MotiveProxy.git
cd MotiveProxy
.\setup.ps1  # Windows PowerShell
# OR
./setup.sh   # Unix/macOS/Linux

# 2. Start the server
motive-proxy

# 3. Test it works
curl http://localhost:8000/health
```

**That's it!** Your proxy server is running and ready to bridge any two OpenAI-compatible clients.

## 💡 Simple Example

Imagine you have a game that normally talks to an AI NPC, but you want to manually control that NPC during development:

```bash
# Game connects to MotiveProxy (thinking it's talking to an AI)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "npc-guard", "messages": [{"role": "user", "content": "ping"}]}'

# You connect with a chat UI using the same session ID
# Game: "You see a troll. What do you do?"
# You: "I attack the troll!"
# Game receives your response as if it came from the AI
```

**No code changes needed** - your game continues using the same OpenAI API calls!

## 🤔 What is MotiveProxy?

MotiveProxy is a **generic bidirectional proxy** that solves the fundamental mismatch between clients that both expect to initiate conversations.

### Why MotiveProxy?

| Problem | Traditional Solution | MotiveProxy Solution |
|---------|---------------------|---------------------|
| **Testing AI interactions** | Modify code, mock responses | Zero code changes, real human responses |
| **Game NPC debugging** | Complex AI debugging tools | Manual control through familiar chat UI |
| **Agent framework testing** | Separate testing infrastructure | Human-in-the-loop testing with existing tools |
| **Quality assurance** | Automated test suites only | Human judgment + automated testing |

### Key Benefits

✅ **Zero Code Changes** - Your existing OpenAI API calls work as-is  
✅ **Familiar Tools** - Use any OpenAI-compatible chat UI  
✅ **Real-time Control** - Manual intervention when needed  
✅ **Generic Design** - Works with any client type or use case  
✅ **Production Ready** - Built with FastAPI and modern Python practices

### The Problem

Consider a system where a program initiates chats with multiple LLMs:

```
Program => LLM
         => LLM  
         => LLM
```

Sometimes you want to manually test or control one of these interactions by having a different client pretend to be an LLM, without changing the original program:

```
Program => LLM
         => Different Client (program thinks it's an LLM)
         => LLM
```

However, there's a fundamental mismatch in communication patterns:

- **Client A** expects to initiate conversations and receive responses
- **Client B** expects to initiate conversations and receive responses

Standard chat clients work like this:
```
Client A => LLM
```

But we need something like this:
```
Client A => MotiveProxy <= Client B
```

## The Solution

MotiveProxy acts as a bidirectional proxy/broker that makes both sides think they're initiating a chat with the other side responding. It uses the OpenAI Chat Completions API protocol because it's widely supported and allows us to use the `model` parameter as a session identifier for pairing connections.

## How It Works

The proxy pairs two clients based on a shared **session ID**, which is passed as the `model` name in the API request.

### Connection Handshake

1. **Client A** connects first (e.g., using Ollama Web UI, Chatbot UI, or any OpenAI-compatible client)
   - Sends their first message (which acts as a "ping" to establish the connection)
   - This initial message is **ignored** by the proxy
   - The proxy holds this connection open, waiting for Client B to connect

2. **Client B** connects using the *same session ID* (model name)
   - Sends the first real prompt (e.g., "You see a troll. What do you do?")
   - The proxy immediately forwards this as the response to Client A's waiting "ping" request

### Message Flow

3. **Client A** sees Client B's prompt and sends their response ("I attack the troll!")
4. **Proxy** receives Client A's response and sends it back to Client B, completing Client B's original request
5. **Client B** receives Client A's response and can continue the conversation
6. This cycle continues for the duration of the session

### Key Design Decisions

- **Client A connects first**: This ensures Client A is ready to receive Client B's initial message
- **First Client A message ignored**: Acts as a connection handshake without interfering with the actual conversation
- **Model name as session ID**: Leverages existing OpenAI API patterns for session management
- **Bidirectional proxying**: Both sides think they're talking directly to the other
- **Protocol agnostic**: MotiveProxy doesn't know or care what type of clients connect to it



## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [💡 Simple Example](#-simple-example)
- [🤔 What is MotiveProxy?](#-what-is-motiveproxy)
- [✨ Features](#-features)
- [🎯 Use Cases](#-use-cases)
- [⚙️ Setup](#️-setup)
- [📖 Usage](#-usage)
- [🔧 Configuration](#-configuration)
- [🛠️ Troubleshooting](#️-troubleshooting)
- [📚 Examples](#-examples)
- [🤖 For LLM Coding Agents](#-for-llm-coding-agents)
- [📄 License](#-license)

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔌 **Multi-Protocol Support** | OpenAI Chat Completions + Anthropic Claude APIs |
| 🔄 **Bidirectional Proxy** | Bridges two clients seamlessly |
| 📡 **Streaming Support** | Real-time Server-Sent Events (SSE) streaming |
| 🎯 **Session Management** | Uses `model` parameter as session ID with TTL |
| ⚡ **Concurrent Sessions** | Handles multiple client pairs simultaneously |
| 🚀 **Async & Fast** | Built with FastAPI and asyncio |
| 🔧 **Zero Code Changes** | Clients use existing LLM API calls |
| 📊 **Production Observability** | Structured logging, metrics, correlation IDs |
| ⚙️ **Configuration Management** | Environment variables and CLI configuration |
| 🛡️ **Admin Endpoints** | Session monitoring and health checks |
| 🔒 **Security & Rate Limiting** | IP-based rate limiting, payload limits, CORS |
| 🔑 **Authentication** | Optional API key authentication |
| 📦 **Standalone** | No dependencies on specific applications |

## ⚙️ Setup

### Prerequisites

- **Python 3.8+** - [Download here](https://www.python.org/downloads/)
- **Git** - [Download here](https://git-scm.com/downloads)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/MotiveProxy.git
   cd MotiveProxy
   ```

2. **Run the setup script:**
   ```bash
   # Windows PowerShell
   .\setup.ps1
   
   # Unix/macOS/Linux
   ./setup.sh
   ```

3. **Activate the virtual environment:**
   ```bash
   # Windows
   .\venv\Scripts\Activate.ps1
   
   # Unix/macOS/Linux
   source venv/bin/activate
   ```

### Verify Installation

```bash
# Check the CLI works
motive-proxy --help

# Run tests to verify everything works
inv test
```

### Development Commands

This project uses modern Python tooling with `invoke` for task management:

```bash
# See all available tasks
inv --list

# Run tests
inv test

# Run tests with coverage
inv test-cov

# Run E2E tests (separate from main test suite)
pytest -m e2e

# Run E2E tool directly
motive-proxy-e2e --scenario basic-handshake --turns 3

# Format code
inv format-code

# Run linters
inv lint

# Start the proxy server
inv run

# Start in development mode (with auto-reload)
inv dev
```

## 📖 Usage

### Starting the Proxy Server

```bash
# Basic usage
motive-proxy

# Custom host/port
motive-proxy --host 0.0.0.0 --port 8080

# Development mode with auto-reload
motive-proxy --reload --log-level debug
```

### API Endpoints

- **Health Check:** `GET /health`
- **Chat Completions:** `POST /v1/chat/completions` (OpenAI compatible)
- **Anthropic Messages:** `POST /v1/messages` (Anthropic Claude compatible)
- **Metrics:** `GET /metrics` (Observability metrics)
- **Admin Sessions:** `GET /admin/sessions` (Session monitoring)

### Example Usage

1. **Client A connects first** (using any OpenAI-compatible client):
   ```bash
   curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "session-123", "messages": [{"role": "user", "content": "ping"}]}'
   ```

2. **Client B connects** (using the same session ID):
   ```bash
   curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "session-123", "messages": [{"role": "user", "content": "Hello, how are you?"}]}'
   ```

3. **Client A responds**, and the response is sent back to Client B.

### Streaming Support

MotiveProxy supports real-time streaming with Server-Sent Events (SSE):

```bash
# Enable streaming
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "session-123", "messages": [{"role": "user", "content": "Hello"}], "stream": true}'

# Response streams word-by-word:
# data: {"id": "chatcmpl-...", "object": "chat.completion.chunk", "choices": [{"delta": {"content": "Hello"}}]}
# data: {"id": "chatcmpl-...", "object": "chat.completion.chunk", "choices": [{"delta": {"content": " world"}}]}
# data: [DONE]
```

### Multi-Protocol Support

MotiveProxy supports multiple LLM APIs through protocol adapters:

```bash
# OpenAI Chat Completions API
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "session-123", "messages": [{"role": "user", "content": "Hello"}]}'

# Anthropic Claude Messages API  
curl -X POST http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -d '{"model": "session-123", "messages": [{"role": "user", "content": "Hello"}]}'
```

## 🔌 Compatible Clients

MotiveProxy works with **any LLM-compatible client**. Popular options include:

### Chat Interfaces
- **Ollama Web UI** - Simple, clean interface
- **Chatbot UI** - Feature-rich chat interface
- **OpenAI Playground** - Official OpenAI interface
- **Custom web clients** - Any application that can connect to OpenAI's API

### Programmatic Clients
- **Python scripts** using `httpx`, `requests`, or `openai` library
- **Node.js applications** using `openai` or `axios`
- **Command-line tools** like `curl` or custom scripts
- **Other services** that can make HTTP requests to OpenAI endpoints

### Protocol Extensions

MotiveProxy supports multiple LLM protocols with a flexible adapter system:
- **OpenAI Chat Completions API** - Full compatibility with streaming
- **Anthropic Claude API** - Complete Claude Messages API support
- **Extensible Architecture** - Easy to add Google Gemini, Cohere, or custom protocols

## 🎯 Generic Design

MotiveProxy is **completely generic** and doesn't know or care about:

- **What type of clients connect** - Could be humans, programs, scripts, services, etc.
- **What the clients are doing** - Could be games, business logic, testing, research, etc.
- **The content of messages** - Just forwards messages between clients
- **The purpose of the session** - Could be debugging, testing, human-in-the-loop, etc.

The proxy only cares about:
- **Session pairing** - Matching clients by session ID
- **Message forwarding** - Bidirectional communication between paired clients
- **Protocol compliance** - Following OpenAI Chat Completions API format

This makes MotiveProxy useful for any scenario where you need to bridge two clients that expect to initiate conversations.

## 🎯 Use Cases

MotiveProxy is perfect for:

### 🎮 **Game Development & Testing**
- **AI-driven games** where you want to manually control NPCs during development
- **Testing game logic** by replacing AI players with human decision-making
- **Debugging AI behavior** by stepping through interactions manually

### 🤖 **Agent Framework Development**
- **Testing agent workflows** by manually controlling one agent in a multi-agent system
- **Debugging agent interactions** by stepping through conversations
- **Prototyping agent behavior** before implementing full AI logic

### 🧪 **Simulation & Testing**
- **Human-in-the-loop simulations** for research or testing
- **Quality assurance** for AI-powered applications
- **User experience testing** of AI interactions

### 🔧 **Development & Debugging**
- **Manual testing** of applications that normally use LLMs
- **Debugging AI integration** without changing application code
- **Prototyping** human-AI interaction patterns

## 🔒 Security Features

MotiveProxy includes comprehensive security features for production deployments:

### Rate Limiting
- **Per-IP limits**: Configurable requests per minute/hour
- **Burst protection**: Prevents rapid-fire requests
- **Automatic cleanup**: Removes old rate limit entries

### Payload Protection
- **Size limits**: Configurable maximum request size (default: 1MB)
- **413 responses**: Clear error messages for oversized requests

### CORS Configuration
- **Origin control**: Whitelist specific domains
- **Preflight support**: Handles OPTIONS requests automatically
- **Credential support**: Allows authenticated requests

### Authentication (Optional)
- **API key auth**: Simple header-based authentication
- **Multiple keys**: Support for multiple valid API keys
- **Configurable**: Enable/disable via environment variables

## 🔧 Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Server Configuration
MOTIVE_PROXY_HOST=127.0.0.1
MOTIVE_PROXY_PORT=8000
MOTIVE_PROXY_LOG_LEVEL=info
MOTIVE_PROXY_DEBUG=false

# Session Management
MOTIVE_PROXY_HANDSHAKE_TIMEOUT_SECONDS=30
MOTIVE_PROXY_TURN_TIMEOUT_SECONDS=30
MOTIVE_PROXY_SESSION_TTL_SECONDS=3600
MOTIVE_PROXY_MAX_SESSIONS=100
MOTIVE_PROXY_CLEANUP_INTERVAL_SECONDS=60

# Security & Rate Limiting
MOTIVE_PROXY_ENABLE_RATE_LIMITING=true
MOTIVE_PROXY_RATE_LIMIT_REQUESTS_PER_MINUTE=60
MOTIVE_PROXY_RATE_LIMIT_REQUESTS_PER_HOUR=1000
MOTIVE_PROXY_RATE_LIMIT_BURST_LIMIT=10
MOTIVE_PROXY_MAX_PAYLOAD_SIZE=1048576
MOTIVE_PROXY_CORS_ORIGINS=["*"]

# Authentication (Optional)
MOTIVE_PROXY_ENABLE_API_KEY_AUTH=false
MOTIVE_PROXY_API_KEY_HEADER=X-API-Key
MOTIVE_PROXY_VALID_API_KEYS=[]

# Observability
MOTIVE_PROXY_ENABLE_METRICS=true
```

> **Note:** Copy `.env.example` to `.env` and modify as needed (if available in your version).

### Advanced Usage

#### Custom Session Management

```python
from motive_proxy.session_manager import SessionManager

# Create custom session manager
manager = SessionManager()

# Create a session with custom timeout
session = manager.create_session("my-session")
```

#### Programmatic API Usage

```python
import httpx

async def connect_as_human(session_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/v1/chat/completions",
            json={
                "model": session_id,
                "messages": [{"role": "user", "content": "ping"}]
            }
        )
        return response.json()

async def connect_as_program(session_id: str, message: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/v1/chat/completions",
            json={
                "model": session_id,
                "messages": [{"role": "user", "content": message}]
            }
        )
        return response.json()
```

## 🛠️ Troubleshooting

### Common Issues

#### **"Session not found" errors**
- Ensure both clients use the **exact same session ID** (model name)
- Check that the human client connected first
- Verify the session hasn't timed out

#### **Connection timeouts**
- Human client must connect first and send initial "ping" message
- Check network connectivity between clients and proxy
- Verify proxy server is running and accessible

#### **Chat UI compatibility issues**
- Ensure your chat UI supports OpenAI Chat Completions API
- Check that the UI can handle long-polling requests
- Verify CORS settings if using web-based clients

### Debug Mode

Run with debug logging to see detailed session information:

```bash
motive-proxy --log-level debug
```

### Health Check

Monitor proxy health:

```bash
curl http://localhost:8000/health
```

## 🤝 Contributing

We welcome contributions! Please see our development guidelines:

1. **Follow TDD**: Write tests first, then implement features
2. **Use modern Python**: Type hints, async/await, proper error handling
3. **Maintain compatibility**: Ensure OpenAI API compatibility
4. **Document changes**: Update README and docstrings

### Development Setup

```bash
# Clone and setup
git clone https://github.com/your-username/MotiveProxy.git
cd MotiveProxy
.\setup.ps1  # or ./setup.sh

# Run tests
inv test

# Format code
inv format-code

# Run linters
inv lint
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Examples

### 🚀 Quick Examples

| Example | Description | Link |
|---------|-------------|------|
| 🐍 **Python Client** | Simple programmatic usage | [basic_usage.py](examples/basic_usage.py) |
| 🎮 **Game Integration** | Human-controlled NPC in a game | [game_integration.py](examples/game_integration.py) |
| 💻 **Command Line** | HTTP examples with curl | [curl_examples.sh](examples/curl_examples.sh) |

### 💡 Python Example

```python
import asyncio
import httpx

async def connect_client(session_id: str, message: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/v1/chat/completions",
            json={
                "model": session_id,
                "messages": [{"role": "user", "content": message}]
            }
        )
        return response.json()

# Client A connects first
await connect_client("my-session-123", "ping")

# Client B connects with real message
response = await connect_client("my-session-123", "Hello!")
print(response["choices"][0]["message"]["content"])
```

### 🎮 Game Development Example

Perfect for testing game NPCs manually:

```python
# Your game normally does this:
# response = openai_client.chat.completions.create(
#     model="gpt-4",
#     messages=[{"role": "user", "content": "You see a troll. What do you do?"}]
# )

# With MotiveProxy, just change the endpoint:
response = openai_client.chat.completions.create(
    model="npc-guard-session-123",  # Session ID
    messages=[{"role": "user", "content": "You see a troll. What do you do?"}],
    base_url="http://localhost:8000/v1"  # MotiveProxy endpoint
)
# Now a human can respond through their chat UI!
```

## 🤖 For LLM Coding Agents

**⚠️ IMPORTANT: If you are an LLM coding agent working on this project, you MUST read [AGENT.md](AGENT.md) immediately after this README.**

[AGENT.md](AGENT.md) contains:
- **Mandatory TDD workflow** (7-step process)
- **Confidence analysis requirements** (detailed reporting before manual testing)
- **Durable testing guidelines** (no ad-hoc curl commands!)
- **Code quality standards** and best practices
- **Emoji usage guidelines** for documentation
- **Project-specific patterns** and expectations

**🚀 Quick Start for Agents:**
1. Read this README (you're here!)
2. **📋 Read [AGENT.md](AGENT.md) immediately** - This is mandatory!
3. Follow the TDD workflow for all changes
4. Provide confidence analysis reports
5. Use durable testing methods (pytest, not curl)

## 🧪 E2E Testing with Real LLMs

MotiveProxy includes powerful E2E testing capabilities that allow you to test real LLM-to-LLM conversations through the proxy.

### 🚀 Quick Setup

1. **Set up environment file:**
   ```bash
   python setup_env.py
   ```

2. **Configure API keys in `.env`:**
   ```bash
   # Copy template and edit
   cp env.template .env
   # Edit .env and add your API keys
   ```

3. **Run LLM-to-LLM conversation test:**
   ```bash
   motive-proxy-e2e --use-llms
   ```

### 🔑 Supported LLM Providers

- **Google Gemini** (recommended for testing)
- **OpenAI GPT** 
- **Anthropic Claude**
- **Cohere Command**

### 🎯 Example: Two Different Models Talking

```bash
# Gemini vs Claude conversation
motive-proxy-e2e --use-llms \
  --llm-provider-a google --llm-model-a gemini-2.5-flash \
  --llm-provider-b anthropic --llm-model-b claude-3-sonnet \
  --conversation-prompt "Let's debate the future of AI safety" \
  --turns 5
```

### 🎯 Example: Multi-Turn Conversation

```bash
# 5-turn conversation with context management
motive-proxy-e2e --use-llms \
  --llm-provider-a google --llm-model-a gemini-2.5-flash \
  --llm-provider-b google --llm-model-b gemini-2.5-flash \
  --conversation-prompt "Let's discuss AI safety" \
  --turns 5 \
  --max-context-messages 8 \
  --system-prompt "Be concise and thoughtful"
```

### 📊 Test Results

E2E tests generate comprehensive reports in `./e2e_test_results/` including:
- Conversation logs
- Performance metrics  
- Error analysis
- LLM response quality

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development setup and modern Python practices.