"""Tests for LLM-enhanced test client functionality."""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from motive_proxy.testing.llm_client import LLMTestClient, create_llm_client


class TestLLMTestClient:
    """Test LLM-enhanced test client functionality."""

    def test_create_openai_client(self):
        """Test creating OpenAI client."""
        with patch('langchain_openai.ChatOpenAI') as mock_openai:
            client = create_llm_client('openai', 'gpt-4', 'test-key')
            mock_openai.assert_called_once_with(model='gpt-4', api_key='test-key')
            assert client is not None

    def test_create_anthropic_client(self):
        """Test creating Anthropic client."""
        with patch('langchain_anthropic.ChatAnthropic') as mock_anthropic:
            client = create_llm_client('anthropic', 'claude-3-sonnet', 'test-key')
            mock_anthropic.assert_called_once_with(model='claude-3-sonnet', api_key='test-key')
            assert client is not None

    def test_create_google_client(self):
        """Test creating Google Gemini client."""
        with patch('langchain_google_genai.ChatGoogleGenerativeAI') as mock_google:
            client = create_llm_client('google', 'gemini-2.5-flash', 'test-key')
            mock_google.assert_called_once_with(model='gemini-2.5-flash', api_key='test-key')
            assert client is not None

    def test_create_unsupported_provider(self):
        """Test creating unsupported provider raises error."""
        with pytest.raises(ValueError, match="Unsupported LLM provider: unsupported"):
            create_llm_client('unsupported', 'model', 'key')

    @pytest.mark.asyncio
    async def test_llm_client_conversation(self):
        """Test LLM client conversation flow."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "Hello! I'm doing well, thank you for asking."
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        
        client = LLMTestClient(mock_llm)
        
        # Process a message
        response = await client.process_message("How are you?")
        
        assert response == "Hello! I'm doing well, thank you for asking."
        mock_llm.ainvoke.assert_called_once()
        
        # Check conversation history
        assert len(client.conversation_history) == 2  # Human message + AI response

    @pytest.mark.asyncio
    async def test_llm_client_conversation_context(self):
        """Test that LLM client maintains conversation context."""
        # Mock LLM responses
        mock_response1 = Mock()
        mock_response1.content = "I'm an AI assistant."
        
        mock_response2 = Mock()
        mock_response2.content = "Yes, I remember you asked about my identity."
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = [mock_response1, mock_response2]
        
        client = LLMTestClient(mock_llm)
        
        # First message
        response1 = await client.process_message("What are you?")
        assert response1 == "I'm an AI assistant."
        
        # Second message (should have context)
        response2 = await client.process_message("Do you remember what I asked?")
        assert response2 == "Yes, I remember you asked about my identity."
        
        # Should have been called twice with different conversation histories
        assert mock_llm.ainvoke.call_count == 2

    def test_environment_variable_api_keys(self):
        """Test that API keys are loaded from environment variables."""
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'env-key'}):
            with patch('langchain_google_genai.ChatGoogleGenerativeAI') as mock_google:
                client = create_llm_client('google', 'gemini-2.5-flash')
                mock_google.assert_called_once_with(model='gemini-2.5-flash', api_key='env-key')

    def test_explicit_api_key_overrides_env(self):
        """Test that explicit API key overrides environment variable."""
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'env-key'}):
            with patch('langchain_google_genai.ChatGoogleGenerativeAI') as mock_google:
                client = create_llm_client('google', 'gemini-2.5-flash', 'explicit-key')
                mock_google.assert_called_once_with(model='gemini-2.5-flash', api_key='explicit-key')

    def test_context_window_management(self):
        """Test context window management functionality."""
        mock_llm = AsyncMock()
        client = LLMTestClient(mock_llm, max_context_messages=3)
        
        # Set system prompt
        client.set_system_prompt("You are a helpful assistant.")
        assert client.system_prompt == "You are a helpful assistant."
        
        # Test context summary
        summary = client.get_context_summary()
        assert summary['max_context_messages'] == 3
        assert summary['total_messages'] == 0
        assert summary['context_messages'] == 0
        assert summary['has_system_prompt'] == True

    @pytest.mark.asyncio
    async def test_context_truncation(self):
        """Test that context is properly truncated when exceeding limits."""
        mock_llm = AsyncMock()
        client = LLMTestClient(mock_llm, max_context_messages=2)
        
        # Add messages beyond the limit
        for i in range(5):
            mock_response = AIMessage(content=f"Response {i}")
            mock_llm.ainvoke.return_value = mock_response
            
            await client.process_message(f"Message {i}")
        
        # Should have 10 total messages (5 human + 5 AI) but only 2 in context
        assert len(client.conversation_history) == 10
        context = client._get_context_for_llm()
        assert len(context) == 2  # Only recent messages
        
        # Context should contain the last 2 messages
        assert isinstance(context[0], HumanMessage)
        assert context[0].content == "Message 4"
        assert isinstance(context[1], AIMessage)
        assert context[1].content == "Response 4"

    @pytest.mark.asyncio
    async def test_system_prompt_in_context(self):
        """Test that system prompt is included in context when present."""
        mock_llm = AsyncMock()
        client = LLMTestClient(mock_llm, max_context_messages=3)
        client.set_system_prompt("You are a helpful assistant.")
        
        # Add messages beyond the limit
        for i in range(4):
            mock_response = AIMessage(content=f"Response {i}")
            mock_llm.ainvoke.return_value = mock_response
            
            await client.process_message(f"Message {i}")
        
        # Context should include system prompt + recent messages
        context = client._get_context_for_llm()
        assert len(context) == 4  # System prompt + 3 recent messages (max_context_messages)
        assert isinstance(context[0], SystemMessage)
        assert context[0].content == "You are a helpful assistant."
        # The last 3 messages should be: HumanMessage("Message 3"), AIMessage("Response 3")
        # But we're getting AIMessage("Response 2") and HumanMessage("Message 3")
        assert isinstance(context[1], AIMessage)
        assert context[1].content == "Response 2"
        assert isinstance(context[2], HumanMessage)
        assert context[2].content == "Message 3"
        assert isinstance(context[3], AIMessage)
        assert context[3].content == "Response 3"

    def test_clear_history(self):
        """Test clearing conversation history."""
        mock_llm = AsyncMock()
        client = LLMTestClient(mock_llm)
        client.set_system_prompt("Test prompt")
        
        # Add some messages
        client.conversation_history = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there")
        ]
        
        # Clear history
        client.clear_history()
        
        assert len(client.conversation_history) == 0
        assert client.system_prompt is None
