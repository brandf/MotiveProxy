"""Rate limiting functionality for MotiveProxy."""

import time
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque

from motive_proxy.observability import get_logger


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    window_size_seconds: int = 60


@dataclass
class RateLimitEntry:
    """Rate limit tracking entry."""
    requests: deque = field(default_factory=deque)
    last_cleanup: float = field(default_factory=time.time)
    
    def add_request(self, timestamp: float):
        """Add a request timestamp."""
        self.requests.append(timestamp)
        self._cleanup_old_requests(timestamp)
    
    def _cleanup_old_requests(self, current_time: float):
        """Remove requests older than the window."""
        cutoff_time = current_time - 3600  # 1 hour window
        while self.requests and self.requests[0] < cutoff_time:
            self.requests.popleft()
    
    def get_recent_requests(self, window_seconds: int, current_time: float) -> int:
        """Get number of requests in the last window_seconds."""
        cutoff_time = current_time - window_seconds
        return sum(1 for req_time in self.requests if req_time >= cutoff_time)


class RateLimiter:
    """Rate limiter for requests per IP/session."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.logger = get_logger("motive_proxy.rate_limiter")
        self._limits: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, identifier: str) -> tuple[bool, Optional[str]]:
        """
        Check if request is allowed for the given identifier.
        
        Returns:
            (is_allowed, reason_if_blocked)
        """
        async with self._lock:
            current_time = time.time()
            entry = self._limits[identifier]
            
            # Add current request
            entry.add_request(current_time)
            
            # Check burst limit (last 10 seconds)
            recent_requests = entry.get_recent_requests(10, current_time)
            if recent_requests > self.config.burst_limit:
                self.logger.warning("Rate limit exceeded: burst limit", 
                                  identifier=identifier,
                                  recent_requests=recent_requests,
                                  limit=self.config.burst_limit)
                return False, "Burst limit exceeded"
            
            # Check per-minute limit
            minute_requests = entry.get_recent_requests(60, current_time)
            if minute_requests > self.config.requests_per_minute:
                self.logger.warning("Rate limit exceeded: per minute", 
                                  identifier=identifier,
                                  minute_requests=minute_requests,
                                  limit=self.config.requests_per_minute)
                return False, "Rate limit exceeded: too many requests per minute"
            
            # Check per-hour limit
            hour_requests = entry.get_recent_requests(3600, current_time)
            if hour_requests > self.config.requests_per_hour:
                self.logger.warning("Rate limit exceeded: per hour", 
                                  identifier=identifier,
                                  hour_requests=hour_requests,
                                  limit=self.config.requests_per_hour)
                return False, "Rate limit exceeded: too many requests per hour"
            
            return True, None
    
    async def get_stats(self, identifier: str) -> Dict[str, int]:
        """Get rate limit statistics for an identifier."""
        async with self._lock:
            current_time = time.time()
            entry = self._limits.get(identifier, RateLimitEntry())
            
            return {
                "requests_last_minute": entry.get_recent_requests(60, current_time),
                "requests_last_hour": entry.get_recent_requests(3600, current_time),
                "requests_last_10_seconds": entry.get_recent_requests(10, current_time),
                "total_tracked_requests": len(entry.requests),
            }
    
    async def cleanup_old_entries(self):
        """Clean up old rate limit entries."""
        async with self._lock:
            current_time = time.time()
            cutoff_time = current_time - 7200  # 2 hours
            
            # Remove entries that haven't been used recently
            to_remove = []
            for identifier, entry in self._limits.items():
                if not entry.requests or entry.requests[-1] < cutoff_time:
                    to_remove.append(identifier)
            
            for identifier in to_remove:
                del self._limits[identifier]
            
            if to_remove:
                self.logger.info("Cleaned up old rate limit entries", 
                               removed_count=len(to_remove))
