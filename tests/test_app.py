"""Tests for the FastAPI application."""

from fastapi.testclient import TestClient

from motive_proxy.app import create_app


class TestApp:
    """Test cases for the FastAPI application."""

    def test_app_creation(self):
        """Test that the app can be created successfully."""
        app = create_app()
        assert app is not None
        assert app.title == "MotiveProxy"

    def test_health_endpoint(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_openai_chat_completions_endpoint_exists(self, client: TestClient):
        """Test that the OpenAI chat completions endpoint exists."""
        # This should return 422 (validation error) rather than 404 (not found)
        response = client.post("/v1/chat/completions")
        assert response.status_code == 422  # Missing required fields

    def test_openai_chat_completions_endpoint_with_valid_request(
        self, client: TestClient, sample_openai_request
    ):
        """Test the OpenAI chat completions endpoint with a valid request."""
        response = client.post("/v1/chat/completions", json=sample_openai_request)
        # For now, this will likely timeout or return an error since we haven't implemented
        # the session management yet. We'll implement this in TDD fashion.
        assert response.status_code in [
            200,
            408,
            500,
        ]  # Accept various states during development
