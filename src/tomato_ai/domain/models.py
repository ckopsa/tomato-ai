
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4


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

    def start(self):
        """
        Starts the session.
        """
        if self.state != "pending":
            raise ValueError("Session has already started")
        self.state = "active"
        self.start_time = datetime.now()

    def complete(self):
        """
        Completes the session.
        """
        if self.state != "active":
            raise ValueError("Session is not active")
        self.state = "completed"
        self.end_time = datetime.now()

    def pause(self):
        """
        Pauses the session.
        """
        if self.state != "active":
            raise ValueError("Session is not active")
        self.state = "paused"

    def resume(self):
        """
        Resumes the session.
        """
        if self.state != "paused":
            raise ValueError("Session is not paused")
        self.state = "active"


# Predefined session types
WORK = SessionType(type="work", default_duration=timedelta(minutes=25))
SHORT_BREAK = SessionType(type="short_break", default_duration=timedelta(minutes=5))
LONG_BREAK = SessionType(type="long_break", default_duration=timedelta(minutes=15))
