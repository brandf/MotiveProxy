"""Application settings and configuration."""

from typing import Optional

from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8000, description="Port to bind to")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Session settings
    handshake_timeout_seconds: float = Field(default=30.0, description="Handshake timeout")
    turn_timeout_seconds: float = Field(default=30.0, description="Turn timeout")
    session_ttl_seconds: float = Field(default=3600.0, description="Session TTL")
    max_sessions: int = Field(default=100, description="Maximum concurrent sessions")
    
    # Cleanup settings
    cleanup_interval_seconds: float = Field(default=60.0, description="Cleanup task interval")
    
    # Observability settings
    log_level: str = Field(default="INFO", description="Logging level")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    
    # Security settings
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")
    max_payload_size: int = Field(default=1024 * 1024, description="Max request payload size (bytes)")
    
    # Rate limiting settings
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests_per_minute: int = Field(default=60, description="Requests per minute per IP")
    rate_limit_requests_per_hour: int = Field(default=1000, description="Requests per hour per IP")
    rate_limit_burst_limit: int = Field(default=10, description="Burst limit (requests per 10 seconds)")
    
    # Authentication settings
    enable_api_key_auth: bool = Field(default=False, description="Enable API key authentication")
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    valid_api_keys: list[str] = Field(default=[], description="Valid API keys")
    
    model_config = ConfigDict(
        env_prefix="MOTIVE_PROXY_",
        case_sensitive=False,
    )


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
