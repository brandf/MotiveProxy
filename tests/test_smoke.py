"""Smoke tests for basic MotiveProxy functionality.

These tests verify that the server can start up and respond to basic requests.
They don't test the full MotiveProxy functionality - just basic server operation.
"""

import threading

import httpx
import pytest
from fastapi.testclient import TestClient


class TestServerSmoke:
    """Smoke tests for basic server functionality."""

    def test_server_starts(self, client: TestClient):
        """Test that the server can start and respond to health check."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_openai_endpoint_exists(self, client: TestClient):
        """Test that the OpenAI chat completions endpoint exists."""
        # This should return 422 (validation error) rather than 404 (not found)
        response = client.post("/v1/chat/completions")
        assert response.status_code == 422  # Missing required fields

    def test_openai_endpoint_accepts_valid_request(self, client: TestClient):
        """Test that the OpenAI endpoint accepts a valid request structure."""
        request_data = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}],
        }

        response = client.post("/v1/chat/completions", json=request_data)
        # Should not return 422 (validation error) - request structure is valid
        assert response.status_code != 422
        # For now, unpaired requests may 408 (timeout) until the counterpart arrives
        assert response.status_code in [200, 408, 500, 501]

    def test_openai_endpoint_returns_proper_format(self, client: TestClient):
        """Test that the OpenAI endpoint returns proper response format."""
        request_data = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}],
        }

        response = client.post("/v1/chat/completions", json=request_data)

        if response.status_code == 200:
            data = response.json()
            # Should have OpenAI-compatible response structure
            assert "id" in data
            assert "object" in data
            assert "created" in data
            assert "model" in data
            assert "choices" in data
            assert "usage" in data

    def test_concurrent_requests(self, client: TestClient):
        """Test that the server can handle multiple concurrent requests."""
        results = []

        def make_request():
            response = client.get("/health")
            results.append(response.status_code)

        # Make 5 concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should succeed
        assert len(results) == 5
        assert all(status == 200 for status in results)

    @pytest.mark.asyncio
    async def test_async_client_works(self, app):
        """Test that async client can connect to the server."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}

    def test_server_handles_invalid_json(self, client: TestClient):
        """Test that server handles invalid JSON gracefully."""
        response = client.post(
            "/v1/chat/completions",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422  # Should return validation error

    def test_server_handles_missing_content_type(self, client: TestClient):
        """Test that server handles missing content type gracefully."""
        response = client.post("/v1/chat/completions", data='{"test": "data"}')
        # Should either accept it or return a clear error
        assert response.status_code in [200, 400, 422]

    def test_server_handles_large_requests(self, client: TestClient):
        """Test that server can handle reasonably large requests."""
        large_message = "x" * 10000  # 10KB message
        request_data = {
            "model": "test-model",
            "messages": [{"role": "user", "content": large_message}],
        }

        response = client.post("/v1/chat/completions", json=request_data)
        # Should not crash; may timeout if unpaired
        assert response.status_code in [200, 400, 408, 413, 500, 501]

    def test_server_handles_empty_messages(self, client: TestClient):
        """Test that server handles empty messages array."""
        request_data = {"model": "test-model", "messages": []}

        response = client.post("/v1/chat/completions", json=request_data)
        # Should return validation error for empty messages
        assert response.status_code == 422

    def test_server_handles_missing_model(self, client: TestClient):
        """Test that server handles missing model parameter."""
        request_data = {"messages": [{"role": "user", "content": "Hello"}]}

        response = client.post("/v1/chat/completions", json=request_data)
        # Should return validation error for missing model
        assert response.status_code == 422

    def test_server_handles_missing_messages(self, client: TestClient):
        """Test that server handles missing messages parameter."""
        request_data = {"model": "test-model"}

        response = client.post("/v1/chat/completions", json=request_data)
        # Should return validation error for missing messages
        assert response.status_code == 422
