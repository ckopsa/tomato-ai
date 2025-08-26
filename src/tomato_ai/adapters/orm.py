from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, Interval, String, Uuid, Integer, Time
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PomodoroSession(Base):
    __tablename__ = "pomodoro_sessions"

    session_id = Column(Uuid, primary_key=True)
    chat_id = Column(Integer, nullable=False)
    session_type = Column(String, nullable=False, server_default="work")
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    pause_start_time = Column(DateTime(timezone=True), nullable=True)
    total_paused_duration = Column(Interval, nullable=False, default=timedelta(0))
    state = Column(String, nullable=False)
    duration = Column(Interval, nullable=False)
    user_id = Column(Uuid, nullable=False)
    task_id = Column(Uuid, nullable=True)


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Uuid, primary_key=True, default=uuid4)
    user_id = Column(Uuid, nullable=False)
    chat_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    send_at = Column(DateTime(timezone=True), nullable=True)
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    state = Column(String, nullable=False, default="pending")
    escalation_count = Column(Integer, nullable=False, default=0)


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid4)
    telegram_chat_id = Column(String, unique=True, nullable=False)
    timezone = Column(String, nullable=False, server_default="UTC")
    work_start = Column(Time, nullable=False, server_default="09:00:00")
    work_end = Column(Time, nullable=False, server_default="17:00:00")
    desired_sessions_per_day = Column(Integer, nullable=False, server_default="8")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


def start_mappers():
    pass  # For now, we are using active record pattern


class Message(Base):
    __tablename__ = "messages"

    id = Column(Uuid, primary_key=True, default=uuid4)
    user_id = Column(Uuid, nullable=False)
    chat_id = Column(Integer, nullable=False)
    message = Column(String, nullable=False)
    sender = Column(String, nullable=False)  # "user" or "agent"
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
