"""Pytest configuration and shared fixtures."""

import asyncio
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from motive_proxy.app import create_app


@pytest.fixture(autouse=True)
def fast_timeouts():
    """Force short protocol timeouts for fast, deterministic tests.

    Ensures unpaired requests return 408 quickly during handshake/turn waits.
    """
    from motive_proxy.session_manager import SessionManager
    import motive_proxy.routes.chat_completions as cc

    cc._session_manager = SessionManager(
        handshake_timeout_seconds=0.2,
        turn_timeout_seconds=0.2,
    )
    yield

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    app = create_app()
    # Manually initialize session manager for tests since lifespan isn't triggered
    from motive_proxy.session_manager import SessionManager
    app.state.session_manager = SessionManager(
        handshake_timeout_seconds=0.2,
        turn_timeout_seconds=0.2,
    )
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI application."""
    async with AsyncClient(base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_openai_request():
    """Sample OpenAI Chat Completions API request."""
    return {
        "model": "test-session-123",
        "messages": [{"role": "user", "content": "Hello, how are you?"}],
        "temperature": 0.7,
        "max_tokens": 100,
    }


@pytest.fixture
def sample_openai_response():
    """Sample OpenAI Chat Completions API response."""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "test-session-123",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "I'm doing well, thank you!",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 9, "completion_tokens": 12, "total_tokens": 21},
    }
