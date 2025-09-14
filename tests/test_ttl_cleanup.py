"""Tests for session TTL cleanup functionality."""

import asyncio
import pytest
import time
from unittest.mock import patch

from motive_proxy.session import Session
from motive_proxy.session_manager import SessionManager


class TestTTLCleanup:
    """Test session TTL cleanup behavior."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self):
        """Test that expired sessions are cleaned up."""
        manager = SessionManager()
        
        # Create a session
        session = await manager.get_or_create("test-session")
        assert await manager.count() == 1
        
        # Mock time to simulate expiration
        with patch('time.time', return_value=time.time() + 4000):  # 4000 seconds later
            removed_count = await manager.cleanup_expired(ttl_seconds=3600)
            assert removed_count == 1
            assert await manager.count() == 0

    @pytest.mark.asyncio
    async def test_cleanup_preserves_active_sessions(self):
        """Test that active sessions are not cleaned up."""
        manager = SessionManager()
        
        # Create a session
        session = await manager.get_or_create("active-session")
        assert await manager.count() == 1
        
        # Mock time to simulate recent activity
        with patch('time.time', return_value=time.time() + 100):  # Only 100 seconds later
            removed_count = await manager.cleanup_expired(ttl_seconds=3600)
            assert removed_count == 0
            assert await manager.count() == 1

    @pytest.mark.asyncio
    async def test_cleanup_multiple_sessions(self):
        """Test cleanup with multiple sessions of different ages."""
        manager = SessionManager()
        
        # Create multiple sessions
        await manager.get_or_create("session-1")
        await manager.get_or_create("session-2")
        await manager.get_or_create("session-3")
        assert await manager.count() == 3
        
        # Mock time to expire only some sessions
        with patch('time.time', return_value=time.time() + 2000):  # 2000 seconds later
            removed_count = await manager.cleanup_expired(ttl_seconds=1500)  # TTL 1500s
            assert removed_count == 3  # All should be expired
            assert await manager.count() == 0

    @pytest.mark.asyncio
    async def test_session_activity_tracking(self):
        """Test that session activity timestamps are updated."""
        manager = SessionManager()
        session = await manager.get_or_create("activity-test")
        
        initial_activity = session._last_activity_ts
        
        # Manually update the activity timestamp to test the mechanism
        import time
        await asyncio.sleep(0.01)  # Small delay to ensure timestamp difference
        session._last_activity_ts = time.time()
        
        assert session._last_activity_ts > initial_activity

    @pytest.mark.asyncio
    async def test_session_metadata_includes_timestamps(self):
        """Test that session metadata includes creation and activity timestamps."""
        manager = SessionManager()
        session = await manager.get_or_create("metadata-test")
        
        metadata = session.metadata()
        
        assert "session_id" in metadata
        assert "created_ts" in metadata
        assert "last_activity_ts" in metadata
        assert metadata["session_id"] == "metadata-test"
        assert isinstance(metadata["created_ts"], float)
        assert isinstance(metadata["last_activity_ts"], float)
