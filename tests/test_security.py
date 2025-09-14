"""Tests for security features: rate limiting, payload size, auth."""

import pytest
import time
from fastapi.testclient import TestClient

from motive_proxy.rate_limiter import RateLimiter, RateLimitConfig
from motive_proxy.middleware import SecurityMiddleware
from motive_proxy.settings import Settings


class TestRateLimiter:
    """Test rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_normal_requests(self):
        """Test that normal requests are allowed."""
        config = RateLimitConfig(requests_per_minute=60, requests_per_hour=1000, burst_limit=10)
        limiter = RateLimiter(config)
        
        # Make several requests quickly
        for _ in range(5):
            is_allowed, reason = await limiter.is_allowed("test-ip")
            assert is_allowed is True
            assert reason is None

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_burst_limit(self):
        """Test that burst limit is enforced."""
        config = RateLimitConfig(requests_per_minute=60, requests_per_hour=1000, burst_limit=5)
        limiter = RateLimiter(config)
        
        # Make requests within burst limit
        for _ in range(5):
            is_allowed, reason = await limiter.is_allowed("test-ip")
            assert is_allowed is True
        
        # This should be blocked
        is_allowed, reason = await limiter.is_allowed("test-ip")
        assert is_allowed is False
        assert "Burst limit exceeded" in reason

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_per_minute_limit(self):
        """Test that per-minute limit is enforced."""
        config = RateLimitConfig(requests_per_minute=5, requests_per_hour=1000, burst_limit=10)
        limiter = RateLimiter(config)
        
        # Make requests up to the limit
        for _ in range(5):
            is_allowed, reason = await limiter.is_allowed("test-ip")
            assert is_allowed is True
        
        # This should be blocked
        is_allowed, reason = await limiter.is_allowed("test-ip")
        assert is_allowed is False
        assert "per minute" in reason

    @pytest.mark.asyncio
    async def test_rate_limiter_different_ips(self):
        """Test that different IPs have separate limits."""
        config = RateLimitConfig(requests_per_minute=5, requests_per_hour=1000, burst_limit=10)
        limiter = RateLimiter(config)
        
        # Exhaust limit for first IP
        for _ in range(5):
            is_allowed, reason = await limiter.is_allowed("ip1")
            assert is_allowed is True
        
        # First IP should be blocked
        is_allowed, reason = await limiter.is_allowed("ip1")
        assert is_allowed is False
        
        # Second IP should still be allowed
        is_allowed, reason = await limiter.is_allowed("ip2")
        assert is_allowed is True

    @pytest.mark.asyncio
    async def test_rate_limiter_stats(self):
        """Test rate limiter statistics."""
        config = RateLimitConfig(requests_per_minute=60, requests_per_hour=1000, burst_limit=10)
        limiter = RateLimiter(config)
        
        # Make some requests
        for _ in range(3):
            await limiter.is_allowed("test-ip")
        
        stats = await limiter.get_stats("test-ip")
        assert stats["requests_last_minute"] == 3
        assert stats["requests_last_hour"] == 3
        assert stats["requests_last_10_seconds"] == 3
        assert stats["total_tracked_requests"] == 3


class TestSecurityMiddleware:
    """Test security middleware functionality."""

    def test_security_middleware_health_endpoint_bypass(self, client: TestClient):
        """Test that health endpoints bypass security checks."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_security_middleware_metrics_endpoint_bypass(self, client: TestClient):
        """Test that metrics endpoints bypass security checks."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_security_middleware_payload_size_limit(self, client: TestClient):
        """Test payload size limit enforcement."""
        # Create a large payload (over 1MB default limit)
        large_content = "x" * (2 * 1024 * 1024)  # 2MB
        large_request = {
            "model": "test-session",
            "messages": [{"role": "user", "content": large_content}]
        }
        
        response = client.post("/v1/chat/completions", json=large_request)
        assert response.status_code == 413
        assert "Payload too large" in response.json()["error"]["message"]

    def test_security_middleware_rate_limiting(self, client: TestClient):
        """Test rate limiting enforcement."""
        request_data = {
            "model": "test-session",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        # Make many requests quickly to trigger rate limiting
        responses = []
        for _ in range(15):  # Exceed burst limit of 10
            response = client.post("/v1/chat/completions", json=request_data)
            responses.append(response)
        
        # Some requests should be rate limited
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0
        
        # Check error format
        if rate_limited_responses:
            error_response = rate_limited_responses[0].json()
            assert "Rate limit exceeded" in error_response["error"]["message"]

    def test_security_middleware_api_key_auth_disabled(self, client: TestClient):
        """Test that API key auth is disabled by default."""
        request_data = {
            "model": "test-session",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        # Should work without API key (auth disabled by default)
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code in [200, 408]  # 408 is expected due to no counterpart

    def test_security_middleware_cors_headers(self, client: TestClient):
        """Test CORS headers are present."""
        response = client.options("/v1/chat/completions")
        assert response.status_code == 200
        
        # Check CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers


class TestHealthEndpoints:
    """Test enhanced health endpoints."""

    def test_basic_health_endpoint(self, client: TestClient):
        """Test basic health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_detailed_health_endpoint(self, client: TestClient):
        """Test detailed health endpoint."""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "system" in data
        assert "sessions" in data
        assert "metrics" in data
        assert "configuration" in data
        
        # Check system metrics
        system = data["system"]
        assert "cpu_percent" in system
        assert "memory_percent" in system
        assert "memory_available_mb" in system
        
        # Check session info
        sessions = data["sessions"]
        assert "active_count" in sessions
        assert "max_sessions" in sessions
        assert "session_ttl_seconds" in sessions
        
        # Check metrics
        metrics = data["metrics"]
        assert "total_requests" in metrics
        assert "rate_limited_requests" in metrics
        assert "payload_too_large_requests" in metrics
        assert "unauthorized_requests" in metrics
        
        # Check configuration
        config = data["configuration"]
        assert "rate_limiting_enabled" in config
        assert "api_key_auth_enabled" in config
        assert "max_payload_size_mb" in config
        assert "log_level" in config

    def test_admin_sessions_endpoint(self, client: TestClient):
        """Test admin sessions endpoint."""
        response = client.get("/admin/sessions")
        assert response.status_code == 200
        
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)


class TestSecurityIntegration:
    """Test security features integration."""

    def test_security_middleware_with_real_requests(self, client: TestClient):
        """Test security middleware with real API requests."""
        # Test normal request
        request_data = {
            "model": "test-session",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code in [200, 408]  # 408 expected due to no counterpart
        
        # Test invalid request (should get 422, not security error)
        invalid_request = {
            "model": "test-session",
            "messages": []  # Empty messages should trigger validation error
        }
        
        response = client.post("/v1/chat/completions", json=invalid_request)
        assert response.status_code == 422

    def test_security_middleware_error_format(self, client: TestClient):
        """Test that security errors have consistent format."""
        # Trigger payload size error
        large_content = "x" * (2 * 1024 * 1024)  # 2MB
        large_request = {
            "model": "test-session",
            "messages": [{"role": "user", "content": large_content}]
        }
        
        response = client.post("/v1/chat/completions", json=large_request)
        assert response.status_code == 413
        
        error_data = response.json()
        assert "error" in error_data
        assert "message" in error_data["error"]
        assert "type" in error_data["error"]
        assert "code" in error_data["error"]
        assert error_data["error"]["type"] == "security_error"
