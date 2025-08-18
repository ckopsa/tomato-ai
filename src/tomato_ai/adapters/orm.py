
from sqlalchemy import Column, DateTime, Interval, String, Uuid
from sqlalchemy.orm import declarative_base
from datetime import timedelta

Base = declarative_base()


class PomodoroSession(Base):
    __tablename__ = "pomodoro_sessions"

    session_id = Column(Uuid, primary_key=True)
    session_type = Column(String, nullable=False, server_default="work")
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    pause_start_time = Column(DateTime, nullable=True)
    total_paused_duration = Column(Interval, nullable=False, default=timedelta(0))
    state = Column(String, nullable=False)
    duration = Column(Interval, nullable=False)
    user_id = Column(Uuid, nullable=False)
    task_id = Column(Uuid, nullable=True)


def start_mappers():
    pass  # For now, we are using active record pattern
