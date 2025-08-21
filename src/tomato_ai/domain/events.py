from dataclasses import dataclass
from uuid import UUID


class Event:
    """
    Base class for domain events.
    """
    pass


@dataclass(frozen=True)
class SessionStarted(Event):
    """
    Event raised when a session starts.
    """
    session_id: UUID
    user_id: UUID
    session_type: str


@dataclass(frozen=True)
class NudgeUser(Event):
    """
    Event raised to nudge the user.
    """
    user_id: UUID
    chat_id: int
    escalation_count: int
    session_type: str


@dataclass(frozen=True)
class SessionCompleted(Event):
    """
    Event raised when a session is completed.
    """
    session_id: UUID
    user_id: UUID
    session_type: str


@dataclass(frozen=True)
class SessionPaused(Event):
    """
    Event raised when a session is paused.
    """
    session_id: UUID


@dataclass(frozen=True)
class SessionResumed(Event):
    """
    Event raised when a session is resumed.
    """
    session_id: UUID


@dataclass(frozen=True)
class SessionExpired(Event):
    """
    Event raised when a session expires.
    """
    session_id: UUID
    user_id: UUID
