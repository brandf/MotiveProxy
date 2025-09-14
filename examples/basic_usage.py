"""
Basic usage example for MotiveProxy.

This example demonstrates how to use MotiveProxy programmatically
to connect any two OpenAI-compatible clients.
"""

import asyncio
import httpx
import json
from typing import Dict, Any


class MotiveProxyClient:
    """Simple client for interacting with MotiveProxy."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def send_message(
        self, 
        session_id: str, 
        message: str, 
        role: str = "user"
    ) -> Dict[str, Any]:
        """Send a message to the proxy."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": session_id,
                    "messages": [{"role": role, "content": message}]
                },
                timeout=30.0
            )
            return response.json()


async def client_a_example():
    """Example of how Client A would connect."""
    client = MotiveProxyClient()
    session_id = "example-session-123"
    
    print("🤖 Client A: Connecting to MotiveProxy...")
    
    # Client A sends initial "ping" message
    response = await client.send_message(session_id, "ping")
    print(f"🤖 Client A: Received response: {response}")
    
    # In a real scenario, Client A could be a chat UI, script, or any other client
    # For this example, we'll simulate a response
    await asyncio.sleep(1)  # Simulate processing time
    
    client_a_response = "I'm doing great! How can I help you today?"
    print(f"🤖 Client A: Sending response: {client_a_response}")
    
    response = await client.send_message(session_id, client_a_response)
    print(f"🤖 Client A: Final response: {response}")


async def client_b_example():
    """Example of how Client B would connect."""
    client = MotiveProxyClient()
    session_id = "example-session-123"
    
    print("💻 Client B: Waiting for Client A to connect...")
    await asyncio.sleep(2)  # Wait for Client A to connect first
    
    print("💻 Client B: Sending initial message...")
    response = await client.send_message(
        session_id, 
        "Hello! I'm a program that normally talks to an AI. How are you?"
    )
    print(f"💻 Client B: Received response: {response}")
    
    # Extract Client A's response from the OpenAI format
    if "choices" in response and len(response["choices"]) > 0:
        client_a_message = response["choices"][0]["message"]["content"]
        print(f"💻 Client B: Client A said: '{client_a_message}'")
        
        # Client B continues the conversation
        follow_up = "That's wonderful! Can you help me solve a problem?"
        print(f"💻 Client B: Sending follow-up: {follow_up}")
        
        response = await client.send_message(session_id, follow_up)
        print(f"💻 Client B: Final response: {response}")


async def main():
    """Run both clients concurrently to simulate the proxy behavior."""
    print("🚀 MotiveProxy Example")
    print("=" * 50)
    
    # Run both clients concurrently
    await asyncio.gather(
        client_a_example(),
        client_b_example()
    )
    
    print("\n✅ Example completed!")


if __name__ == "__main__":
    print("Make sure MotiveProxy is running on http://localhost:8000")
    print("Start it with: motive-proxy")
    print()
    
    try:
        asyncio.run(main())
    except httpx.ConnectError:
        print("❌ Could not connect to MotiveProxy.")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
