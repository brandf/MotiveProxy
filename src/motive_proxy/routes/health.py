"""Health check endpoint."""

from fastapi import APIRouter, Request
import time
import psutil

from motive_proxy.observability import get_logger, get_metrics_collector
from motive_proxy.settings import get_settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    logger = get_logger("motive_proxy.health")
    logger.debug("Health check requested")
    return {"status": "healthy"}


@router.get("/health/detailed")
async def detailed_health_check(request: Request):
    """Detailed health check with system information."""
    logger = get_logger("motive_proxy.health")
    logger.info("Detailed health check requested", 
               client_ip=request.client.host if request.client else None)
    
    settings = get_settings()
    
    # Get system information
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
    except Exception as exc:
        logger.warning("Failed to get system metrics", error=str(exc))
        cpu_percent = 0
        memory = type('Memory', (), {'percent': 0, 'available': 0})()
        disk = type('Disk', (), {'percent': 0, 'free': 0})()
    
    # Get session manager stats
    session_manager = request.app.state.session_manager
    active_sessions = await session_manager.count()
    
    # Get metrics
    metrics_collector = get_metrics_collector()
    counters = metrics_collector.get_counters()
    timers = metrics_collector.get_timers()
    
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "0.1.0",
        "uptime_seconds": time.time() - getattr(request.app.state, 'start_time', time.time()),
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available // (1024 * 1024),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free // (1024 * 1024 * 1024),
        },
        "sessions": {
            "active_count": active_sessions,
            "max_sessions": settings.max_sessions,
            "session_ttl_seconds": settings.session_ttl_seconds,
        },
        "metrics": {
            "total_requests": counters.get("requests_processed", 0),
            "rate_limited_requests": counters.get("rate_limit_exceeded", 0),
            "payload_too_large_requests": counters.get("payload_too_large", 0),
            "unauthorized_requests": counters.get("unauthorized_request", 0),
        },
        "configuration": {
            "rate_limiting_enabled": settings.enable_rate_limiting,
            "api_key_auth_enabled": settings.enable_api_key_auth,
            "max_payload_size_mb": settings.max_payload_size // (1024 * 1024),
            "log_level": settings.log_level,
        }
    }


@router.get("/admin/sessions")
async def list_sessions(request: Request):
    """Admin endpoint returning active sessions metadata (redacted)."""
    logger = get_logger("motive_proxy.admin")
    logger.info("Admin sessions endpoint accessed", 
               client_ip=request.client.host if request.client else None)
    
    session_manager = request.app.state.session_manager
    sessions = await session_manager.list_sessions()
    
    logger.info("Sessions listed", session_count=len(sessions))
    return {"sessions": sessions}


@router.get("/metrics")
async def get_metrics():
    """Metrics endpoint for observability."""
    logger = get_logger("motive_proxy.metrics")
    logger.debug("Metrics endpoint accessed")
    
    metrics_collector = get_metrics_collector()
    return {
        "counters": metrics_collector.get_counters(),
        "timers": metrics_collector.get_timers(),
    }
