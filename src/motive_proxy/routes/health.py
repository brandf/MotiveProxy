"""Health check endpoint."""

from fastapi import APIRouter, Request

from motive_proxy.observability import get_logger, get_metrics_collector

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    logger = get_logger("motive_proxy.health")
    logger.debug("Health check requested")
    return {"status": "healthy"}


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
