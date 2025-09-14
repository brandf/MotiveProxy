#!/bin/bash

# MotiveProxy curl examples
# These examples show how to interact with MotiveProxy using curl commands

echo "🚀 MotiveProxy curl Examples"
echo "=========================="
echo ""

# Check if MotiveProxy is running
echo "🔍 Checking if MotiveProxy is running..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ MotiveProxy is running on http://localhost:8000"
else
    echo "❌ MotiveProxy is not running!"
    echo "Start it with: motive-proxy"
    exit 1
fi

echo ""
echo "📋 Example Session: 'demo-session-123'"
echo ""

# Example 1: Human client connects first (sends ping)
echo "🤖 Step 1: Human client connects (sends ping)"
echo "Command:"
echo "curl -X POST http://localhost:8000/v1/chat/completions \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"model\": \"demo-session-123\", \"messages\": [{\"role\": \"user\", \"content\": \"ping\"}]}'"
echo ""

echo "Executing..."
HUMAN_RESPONSE=$(curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "demo-session-123", "messages": [{"role": "user", "content": "ping"}]}')

echo "Response: $HUMAN_RESPONSE"
echo ""

# Wait a moment
sleep 2

# Example 2: Program client connects with real message
echo "💻 Step 2: Program client connects with real message"
echo "Command:"
echo "curl -X POST http://localhost:8000/v1/chat/completions \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"model\": \"demo-session-123\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello! How are you today?\"}]}'"
echo ""

echo "Executing..."
PROGRAM_RESPONSE=$(curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "demo-session-123", "messages": [{"role": "user", "content": "Hello! How are you today?"}]}')

echo "Response: $PROGRAM_RESPONSE"
echo ""

# Wait a moment
sleep 2

# Example 3: Human responds
echo "🤖 Step 3: Human responds"
echo "Command:"
echo "curl -X POST http://localhost:8000/v1/chat/completions \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"model\": \"demo-session-123\", \"messages\": [{\"role\": \"user\", \"content\": \"I am doing great! What can I help you with?\"}]}'"
echo ""

echo "Executing..."
FINAL_RESPONSE=$(curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "demo-session-123", "messages": [{"role": "user", "content": "I am doing great! What can I help you with?"}]}')

echo "Response: $FINAL_RESPONSE"
echo ""

echo "✅ Example completed!"
echo ""
echo "📝 Notes:"
echo "- The human client must connect first and send a 'ping' message"
echo "- Both clients must use the exact same session ID (model name)"
echo "- The proxy forwards messages between the two clients"
echo "- In a real scenario, the human would type responses in a chat UI"
echo ""

# Additional examples
echo "🔧 Additional Examples:"
echo ""

echo "Health check:"
echo "curl http://localhost:8000/health"
echo ""

echo "Different session:"
echo "curl -X POST http://localhost:8000/v1/chat/completions \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"model\": \"another-session\", \"messages\": [{\"role\": \"user\", \"content\": \"ping\"}]}'"
echo ""

echo "With custom parameters:"
echo "curl -X POST http://localhost:8000/v1/chat/completions \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"model\": \"session-456\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}], \"temperature\": 0.7, \"max_tokens\": 100}'"
