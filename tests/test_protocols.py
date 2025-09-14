"""Tests for protocol adapters."""

import pytest
from motive_proxy.protocols.base import ProtocolType, ProtocolRequest, ProtocolResponse
from motive_proxy.protocols.openai import OpenAIAdapter
from motive_proxy.protocols.anthropic import AnthropicAdapter
from motive_proxy.protocol_manager import ProtocolManager


class TestProtocolRequest:
    """Test ProtocolRequest data structure."""

    def test_protocol_request_creation(self):
        """Test ProtocolRequest creation."""
        request = ProtocolRequest(
            session_id="test-session",
            messages=[{"role": "user", "content": "Hello"}],
            stream=False,
            model="test-model"
        )
        
        assert request.session_id == "test-session"
        assert len(request.messages) == 1
        assert request.messages[0]["role"] == "user"
        assert request.messages[0]["content"] == "Hello"
        assert request.stream is False
        assert request.model == "test-model"
        assert request.extra_params == {}

    def test_protocol_request_with_extra_params(self):
        """Test ProtocolRequest with extra parameters."""
        request = ProtocolRequest(
            session_id="test-session",
            messages=[{"role": "user", "content": "Hello"}],
            extra_params={"custom": "value"}
        )
        
        assert request.extra_params["custom"] == "value"


class TestProtocolResponse:
    """Test ProtocolResponse data structure."""

    def test_protocol_response_creation(self):
        """Test ProtocolResponse creation."""
        response = ProtocolResponse(
            content="Hello world",
            model="test-model",
            session_id="test-session",
            finish_reason="stop"
        )
        
        assert response.content == "Hello world"
        assert response.model == "test-model"
        assert response.session_id == "test-session"
        assert response.finish_reason == "stop"
        assert response.extra_data == {}


class TestOpenAIAdapter:
    """Test OpenAI protocol adapter."""

    def test_adapter_creation(self):
        """Test OpenAI adapter creation."""
        adapter = OpenAIAdapter()
        assert adapter.get_protocol_type() == ProtocolType.OPENAI
        assert adapter.get_endpoint_path() == "/v1/chat/completions"

    def test_parse_request(self):
        """Test parsing OpenAI request."""
        adapter = OpenAIAdapter()
        raw_request = {
            "model": "test-session",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        request = adapter.parse_request(raw_request)
        
        assert request.session_id == "test-session"
        assert len(request.messages) == 1
        assert request.stream is True
        assert request.temperature == 0.7
        assert request.max_tokens == 100

    def test_format_response(self):
        """Test formatting OpenAI response."""
        adapter = OpenAIAdapter()
        response = ProtocolResponse(
            content="Hello world",
            model="test-model",
            session_id="test-session",
            finish_reason="stop"
        )
        
        formatted = adapter.format_response(response)
        
        assert formatted["object"] == "chat.completion"
        assert formatted["model"] == "test-model"
        assert len(formatted["choices"]) == 1
        assert formatted["choices"][0]["message"]["content"] == "Hello world"
        assert formatted["choices"][0]["finish_reason"] == "stop"
        assert "usage" in formatted

    def test_validate_request_valid(self):
        """Test validating valid OpenAI request."""
        adapter = OpenAIAdapter()
        request = ProtocolRequest(
            session_id="test-session",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        assert adapter.validate_request(request) is True

    def test_validate_request_invalid_session_id(self):
        """Test validating request with invalid session ID."""
        adapter = OpenAIAdapter()
        request = ProtocolRequest(
            session_id="",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        assert adapter.validate_request(request) is False

    def test_validate_request_invalid_messages(self):
        """Test validating request with invalid messages."""
        adapter = OpenAIAdapter()
        request = ProtocolRequest(
            session_id="test-session",
            messages=[]
        )
        
        assert adapter.validate_request(request) is False

    def test_validate_request_invalid_message_format(self):
        """Test validating request with invalid message format."""
        adapter = OpenAIAdapter()
        request = ProtocolRequest(
            session_id="test-session",
            messages=[{"role": "invalid", "content": "Hello"}]
        )
        
        assert adapter.validate_request(request) is False


class TestAnthropicAdapter:
    """Test Anthropic protocol adapter."""

    def test_adapter_creation(self):
        """Test Anthropic adapter creation."""
        adapter = AnthropicAdapter()
        assert adapter.get_protocol_type() == ProtocolType.ANTHROPIC
        assert adapter.get_endpoint_path() == "/v1/messages"

    def test_parse_request(self):
        """Test parsing Anthropic request."""
        adapter = AnthropicAdapter()
        raw_request = {
            "model": "test-session",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        request = adapter.parse_request(raw_request)
        
        assert request.session_id == "test-session"
        assert len(request.messages) == 1
        assert request.stream is True
        assert request.temperature == 0.7
        assert request.max_tokens == 100

    def test_format_response(self):
        """Test formatting Anthropic response."""
        adapter = AnthropicAdapter()
        response = ProtocolResponse(
            content="Hello world",
            model="test-model",
            session_id="test-session",
            finish_reason="end_turn"
        )
        
        formatted = adapter.format_response(response)
        
        assert formatted["type"] == "message"
        assert formatted["role"] == "assistant"
        assert formatted["model"] == "test-model"
        assert len(formatted["content"]) == 1
        assert formatted["content"][0]["text"] == "Hello world"
        assert formatted["stop_reason"] == "end_turn"
        assert "usage" in formatted

    def test_validate_request_valid(self):
        """Test validating valid Anthropic request."""
        adapter = AnthropicAdapter()
        request = ProtocolRequest(
            session_id="test-session",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        assert adapter.validate_request(request) is True

    def test_validate_request_invalid_role(self):
        """Test validating request with invalid role."""
        adapter = AnthropicAdapter()
        request = ProtocolRequest(
            session_id="test-session",
            messages=[{"role": "system", "content": "Hello"}]
        )
        
        assert adapter.validate_request(request) is False


class TestProtocolManager:
    """Test protocol manager functionality."""

    def test_manager_creation(self):
        """Test protocol manager creation."""
        manager = ProtocolManager()
        
        # Should have default adapters registered
        assert ProtocolType.OPENAI in manager._adapters
        assert ProtocolType.ANTHROPIC in manager._adapters

    def test_get_adapter(self):
        """Test getting adapter by type."""
        manager = ProtocolManager()
        
        openai_adapter = manager.get_adapter(ProtocolType.OPENAI)
        assert openai_adapter is not None
        assert isinstance(openai_adapter, OpenAIAdapter)
        
        anthropic_adapter = manager.get_adapter(ProtocolType.ANTHROPIC)
        assert anthropic_adapter is not None
        assert isinstance(anthropic_adapter, AnthropicAdapter)

    def test_get_adapter_by_endpoint(self):
        """Test getting adapter by endpoint path."""
        manager = ProtocolManager()
        
        openai_adapter = manager.get_adapter_by_endpoint("/v1/chat/completions")
        assert openai_adapter is not None
        assert isinstance(openai_adapter, OpenAIAdapter)
        
        anthropic_adapter = manager.get_adapter_by_endpoint("/v1/messages")
        assert anthropic_adapter is not None
        assert isinstance(anthropic_adapter, AnthropicAdapter)

    def test_get_adapter_for_request_openai_endpoint(self):
        """Test getting adapter for OpenAI endpoint."""
        manager = ProtocolManager()
        
        adapter = manager.get_adapter_for_request({}, "/v1/chat/completions")
        assert adapter is not None
        assert isinstance(adapter, OpenAIAdapter)

    def test_get_adapter_for_request_anthropic_endpoint(self):
        """Test getting adapter for Anthropic endpoint."""
        manager = ProtocolManager()
        
        adapter = manager.get_adapter_for_request({}, "/v1/messages")
        assert adapter is not None
        assert isinstance(adapter, AnthropicAdapter)

    def test_get_adapter_for_request_unknown_endpoint(self):
        """Test getting adapter for unknown endpoint (fallback to OpenAI)."""
        manager = ProtocolManager()
        
        adapter = manager.get_adapter_for_request({}, "/unknown/endpoint")
        assert adapter is not None
        assert isinstance(adapter, OpenAIAdapter)

    def test_list_supported_protocols(self):
        """Test listing supported protocols."""
        manager = ProtocolManager()
        
        protocols = manager.list_supported_protocols()
        assert "openai" in protocols
        assert "anthropic" in protocols
        assert len(protocols) == 2
