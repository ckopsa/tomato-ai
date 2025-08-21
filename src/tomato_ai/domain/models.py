from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone, time
from typing import Optional
from uuid import UUID, uuid4

from tomato_ai.domain import events


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
    session_type: str = "work"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    pause_start_time: Optional[datetime] = None
    total_paused_duration: timedelta = field(default_factory=timedelta)
    state: str = "pending"
    duration: timedelta = timedelta(minutes=25)
    task_id: Optional[UUID] = None
    events: list = field(default_factory=list, init=False)

    def start(self):
        """
        Starts the session.
        """
        if self.state != "pending":
            raise ValueError("Session has already started")
        self.state = "active"
        self.start_time = datetime.now(timezone.utc)
        self.expires_at = self.start_time + self.duration
        self.events.append(
            events.SessionStarted(session_id=self.session_id, user_id=self.user_id, session_type=self.session_type)
        )

    def complete(self):
        """
        Completes the session.
        """
        if self.state != "active":
            raise ValueError("Session is not active")
        self.state = "completed"
        self.end_time = datetime.now(timezone.utc)
        self.events.append(events.SessionCompleted(
            user_id=self.user_id,
            session_id=self.session_id,
            session_type=self.session_type,
        ))

    def pause(self):
        """
        Pauses the session.
        """
        if self.state != "active":
            raise ValueError("Session is not active")
        self.state = "paused"
        self.pause_start_time = datetime.now(timezone.utc)
        self.events.append(events.SessionPaused(session_id=self.session_id))

    def resume(self):
        """
        Resumes the session.
        """
        if self.state != "paused":
            raise ValueError("Session is not paused")
        if self.pause_start_time is None:
            raise ValueError("Session is not paused or pause_start_time is not set")
        self.state = "active"
        paused_duration = datetime.now(timezone.utc) - self.pause_start_time
        self.total_paused_duration += paused_duration
        if self.expires_at:
            self.expires_at += paused_duration
        self.pause_start_time = None
        self.events.append(events.SessionResumed(session_id=self.session_id))


# Predefined session types
WORK = SessionType(type="work", default_duration=timedelta(minutes=25))
SHORT_BREAK = SessionType(type="short_break", default_duration=timedelta(minutes=5))
LONG_BREAK = SessionType(type="long_break", default_duration=timedelta(minutes=15))


@dataclass
class User:
    telegram_chat_id: str
    id: UUID = field(default_factory=uuid4)
    timezone: str = "UTC"
    work_start: time = time(9, 0)
    work_end: time = time(17, 0)
    desired_sessions_per_day: int = 8
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
