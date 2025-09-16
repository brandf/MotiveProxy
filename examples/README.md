# MotiveProxy Examples

This directory contains practical examples showing how to use MotiveProxy in different scenarios.

## Examples Overview

### 1. Basic Usage (`basic_usage.py`)
Demonstrates the fundamental concept of MotiveProxy with simple Python clients.

**What it shows:**
- How to connect both human and program clients
- Basic message flow between clients
- Error handling and connection management

**Run it:**
```bash
# Start MotiveProxy first
motive-proxy

# In another terminal, run the example
python examples/basic_usage.py
```

### 2. Game Integration (`game_integration.py`)
Shows how MotiveProxy can be used in a game scenario where a human controls an NPC.

**What it shows:**
- Game engine integration
- Human-controlled NPCs
- Context-aware interactions
- Game state management

**Run it:**
```bash
# Start MotiveProxy first
motive-proxy

# In another terminal, run the game example
python examples/game_integration.py
```

### 3. Curl Examples (`curl_examples.sh`)
Command-line examples using curl to interact with MotiveProxy.

**What it shows:**
- HTTP API usage
- Session management
- Message flow
- Error handling

**Run it:**
```bash
# Make executable and run
chmod +x examples/curl_examples.sh
./examples/curl_examples.sh
```

### 4. E2E Testing with Real LLMs
Advanced testing examples using real AI models to validate MotiveProxy functionality.

**What it shows:**
- Real AI-to-AI conversations through MotiveProxy
- Smart context window management and optimization
- Multi-turn conversation validation (5-20 turns)
- Performance optimization and reliability testing
- Cross-platform compatibility validation

**Run it:**
```bash
# Set up API keys first
python setup_env.py

# Basic LLM-to-LLM test
motive-proxy-e2e --use-llms --turns 5

# Advanced configuration with performance optimization
motive-proxy-e2e --use-llms \
  --llm-provider-a google --llm-model-a gemini-2.5-flash \
  --llm-provider-b anthropic --llm-model-b claude-3-sonnet \
  --conversation-prompt "Discuss the future of AI" \
  --turns 20 --max-context-messages 6 --max-response-length 1000

# Test with different model combinations
motive-proxy-e2e --use-llms \
  --llm-provider-a google --llm-model-a gemini-2.5-flash \
  --llm-provider-b google --llm-model-b gemini-2.5-flash \
  --conversation-prompt "Debate AI safety" \
  --turns 10 --system-prompt "Be concise and thoughtful"

# Test concurrent sessions
motive-proxy-e2e --use-llms --concurrent 3 --turns 5
```

## Common Patterns

### Session Management
All examples use a session ID (passed as the `model` parameter) to pair clients:

```python
# Both clients use the same session ID
session_id = "my-session-123"

# Human client connects first
await client.send_message(session_id, "ping")

# Program client connects with real message
await client.send_message(session_id, "Hello, how are you?")
```

### Error Handling
Always handle connection errors and timeouts:

```python
try:
    response = await client.send_message(session_id, message)
except httpx.ConnectError:
    print("Could not connect to MotiveProxy")
except httpx.TimeoutException:
    print("Request timed out")
```

### Message Format
Messages follow the OpenAI Chat Completions format:

```python
{
    "model": "session-id",
    "messages": [
        {"role": "user", "content": "Your message here"}
    ]
}
```

## Integration Ideas

### Chat Applications
- **Slack/Discord bots** with human override
- **Customer service** with human escalation
- **Educational tools** with human tutoring

### Game Development
- **NPCs** controlled by humans during development
- **Testing** game logic with human players
- **Debugging** AI behavior step-by-step

### Agent Frameworks
- **Multi-agent systems** with human supervision
- **Workflow testing** with human intervention
- **Prototyping** agent interactions

### Research & Simulation
- **Human-in-the-loop** research studies
- **Behavioral analysis** of AI interactions
- **User experience** testing

### Human Chat Client Integration
- **Embeddable chat interfaces** for human players
- **Modern UI frameworks** (React, Vue, SvelteKit)
- **Cross-platform compatibility** (Windows, macOS, Linux)
- **Real-time communication** with MotiveProxy

## Troubleshooting Examples

### Connection Issues
```bash
# Check if MotiveProxy is running
curl http://localhost:8000/health

# Test basic connectivity
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "test", "messages": [{"role": "user", "content": "ping"}]}'
```

### Session Problems
- Ensure both clients use the **exact same session ID**
- Human client must connect **first**
- Check for typos in session IDs

### Timeout Issues
- Increase timeout values for long-running requests
- Check network connectivity
- Verify MotiveProxy server is responsive

### Performance Optimization
- Use smart context management (6-8 messages for Gemini)
- Enable response caching for repeated queries
- Set response length limits (1000-2000 characters)
- Use retry logic with exponential backoff
- Monitor response times and throughput

## Contributing Examples

We welcome new examples! When contributing:

1. **Follow the existing patterns** in the current examples
2. **Include clear documentation** explaining what the example demonstrates
3. **Add error handling** for common failure cases
4. **Test your examples** before submitting
5. **Update this README** with your new example

### Example Template
```python
"""
Brief description of what this example demonstrates.

This example shows how to...
"""

import asyncio
import httpx

async def main():
    """Main example function."""
    # Your example code here
    pass

if __name__ == "__main__":
    print("Make sure MotiveProxy is running: motive-proxy")
    asyncio.run(main())
```

## Getting Help

If you have questions about these examples:

1. **Check the main README** for general MotiveProxy information
2. **Look at the DEVELOPMENT.md** for development setup
3. **Run the examples** to see them in action
4. **Open an issue** if you find bugs or need help

Happy coding! 🚀
