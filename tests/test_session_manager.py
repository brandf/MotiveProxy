"""Tests for session management functionality."""

from unittest.mock import AsyncMock, Mock

import pytest

from motive_proxy.session_manager import Session, SessionManager


class TestSession:
    """Test cases for the Session class."""

    def test_session_creation(self):
        """Test that a session can be created with required parameters."""
        session_id = "test-session-123"
        session = Session(session_id=session_id)

        assert session.session_id == session_id
        assert session.human_client is None
        assert session.program_client is None
        assert session.is_human_connected() is False
        assert session.is_program_connected() is False
        assert session.is_ready() is False

    def test_session_human_connection(self):
        """Test connecting a human client to a session."""
        session = Session(session_id="test-session")
        mock_human = Mock()

        session.connect_human(mock_human)

        assert session.human_client == mock_human
        assert session.is_human_connected() is True
        assert session.is_ready() is False  # Still waiting for program

    def test_session_program_connection(self):
        """Test connecting a program client to a session."""
        session = Session(session_id="test-session")
        mock_program = Mock()

        session.connect_program(mock_program)

        assert session.program_client == mock_program
        assert session.is_program_connected() is True
        assert session.is_ready() is False  # Still waiting for human

    def test_session_both_connected(self):
        """Test that a session is ready when both clients are connected."""
        session = Session(session_id="test-session")
        mock_human = Mock()
        mock_program = Mock()

        session.connect_human(mock_human)
        session.connect_program(mock_program)

        assert session.is_human_connected() is True
        assert session.is_program_connected() is True
        assert session.is_ready() is True

    def test_session_disconnection(self):
        """Test disconnecting clients from a session."""
        session = Session(session_id="test-session")
        mock_human = Mock()
        mock_program = Mock()

        session.connect_human(mock_human)
        session.connect_program(mock_program)

        session.disconnect_human()
        assert session.is_human_connected() is False
        assert session.is_ready() is False

        session.disconnect_program()
        assert session.is_program_connected() is False
        assert session.is_ready() is False


class TestSessionManager:
    """Test cases for the SessionManager class."""

    def test_session_manager_creation(self):
        """Test that a session manager can be created."""
        manager = SessionManager()
        assert manager is not None
        assert len(manager.sessions) == 0

    def test_create_session(self):
        """Test creating a new session."""
        manager = SessionManager()
        session_id = "test-session-123"

        session = manager.create_session(session_id)

        assert session.session_id == session_id
        assert session_id in manager.sessions
        assert manager.sessions[session_id] == session

    def test_get_existing_session(self):
        """Test retrieving an existing session."""
        manager = SessionManager()
        session_id = "test-session-123"

        created_session = manager.create_session(session_id)
        retrieved_session = manager.get_session(session_id)

        assert retrieved_session == created_session

    def test_get_nonexistent_session(self):
        """Test retrieving a session that doesn't exist."""
        manager = SessionManager()

        session = manager.get_session("nonexistent-session")

        assert session is None

    def test_cleanup_inactive_sessions(self):
        """Test cleaning up inactive sessions."""
        manager = SessionManager()
        session_id = "test-session-123"

        manager.create_session(session_id)
        assert session_id in manager.sessions

        # Simulate session becoming inactive (no clients connected)
        manager.cleanup_inactive_sessions()

        # Session should still exist (cleanup logic will be implemented later)
        assert session_id in manager.sessions
