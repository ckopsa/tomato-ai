
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID, uuid4

from tomato_ai.domain import events as domain_events


@dataclass(frozen=True)
class SessionType:
    """
    A value object representing the type of a session.
    """
    type: str
    default_duration: timedelta


@dataclass
class PomodoroSession:
    """
    An entity representing a Pomodoro session.
    """

    user_id: UUID
    session_id: UUID = field(default_factory=uuid4)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    state: str = "pending"
    duration: timedelta = timedelta(minutes=25)
    task_id: Optional[UUID] = None
    events: list[domain_events.Event] = field(default_factory=list)

    def start(self):
        """
        Starts the session.
        """
        if self.state != "pending":
            raise ValueError("Session has already started")
        self.state = "active"
        self.start_time = datetime.now()
        self.events.append(
            domain_events.SessionStarted(session_id=self.session_id, user_id=self.user_id)
        )

    def complete(self):
        """
        Completes the session.
        """
        if self.state != "active":
            raise ValueError("Session is not active")
        self.state = "completed"
        self.end_time = datetime.now()
        self.events.append(domain_events.SessionCompleted(session_id=self.session_id))

    def pause(self):
        """
        Pauses the session.
        """
        if self.state != "active":
            raise ValueError("Session is not active")
        self.state = "paused"
        self.events.append(domain_events.SessionPaused(session_id=self.session_id))

    def resume(self):
        """
        Resumes the session.
        """
        if self.state != "paused":
            raise ValueError("Session is not paused")
        self.state = "active"
        self.events.append(domain_events.SessionResumed(session_id=self.session_id))


# Predefined session types
WORK = SessionType(type="work", default_duration=timedelta(minutes=25))
SHORT_BREAK = SessionType(type="short_break", default_duration=timedelta(minutes=5))
LONG_BREAK = SessionType(type="long_break", default_duration=timedelta(minutes=15))
