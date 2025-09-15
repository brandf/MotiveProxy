#!/usr/bin/env python3
"""Test LLM connection directly."""

import asyncio
from src.motive_proxy.testing.llm_client import create_llm_client, LLMTestClient

async def test_llm():
    """Test LLM connection."""
    try:
        print("Creating LLM client...")
        client = create_llm_client('google', 'gemini-2.5-flash')
        print("✅ LLM client created")
        
        print("Creating LLM test client...")
        llm_client = LLMTestClient(client)
        print("✅ LLM test client created")
        
        print("Sending test message...")
        response = await llm_client.process_message('Hello, how are you?')
        print(f"✅ Response received: {response[:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm())
