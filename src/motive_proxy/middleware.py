"""Middleware for security and rate limiting."""

import asyncio
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from motive_proxy.rate_limiter import RateLimiter, RateLimitConfig
from motive_proxy.settings import get_settings
from motive_proxy.observability import get_logger, get_metrics_collector
from motive_proxy.models import ErrorResponse, ErrorDetails


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security features: rate limiting, payload size, auth."""
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        self.logger = get_logger("motive_proxy.security_middleware")
        self.metrics = get_metrics_collector()
        
        # Initialize rate limiter if enabled
        if self.settings.enable_rate_limiting:
            rate_config = RateLimitConfig(
                requests_per_minute=self.settings.rate_limit_requests_per_minute,
                requests_per_hour=self.settings.rate_limit_requests_per_hour,
                burst_limit=self.settings.rate_limit_burst_limit,
            )
            self.rate_limiter = RateLimiter(rate_config)
        else:
            self.rate_limiter = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security middleware."""
        client_ip = self._get_client_ip(request)
        
        # Skip security checks for health and metrics endpoints
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        try:
            # Rate limiting
            if self.rate_limiter:
                is_allowed, reason = await self.rate_limiter.is_allowed(client_ip)
                if not is_allowed:
                    self.metrics.increment_counter("rate_limit_exceeded", tags={"ip": client_ip})
                    return self._create_error_response(429, "Rate limit exceeded", reason)
            
            # Payload size check
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.settings.max_payload_size:
                self.metrics.increment_counter("payload_too_large", tags={"ip": client_ip})
                return self._create_error_response(413, "Payload too large", 
                                                 f"Request size exceeds {self.settings.max_payload_size} bytes")
            
            # API key authentication (if enabled)
            if self.settings.enable_api_key_auth:
                api_key = request.headers.get(self.settings.api_key_header.lower())
                if not api_key or api_key not in self.settings.valid_api_keys:
                    self.metrics.increment_counter("unauthorized_request", tags={"ip": client_ip})
                    return self._create_error_response(401, "Unauthorized", "Invalid or missing API key")
            
            # Process request
            response = await call_next(request)
            
            # Record successful request metrics
            self.metrics.increment_counter("requests_processed", tags={"ip": client_ip})
            
            return response
            
        except Exception as exc:
            self.logger.error("Security middleware error", 
                            error=str(exc),
                            client_ip=client_ip,
                            exc_info=True)
            self.metrics.increment_counter("middleware_error", tags={"ip": client_ip})
            return self._create_error_response(500, "Internal server error", str(exc))
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check for forwarded headers first (for reverse proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _create_error_response(self, status_code: int, message: str, detail: str) -> JSONResponse:
        """Create standardized error response."""
        error_response = ErrorResponse(
            error=ErrorDetails(
                message=message,
                type="security_error",
                code=str(status_code),
                param=detail
            )
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.model_dump()
        )


class CORSMiddleware:
    """Enhanced CORS middleware with configuration."""
    
    def __init__(self, app, settings):
        self.app = app
        self.settings = settings
        self.logger = get_logger("motive_proxy.cors_middleware")
    
    async def __call__(self, scope, receive, send):
        """Handle CORS for requests."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            self._add_cors_headers(response, request)
            await response(scope, receive, send)
            return
        
        # Add CORS headers to all responses
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                self._add_cors_headers_to_dict(headers, request)
                # Ensure all headers are bytes
                message["headers"] = [(k.encode() if isinstance(k, str) else k, 
                                     v.encode() if isinstance(v, str) else v) 
                                    for k, v in headers.items()]
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
    
    def _add_cors_headers(self, response: Response, request: Request):
        """Add CORS headers to response."""
        origin = request.headers.get("origin")
        
        if self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
        elif "*" in self.settings.cors_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-Key"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"
    
    def _add_cors_headers_to_dict(self, headers: dict, request: Request):
        """Add CORS headers to headers dictionary."""
        origin = request.headers.get("origin")
        
        if self._is_origin_allowed(origin):
            headers["access-control-allow-origin"] = origin
        elif "*" in self.settings.cors_origins:
            headers["access-control-allow-origin"] = "*"
        
        headers["access-control-allow-methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        headers["access-control-allow-headers"] = "Content-Type, Authorization, X-API-Key"
        headers["access-control-allow-credentials"] = "true"
        headers["access-control-max-age"] = "86400"
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed."""
        if not origin:
            return False
        
        return origin in self.settings.cors_origins
