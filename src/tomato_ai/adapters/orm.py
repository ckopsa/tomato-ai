from sqlalchemy import Column, DateTime, Interval, String, Uuid, TypeDecorator
from sqlalchemy.orm import declarative_base
from datetime import timedelta, datetime, timezone

Base = declarative_base()


class TzAwareDateTime(TypeDecorator):
    """
    A TypeDecorator for storing timezone-aware datetimes in the database.
    """
    impl = DateTime(timezone=True)

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is None:
            raise TypeError("tzinfo is required")
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class PomodoroSession(Base):
    __tablename__ = "pomodoro_sessions"

    session_id = Column(Uuid, primary_key=True)
    start_time = Column(TzAwareDateTime, nullable=True)
    end_time = Column(TzAwareDateTime, nullable=True)
    expires_at = Column(TzAwareDateTime, nullable=True)
    pause_start_time = Column(TzAwareDateTime, nullable=True)
    total_paused_duration = Column(Interval, nullable=False, default=timedelta(0))
    state = Column(String, nullable=False)
    duration = Column(Interval, nullable=False)
    user_id = Column(Uuid, nullable=False)
    task_id = Column(Uuid, nullable=True)


def start_mappers():
    pass  # For now, we are using active record pattern
