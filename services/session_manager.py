"""
Session Management for Chat Context

Manages chat sessions and conversation history for continued interactions.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from models.schemas import ChatSession, ChatMessage


class SessionManager:
    """Manages chat sessions with conversation history"""

    def __init__(self, session_timeout_minutes: int = 60):
        """
        Initialize session manager.

        Args:
            session_timeout_minutes: Minutes before a session expires
        """
        self.sessions: Dict[str, ChatSession] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)

    def create_session(self) -> str:
        """
        Create a new chat session.

        Returns:
            session_id: Unique identifier for the session
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = ChatSession(session_id=session_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Get an existing session.

        Args:
            session_id: Session identifier

        Returns:
            ChatSession if found and not expired, None otherwise
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]

        # Check if session expired
        if datetime.now() - session.last_updated > self.session_timeout:
            # Clean up expired session
            del self.sessions[session_id]
            return None

        return session

    def get_or_create_session(self, session_id: Optional[str] = None) -> tuple[ChatSession, bool]:
        """
        Get existing session or create new one.

        Args:
            session_id: Optional session identifier

        Returns:
            Tuple of (ChatSession, is_new)
        """
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session, False

        # Create new session
        new_id = self.create_session()
        return self.sessions[new_id], True

    def add_user_message(self, session_id: str, message: str) -> None:
        """
        Add a user message to the session.

        Args:
            session_id: Session identifier
            message: User's message content
        """
        session = self.get_session(session_id)
        if session:
            session.add_message("user", message)

    def add_assistant_message(self, session_id: str, message: str) -> None:
        """
        Add an assistant message to the session.

        Args:
            session_id: Session identifier
            message: Assistant's message content
        """
        session = self.get_session(session_id)
        if session:
            session.add_message("assistant", message)

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        expired_ids = [
            sid for sid, session in self.sessions.items()
            if now - session.last_updated > self.session_timeout
        ]

        for sid in expired_ids:
            del self.sessions[sid]

        return len(expired_ids)

    def get_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)


# Global session manager instance
_session_manager = SessionManager(session_timeout_minutes=60)


def get_session_manager() -> SessionManager:
    """Get the global session manager instance"""
    return _session_manager
