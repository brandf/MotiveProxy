"""Session management for human-in-the-loop interactions."""

from __future__ import annotations

import asyncio
from typing import Dict, List

from motive_proxy.session import Session


class SessionManager:
    """Manages sessions for human-in-the-loop interactions."""

    def __init__(self,
                 handshake_timeout_seconds: float = 30.0,
                 turn_timeout_seconds: float = 30.0,
                 max_sessions: int = 100) -> None:
        self._sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()
        self._handshake_timeout = handshake_timeout_seconds
        self._turn_timeout = turn_timeout_seconds
        self._max_sessions = max_sessions

    async def get_or_create(self, session_id: str) -> Session:
        """Get or create a session safely under a lock."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is not None:
                return session
            if len(self._sessions) >= self._max_sessions:
                # Simple guard; more graceful error handling can be added later
                raise RuntimeError("Max sessions limit reached")
            session = Session(
                session_id=session_id,
                handshake_timeout_seconds=self._handshake_timeout,
                turn_timeout_seconds=self._turn_timeout,
            )
            self._sessions[session_id] = session
            return session

    async def close(self, session_id: str) -> None:
        async with self._lock:
            self._sessions.pop(session_id, None)

    async def count(self) -> int:
        async with self._lock:
            return len(self._sessions)

    async def list_sessions(self) -> List[dict]:
        """Return metadata for active sessions (redacted)."""
        async with self._lock:
            return [s.metadata() for s in self._sessions.values()]

    async def cleanup_expired(self, ttl_seconds: float) -> int:
        """Remove sessions idle longer than ttl_seconds. Returns count removed."""
        import time
        async with self._lock:
            now = time.time()
            to_delete = [sid for sid, s in self._sessions.items() if (now - s._last_activity_ts) > ttl_seconds]
            for sid in to_delete:
                self._sessions.pop(sid, None)
            return len(to_delete)
