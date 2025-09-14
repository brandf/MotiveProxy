# Motive Human-in-the-Loop Proxy

A standalone, stateful proxy server that emulates the OpenAI Chat Completions API to enable bidirectional communication between any two clients that can connect to OpenAI-compatible endpoints.

## The Problem

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



## Features

-   **OpenAI API Compatible:** Exposes a `/v1/chat/completions` endpoint that works with any OpenAI-compatible client
-   **Bidirectional Proxying:** Seamlessly bridges any two clients that can connect to OpenAI-compatible endpoints
-   **Session Management:** Uses the `model` parameter as a session identifier to pair client connections
-   **Concurrent Sessions:** Manages multiple independent client pairs simultaneously
-   **Asynchronous:** Built with FastAPI and asyncio for efficient handling of long-polling requests
-   **No Code Changes Required:** Clients continue using their existing OpenAI API calls without modification
-   **Protocol Agnostic:** Works with any OpenAI-compatible client - chat UIs, programs, scripts, or other services
-   **Standalone:** No dependencies on any specific application or use case. It's a completely generic proxy

## Setup

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
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

### Development Commands

This project uses modern Python tooling with `invoke` for task management:

```bash
# See all available tasks
inv --list

# Run tests
inv test

# Run tests with coverage
inv test-cov

# Format code
inv format-code

# Run linters
inv lint

# Start the proxy server
inv run

# Start in development mode (with auto-reload)
inv dev
```

## Usage

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

## Compatible Clients

MotiveProxy works with **any OpenAI-compatible client**. Popular options include:

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

MotiveProxy could easily be extended to support other LLM chat protocols:
- **Anthropic Claude API** - Similar chat completion format
- **Google Gemini API** - Chat-based interface
- **Custom protocols** - Any HTTP-based chat API

## Generic Design

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

## Use Cases

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

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Server Configuration
MOTIVE_PROXY_HOST=127.0.0.1
MOTIVE_PROXY_PORT=8000
MOTIVE_PROXY_LOG_LEVEL=info

# Session Management
MOTIVE_PROXY_SESSION_TIMEOUT=3600  # seconds
MOTIVE_PROXY_MAX_SESSIONS=100

# CORS Settings (for web clients)
MOTIVE_PROXY_CORS_ORIGINS=*

# Development Settings
MOTIVE_PROXY_DEBUG=false
MOTIVE_PROXY_RELOAD=false
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

## Troubleshooting

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

## Contributing

We welcome contributions! Please see our development guidelines:

1. **Follow TDD**: Write tests first, then implement features
2. **Use modern Python**: Type hints, async/await, proper error handling
3. **Maintain compatibility**: Ensure OpenAI API compatibility
4. **Document changes**: Update README and docstrings

### Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd MotiveProxy
.\setup.ps1  # or ./setup.sh

# Run tests
inv test

# Format code
inv format-code

# Run linters
inv lint
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Examples

See the [examples/](examples/) directory for practical usage examples:

- **[Basic Usage](examples/basic_usage.py)** - Simple Python client example
- **[Game Integration](examples/game_integration.py)** - Human-controlled NPC in a game
- **[Curl Examples](examples/curl_examples.sh)** - Command-line HTTP examples

### Quick Example

```python
import asyncio
import httpx

async def connect_human(session_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/v1/chat/completions",
            json={
                "model": session_id,
                "messages": [{"role": "user", "content": "ping"}]
            }
        )
        return response.json()

# Human connects first
await connect_human("my-session-123")

# Program connects with real message
# Human responds through chat UI
# Response is sent back to program
```

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development setup and modern Python practices.