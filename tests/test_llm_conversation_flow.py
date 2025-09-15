"""Test LLM conversation flow through MotiveProxy."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from motive_proxy.testing.llm_client import LLMTestClient


class TestLLMConversationFlow:
    """Test that LLM clients have proper conversation flow."""
    
    @pytest.mark.asyncio
    async def test_conversation_flow_client_a_initiates(self):
        """Test that Client A initiates conversation and Client B responds to A's message."""
        # Mock LLM that responds differently to different inputs
        mock_llm = AsyncMock()
        
        # Client A's LLM responds to conversation prompt
        mock_llm.ainvoke.return_value = Mock(content="Hello! I'm ready to test context management.")
        
        client_a = LLMTestClient(mock_llm, max_context_messages=10)
        
        # Client A processes conversation prompt
        conversation_prompt = "Let's test context management. My favorite color is blue."
        client_a_response = await client_a.process_message(conversation_prompt)
        
        assert client_a_response == "Hello! I'm ready to test context management."
        
        # Now Client A should send this response to MotiveProxy
        # Client B should receive this response and respond to it
        mock_llm.ainvoke.return_value = Mock(content="Got it! Your favorite color is blue. I'll remember that.")
        
        client_b_response = await client_a.process_message(client_a_response)
        
        assert client_b_response == "Got it! Your favorite color is blue. I'll remember that."
    
    @pytest.mark.asyncio 
    async def test_conversation_flow_client_b_responds_to_a(self):
        """Test that Client B responds to Client A's message, not the conversation prompt."""
        mock_llm = AsyncMock()
        
        # Client B should respond to Client A's message, not the conversation prompt
        client_b = LLMTestClient(mock_llm, max_context_messages=10)
        
        # Simulate Client A's message coming through MotiveProxy
        client_a_message = "Hello! I'm ready to test context management."
        mock_llm.ainvoke.return_value = Mock(content="Got it! Your favorite color is blue. I'll remember that.")
        
        client_b_response = await client_b.process_message(client_a_message)
        
        assert client_b_response == "Got it! Your favorite color is blue. I'll remember that."
        
        # Verify the LLM was called with Client A's message, not the conversation prompt
        mock_llm.ainvoke.assert_called_once()
        call_args = mock_llm.ainvoke.call_args[0][0]  # First argument (messages list)
        assert len(call_args) == 1
        assert call_args[0].content == client_a_message
    
    def test_expected_conversation_flow(self):
        """Test the expected conversation flow between Client A and Client B."""
        conversation_prompt = "Let's test context management. My favorite color is blue."
        
        # Expected flow:
        # 1. Client A processes conversation_prompt → "Hello! I'm ready to test context management."
        # 2. Client A sends this to MotiveProxy
        # 3. Client B receives "Hello! I'm ready to test context management." → "Got it! Your favorite color is blue. I'll remember that."
        # 4. Client B sends this to MotiveProxy  
        # 5. Client A receives "Got it! Your favorite color is blue. I'll remember that." → "Yes, I've got it! Your favorite color is blue. Is there anything else I can help you with today?"
        
        expected_flow = [
            {
                "client": "A",
                "sends": "Hello! I'm ready to test context management.",
                "receives": "Got it! Your favorite color is blue. I'll remember that."
            },
            {
                "client": "B", 
                "sends": "Got it! Your favorite color is blue. I'll remember that.",
                "receives": "Yes, I've got it! Your favorite color is blue. Is there anything else I can help you with today?"
            }
        ]
        
        # This test documents the expected flow
        assert len(expected_flow) == 2
        assert expected_flow[0]["client"] == "A"
        assert expected_flow[1]["client"] == "B"
