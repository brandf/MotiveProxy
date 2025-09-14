"""Session management for human-in-the-loop interactions."""

from dataclasses import dataclass
from typing import Dict, Optional
from unittest.mock import Mock


@dataclass
class Session:
    """Represents a session between a human and a program client."""

    session_id: str
    human_client: Optional[Mock] = None
    program_client: Optional[Mock] = None

    def is_human_connected(self) -> bool:
        """Check if a human client is connected to this session."""
        return self.human_client is not None

    def is_program_connected(self) -> bool:
        """Check if a program client is connected to this session."""
        return self.program_client is not None

    def is_ready(self) -> bool:
        """Check if both human and program clients are connected."""
        return self.is_human_connected() and self.is_program_connected()

    def connect_human(self, client: Mock) -> None:
        """Connect a human client to this session."""
        self.human_client = client

    def connect_program(self, client: Mock) -> None:
        """Connect a program client to this session."""
        self.program_client = client

    def disconnect_human(self) -> None:
        """Disconnect the human client from this session."""
        self.human_client = None

    def disconnect_program(self) -> None:
        """Disconnect the program client from this session."""
        self.program_client = None


class SessionManager:
    """Manages sessions for human-in-the-loop interactions."""

    def __init__(self):
        """Initialize the session manager."""
        self.sessions: Dict[str, Session] = {}

    def create_session(self, session_id: str) -> Session:
        """Create a new session with the given ID."""
        session = Session(session_id=session_id)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get an existing session by ID."""
        return self.sessions.get(session_id)

    def cleanup_inactive_sessions(self) -> None:
        """Clean up sessions that have no active connections."""
        # TODO: Implement cleanup logic for inactive sessions
        # For now, we'll keep all sessions
        pass
