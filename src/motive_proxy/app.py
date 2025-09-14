"""FastAPI application setup and configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from motive_proxy.routes import chat_completions, health
from motive_proxy.models import ErrorResponse, ErrorDetails
from motive_proxy.session_manager import SessionManager
from motive_proxy.observability import setup_logging, get_logger, extract_request_context, generate_correlation_id
from motive_proxy.settings import get_settings
from motive_proxy.middleware import SecurityMiddleware, CORSMiddleware
import asyncio
import contextlib
import time


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    setup_logging()
    logger = get_logger("motive_proxy.startup")
    
    logger.info("Starting MotiveProxy", 
                host=settings.host, 
                port=settings.port,
                debug=settings.debug)
    
    app.state.session_manager = SessionManager(
        handshake_timeout_seconds=settings.handshake_timeout_seconds,
        turn_timeout_seconds=settings.turn_timeout_seconds,
        session_ttl_seconds=settings.session_ttl_seconds,
        max_sessions=settings.max_sessions,
    )
    
    # Background TTL cleanup task
    async def _cleanup_loop():
        cleanup_logger = get_logger("motive_proxy.cleanup")
        try:
            while True:
                removed_count = await app.state.session_manager.cleanup_expired(ttl_seconds=settings.session_ttl_seconds)
                if removed_count > 0:
                    cleanup_logger.info("Cleaned up expired sessions", removed_count=removed_count)
                await asyncio.sleep(settings.cleanup_interval_seconds)
        except asyncio.CancelledError:
            cleanup_logger.info("Cleanup task cancelled")
            return

    cleanup_task = asyncio.create_task(_cleanup_loop())
    app.state.cleanup_task = cleanup_task
    
    # Store startup time for uptime calculation
    app.state.start_time = time.time()
    
    logger.info("MotiveProxy startup complete")
    yield
    
    # Shutdown
    shutdown_logger = get_logger("motive_proxy.shutdown")
    shutdown_logger.info("Shutting down MotiveProxy")
    cleanup_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cleanup_task
    shutdown_logger.info("MotiveProxy shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="MotiveProxy",
        description="A human-in-the-loop proxy server for OpenAI Chat Completions API",  # noqa: E501
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add security middleware
    app.add_middleware(SecurityMiddleware)
    
    # Add enhanced CORS middleware
    app.add_middleware(CORSMiddleware, settings=settings)

    # Include routers
    app.include_router(health.router)
    app.include_router(chat_completions.router)

    # Standardized validation error handler (422)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error=ErrorDetails(
                    message="Validation error",
                    type="invalid_request_error",
                    code="validation_error",
                )
            ).model_dump(),
        )

    return app
