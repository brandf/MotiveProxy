"""Tests for streaming functionality."""

import pytest
import json
from fastapi.testclient import TestClient

from motive_proxy.streaming import StreamingResponse, StreamChunk, StreamingSession
from motive_proxy.session_manager import SessionManager


class TestStreamingResponse:
    """Test streaming response functionality."""

    @pytest.mark.asyncio
    async def test_stream_completion(self):
        """Test streaming a completion."""
        response = StreamingResponse("test-session", "test-model")
        completion = "Hello world this is a test"
        
        chunks = []
        async for chunk in response.stream_completion("test prompt", completion):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        
        # Parse first chunk
        first_chunk_data = json.loads(chunks[0].split("data: ")[1])
        assert first_chunk_data["object"] == "chat.completion.chunk"
        assert first_chunk_data["model"] == "test-model"
        assert "choices" in first_chunk_data
        assert len(first_chunk_data["choices"]) == 1
        
        # Check that we have content
        delta = first_chunk_data["choices"][0]["delta"]
        assert "content" in delta
        assert len(delta["content"]) > 0

    @pytest.mark.asyncio
    async def test_stream_empty_completion(self):
        """Test streaming an empty completion."""
        response = StreamingResponse("test-session", "test-model")
        
        chunks = []
        async for chunk in response.stream_completion("test prompt", ""):
            chunks.append(chunk)
        
        assert len(chunks) == 1
        
        chunk_data = json.loads(chunks[0].split("data: ")[1])
        assert chunk_data["choices"][0]["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_stream_error(self):
        """Test streaming an error."""
        response = StreamingResponse("test-session", "test-model")
        
        chunks = []
        async for chunk in response.stream_error("Test error message", "test_error"):
            chunks.append(chunk)
        
        assert len(chunks) == 1
        
        chunk_data = json.loads(chunks[0].split("data: ")[1])
        assert "error" in chunk_data
        assert chunk_data["error"]["message"] == "Test error message"
        assert chunk_data["error"]["type"] == "test_error"


class TestStreamingIntegration:
    """Test streaming integration with the API."""

    def test_streaming_endpoint_non_stream(self, client: TestClient):
        """Test that non-streaming requests still work."""
        request_data = {
            "model": "test-session",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False
        }
        
        response = client.post("/v1/chat/completions", json=request_data)
        # Should timeout (408) since no counterpart, but endpoint should work
        assert response.status_code in [200, 408]

    def test_streaming_endpoint_stream_request(self, client: TestClient):
        """Test streaming endpoint with stream=true."""
        request_data = {
            "model": "test-session-stream",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True
        }
        
        response = client.post("/v1/chat/completions", json=request_data)
        
        # Should return 200 with streaming response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"
        assert "cache-control" in response.headers
        
        # Check that response contains SSE format
        content = response.text
        assert "data: " in content
        assert "[DONE]" in content

    def test_streaming_endpoint_invalid_json(self, client: TestClient):
        """Test streaming endpoint with invalid JSON."""
        response = client.post(
            "/v1/chat/completions",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

    def test_streaming_endpoint_empty_messages(self, client: TestClient):
        """Test streaming endpoint with empty messages."""
        request_data = {
            "model": "test-session",
            "messages": [],
            "stream": True
        }
        
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 422


class TestStreamChunk:
    """Test StreamChunk data structure."""

    def test_stream_chunk_creation(self):
        """Test StreamChunk creation and formatting."""
        chunk = StreamChunk(
            id="test-id",
            model="test-model",
            choices=[{
                "index": 0,
                "delta": {"content": "Hello"},
                "finish_reason": None
            }]
        )
        
        assert chunk.id == "test-id"
        assert chunk.model == "test-model"
        assert chunk.object == "chat.completion.chunk"
        assert len(chunk.choices) == 1
        assert chunk.created > 0

    def test_stream_chunk_with_finish_reason(self):
        """Test StreamChunk with finish reason."""
        chunk = StreamChunk(
            id="test-id",
            model="test-model",
            choices=[{
                "index": 0,
                "delta": {"content": ""},
                "finish_reason": "stop"
            }]
        )
        
        assert chunk.choices[0]["finish_reason"] == "stop"


class TestStreamingSession:
    """Test StreamingSession functionality."""

    @pytest.mark.asyncio
    async def test_streaming_session_creation(self):
        """Test StreamingSession creation."""
        session = StreamingSession("test-session", "test-model")
        
        assert session.session_id == "test-session"
        assert session.model == "test-model"
        assert session.streaming_response is not None

    @pytest.mark.asyncio
    async def test_streaming_session_timeout(self):
        """Test StreamingSession handles timeouts."""
        session = StreamingSession("test-session", "test-model")
        
        # Create a mock session that will timeout
        class MockSession:
            async def process_request(self, content):
                raise TimeoutError("Test timeout")
        
        mock_session = MockSession()
        
        chunks = []
        async for chunk in session.process_streaming_request("test content", mock_session):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        
        # Check that we get an error chunk
        chunk_data = json.loads(chunks[0].split("data: ")[1])
        assert "error" in chunk_data
        assert "timeout" in chunk_data["error"]["type"]
