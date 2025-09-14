"""Tests for observability features."""

import pytest
from fastapi.testclient import TestClient

from motive_proxy.app import create_app
from motive_proxy.observability import get_logger, get_metrics_collector, time_operation


class TestObservability:
    """Test observability features."""

    def test_structured_logging_setup(self):
        """Test that structured logging is properly configured."""
        logger = get_logger("test.logger")
        
        # Should not raise any exceptions
        logger.info("Test log message", test_field="test_value")
        assert True  # If we get here, logging works

    def test_metrics_collector(self):
        """Test metrics collection functionality."""
        collector = get_metrics_collector()
        
        # Test counter increment
        collector.increment_counter("test_counter", value=5)
        collector.increment_counter("test_counter", tags={"env": "test"})
        
        counters = collector.get_counters()
        assert counters["test_counter"] == 5
        assert counters["test_counter[env=test]"] == 1
        
        # Test timer recording
        collector.record_timer("test_timer", 1.5)
        collector.record_timer("test_timer", 2.0)
        
        timers = collector.get_timers()
        assert "test_timer" in timers
        assert timers["test_timer"]["count"] == 2
        assert timers["test_timer"]["min"] == 1.5
        assert timers["test_timer"]["max"] == 2.0
        assert timers["test_timer"]["avg"] == 1.75

    def test_timer_context_manager(self):
        """Test timer context manager."""
        collector = get_metrics_collector()
        
        with time_operation("context_timer", {"test": "value"}):
            import time
            time.sleep(0.01)  # Small delay
        
        timers = collector.get_timers()
        assert "context_timer[test=value]" in timers
        assert timers["context_timer[test=value]"]["count"] == 1

    def test_metrics_endpoint(self, client: TestClient):
        """Test that metrics endpoint returns data."""
        # Add some test metrics
        collector = get_metrics_collector()
        collector.increment_counter("test_endpoint_counter")
        collector.record_timer("test_endpoint_timer", 1.0)
        
        response = client.get("/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "counters" in data
        assert "timers" in data
        assert "test_endpoint_counter" in data["counters"]
        assert "test_endpoint_timer" in data["timers"]

    def test_health_endpoint_with_logging(self, client: TestClient):
        """Test that health endpoint works with logging."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_admin_sessions_with_logging(self, client: TestClient):
        """Test that admin sessions endpoint works with logging."""
        response = client.get("/admin/sessions")
        assert response.status_code == 200
        assert "sessions" in response.json()

    def test_chat_completions_with_logging(self, client: TestClient):
        """Test that chat completions endpoint includes logging."""
        request_data = {
            "model": "test-session",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        response = client.post("/v1/chat/completions", json=request_data)
        # Should timeout (408) since no counterpart, but logging should work
        assert response.status_code in [200, 408]
