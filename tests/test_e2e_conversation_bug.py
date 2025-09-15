"""Integration test that captures the LLM conversation bug."""

import pytest
import asyncio
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from motive_proxy.testing.test_client_runner import _run_llm_conversation
from motive_proxy.testing.llm_client import LLMTestClient
from langchain_openai import ChatOpenAI
from unittest.mock import Mock, AsyncMock


class TestE2EConversationBug:
    """Test that captures the actual LLM conversation bug."""
    
    @pytest.mark.asyncio
    async def test_llm_conversation_flow_bug(self):
        """Test that reproduces the actual conversation bug."""
        # Mock LLM that responds differently to different inputs
        mock_llm = AsyncMock()
        
        # Mock responses based on input
        def mock_ainvoke(messages):
            if not messages:
                return Mock(content="No messages")
            
            last_message = messages[-1].content
            
            if "Let's test context management" in last_message:
                return Mock(content="Hello! I'm ready to test context management.")
            elif "Hello! I'm ready to test context management" in last_message:
                return Mock(content="Got it! Your favorite color is blue. I'll remember that.")
            elif "Got it! Your favorite color is blue" in last_message:
                return Mock(content="Yes, I've got it! Your favorite color is blue. Is there anything else I can help you with today?")
            else:
                return Mock(content=f"Unknown message: {last_message}")
        
        mock_llm.ainvoke.side_effect = mock_ainvoke
        
        # Mock ChatOpenAI client to simulate MotiveProxy routing
        mock_client = AsyncMock()
        
        # Simulate MotiveProxy session protocol:
        # 1. Client A sends message → Client B receives it
        # 2. Client B sends message → Client A receives it
        
        # Track the conversation state
        client_a_message = None
        client_b_message = None
        
        def mock_client_ainvoke(messages):
            nonlocal client_a_message, client_b_message
            
            if not messages:
                return Mock(content="No messages")
            
            last_message = messages[-1].content
            
            # Client A sends "Hello! I'm ready to test context management."
            if "Hello! I'm ready to test context management" in last_message:
                client_a_message = last_message
                return Mock(content="Hello! I'm ready to test context management.")
            
            # Client B sends "Ready to chat!" - this should return Client A's message
            elif "Ready to chat!" in last_message:
                return Mock(content=client_a_message or "Hello! I'm ready to test context management.")
            
            # Client B sends "Got it! Your favorite color is blue..."
            elif "Got it! Your favorite color is blue" in last_message:
                client_b_message = last_message
                return Mock(content="Got it! Your favorite color is blue. I'll remember that.")
            
            else:
                return Mock(content=f"Unknown message: {last_message}")
        
        mock_client.ainvoke.side_effect = mock_client_ainvoke
        
        # Test Client A conversation flow
        client_a_llm = LLMTestClient(mock_llm, max_context_messages=10)
        conversation_prompt = "Let's test context management. My favorite color is blue."
        
        # Client A should:
        # 1. Process conversation_prompt → "Hello! I'm ready to test context management."
        # 2. Send this to MotiveProxy
        # 3. Receive response from Client B
        # 4. Process that response
        
        results_a = await _run_llm_conversation(
            name="ClientA",
            client=mock_client,
            llm_client=client_a_llm,
            conversation_prompt=conversation_prompt,
            turns=1,
            streaming=False,
            role="A"
        )
        
        # Verify Client A's conversation
        assert len(results_a) >= 1
        assert results_a[0]["action"] == "llm_init"
        assert "Hello! I'm ready to test context management" in results_a[0]["message"]
        
        # Test Client B conversation flow  
        client_b_llm = LLMTestClient(mock_llm, max_context_messages=10)
        
        # Client B should:
        # 1. Process conversation_prompt → "Hello! I'm ready to test context management." (WRONG!)
        # 2. Send this to MotiveProxy
        # 3. Receive response from Client A
        # 4. Process that response
        
        results_b = await _run_llm_conversation(
            name="ClientB", 
            client=mock_client,
            llm_client=client_b_llm,
            conversation_prompt=conversation_prompt,
            turns=1,
            streaming=False,
            role="B"
        )
        
        # With the fix, Client B should now:
        # 1. Send "Ready to chat!" to establish connection
        # 2. Receive Client A's message
        # 3. Respond to Client A's message
        
        assert len(results_b) >= 2  # Should have llm_wait and llm_response steps
        
        # First step: llm_wait (establishing connection)
        assert results_b[0]["action"] == "llm_wait"
        assert results_b[0]["message"] == "Ready to chat!"
        
        # Second step: llm_response (responding to Client A)
        assert results_b[1]["action"] == "llm_response"
        
        # The fix should make Client B respond to Client A's message
        # Expected: Client B should receive "Hello! I'm ready to test context management." 
        # and respond with "Got it! Your favorite color is blue. I'll remember that."
        
        # This assertion should PASS now that we fixed the bug
        assert "Got it! Your favorite color is blue" in results_b[1]["message"], \
            f"Client B should respond to Client A's message, but got: {results_b[1]['message']}"
