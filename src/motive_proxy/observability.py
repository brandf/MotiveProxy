"""Observability utilities for logging and metrics."""

import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from fastapi import Request


def setup_logging() -> None:
    """Configure structured logging with JSON output."""
    # Ensure logs directory exists
    logs_dir = Path("logs/motive-proxy")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging with file handler
    log_file = logs_dir / "motive-proxy.log"
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also log to console
        ]
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def extract_request_context(request: Request) -> Dict[str, Any]:
    """Extract relevant context from FastAPI request."""
    return {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing."""
    return str(uuid.uuid4())


class MetricsCollector:
    """Simple metrics collector for counters and timers."""
    
    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._timers: Dict[str, list] = {}
        self._lock = None  # Would use threading.Lock in production
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        key = self._make_key(name, tags)
        self._counters[key] = self._counters.get(key, 0) + value
    
    def record_timer(self, name: str, duration_seconds: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a timer metric."""
        key = self._make_key(name, tags)
        if key not in self._timers:
            self._timers[key] = []
        self._timers[key].append(duration_seconds)
    
    def get_counters(self) -> Dict[str, int]:
        """Get all counter values."""
        return self._counters.copy()
    
    def get_timers(self) -> Dict[str, Dict[str, float]]:
        """Get timer statistics (count, min, max, avg)."""
        result = {}
        for key, values in self._timers.items():
            if values:
                result[key] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                }
        return result
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Create a key for metrics with optional tags."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"


# Global metrics collector instance
_metrics = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics


class TimerContext:
    """Context manager for timing operations."""
    
    def __init__(self, name: str, tags: Optional[Dict[str, str]] = None):
        self.name = name
        self.tags = tags
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            get_metrics_collector().record_timer(self.name, duration, self.tags)


def time_operation(name: str, tags: Optional[Dict[str, str]] = None) -> TimerContext:
    """Create a timer context for timing operations."""
    return TimerContext(name, tags)
