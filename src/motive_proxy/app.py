"""FastAPI application setup and configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from motive_proxy.routes import chat_completions, health


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="MotiveProxy",
        description="A human-in-the-loop proxy server for OpenAI Chat Completions API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(chat_completions.router)

    return app
