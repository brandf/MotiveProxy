"""Integration tests for MotiveProxy server functionality.

These tests verify that the server works correctly with real HTTP requests,
replacing the need for ad-hoc curl or manual testing.
"""

import pytest
import httpx
from fastapi.testclient import TestClient


class TestServerIntegration:
    """Integration tests for server functionality."""

    def test_health_endpoint_integration(self, client: TestClient):
        """Test health endpoint with real HTTP request."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_openai_endpoint_integration(self, client: TestClient):
        """Test OpenAI chat completions endpoint with real request."""
        request_data = {
            "model": "test-session-123",
            "messages": [{"role": "user", "content": "Hello, MotiveProxy!"}]
        }
        
        # Single request without counterpart now times out (expected 408) until paired
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code in [200, 408]

        data = response.json()
        if response.status_code == 200:
            assert "id" in data
            assert "object" in data
            assert "created" in data
            assert "model" in data
            assert "choices" in data
            assert "usage" in data
            # Verify the response structure matches OpenAI format
            assert data["object"] == "chat.completion"
            assert data["model"] == "test-session-123"
            assert len(data["choices"]) == 1
            assert data["choices"][0]["message"]["role"] == "assistant"
        else:
            # Standard timeout response
            assert data == {
                "detail": {
                    "error": {
                        "message": "Request timed out",
                        "type": "timeout_error",
                        "code": "timeout",
                        "param": None,
                    }
                }
            }

    def test_openai_endpoint_with_different_models(self, client: TestClient):
        """Test that different model names are handled correctly."""
        test_cases = [
            "session-abc-123",
            "game-npc-guard",
            "test-user-session",
            "long-session-name-with-dashes-and-numbers-12345"
        ]
        
        for model_name in test_cases:
            request_data = {
                "model": model_name,
                "messages": [{"role": "user", "content": f"Test message for {model_name}"}]
            }
            
            response = client.post("/v1/chat/completions", json=request_data)
            assert response.status_code in [200, 408]

            data = response.json()
            if response.status_code == 200:
                assert data["model"] == model_name
            else:
                assert data == {
                    "detail": {
                        "error": {
                            "message": "Request timed out",
                            "type": "timeout_error",
                            "code": "timeout",
                            "param": None,
                        }
                    }
                }

    def test_openai_endpoint_with_multiple_messages(self, client: TestClient):
        """Test endpoint with multiple messages in conversation."""
        request_data = {
            "model": "conversation-test",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"}
            ]
        }
        
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code in [200, 408]

        data = response.json()
        if response.status_code == 200:
            assert data["model"] == "conversation-test"
        else:
            assert data == {
                "detail": {
                    "error": {
                        "message": "Request timed out",
                        "type": "timeout_error",
                        "code": "timeout",
                        "param": None,
                    }
                }
            }

    def test_openai_endpoint_with_optional_parameters(self, client: TestClient):
        """Test endpoint with optional OpenAI parameters."""
        request_data = {
            "model": "parameter-test",
            "messages": [{"role": "user", "content": "Test with parameters"}],
            "temperature": 0.8,
            "max_tokens": 150,
            "stream": False
        }
        
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code in [200, 408]

        data = response.json()
        if response.status_code == 200:
            assert data["model"] == "parameter-test"
        else:
            assert data == {
                "detail": {
                    "error": {
                        "message": "Request timed out",
                        "type": "timeout_error",
                        "code": "timeout",
                        "param": None,
                    }
                }
            }

    def test_openai_endpoint_error_handling(self, client: TestClient):
        """Test proper error handling for invalid requests."""
        # Test empty messages array
        request_data = {
            "model": "error-test",
            "messages": []
        }
        
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 422
        assert response.json() == {
            "detail": {
                "error": {
                    "message": "Messages array cannot be empty",
                    "type": "invalid_request_error",
                    "code": "messages_empty",
                    "param": None,
                }
            }
        }

    def test_openai_endpoint_missing_required_fields(self, client: TestClient):
        """Test error handling for missing required fields."""
        # Test missing model
        request_data = {
            "messages": [{"role": "user", "content": "Missing model"}]
        }
        
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 422

        # Test missing messages
        request_data = {
            "model": "missing-messages"
        }
        
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 422

    def test_openai_endpoint_invalid_json(self, client: TestClient):
        """Test handling of invalid JSON requests."""
        response = client.post(
            "/v1/chat/completions",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_openai_endpoint_large_request(self, client: TestClient):
        """Test handling of reasonably large requests."""
        large_message = "x" * 10000  # 10KB message
        request_data = {
            "model": "large-request-test",
            "messages": [{"role": "user", "content": large_message}]
        }
        
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code in [200, 408]

        data = response.json()
        if response.status_code == 200:
            assert data["model"] == "large-request-test"
        else:
            assert data == {
                "detail": {
                    "error": {
                        "message": "Request timed out",
                        "type": "timeout_error",
                        "code": "timeout",
                        "param": None,
                    }
                }
            }

    @pytest.mark.asyncio
    async def test_async_client_integration(self, app):
        """Test server with async HTTP client."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Test health endpoint
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}
            
            # Test OpenAI endpoint
            request_data = {
                "model": "async-test",
                "messages": [{"role": "user", "content": "Async test message"}]
            }
            
            response = await client.post("/v1/chat/completions", json=request_data)
            assert response.status_code in [200, 408]

            data = response.json()
            if response.status_code == 200:
                assert data["model"] == "async-test"
            else:
                assert data == {
                    "detail": {
                        "error": {
                            "message": "Request timed out",
                            "type": "timeout_error",
                            "code": "timeout",
                            "param": None,
                        }
                    }
                }

    def test_concurrent_requests_integration(self, client: TestClient):
        """Test server handling of concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request(session_id: str):
            request_data = {
                "model": f"concurrent-test-{session_id}",
                "messages": [{"role": "user", "content": f"Concurrent request {session_id}"}]
            }
            
            response = client.post("/v1/chat/completions", json=request_data)
            results.append((session_id, response.status_code))
        
        # Make 5 concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(str(i),))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should be handled (200 or timeout 408 if unpaired)
        assert len(results) == 5
        for session_id, status_code in results:
            assert status_code in [200, 408], f"Request {session_id} failed with status {status_code}"

    def test_server_response_timing(self, client: TestClient):
        """Test that server responds within reasonable time."""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second

    def test_api_documentation_endpoints(self, client: TestClient):
        """Test that API documentation endpoints are accessible."""
        # Test OpenAPI docs endpoint
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Test ReDoc endpoint
        response = client.get("/redoc")
        assert response.status_code == 200
        
        # Test OpenAPI JSON schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "MotiveProxy"
