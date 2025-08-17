
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PomodoroSessionCreate(BaseModel):
    user_id: UUID
    task_id: Optional[UUID] = None
    duration_seconds: Optional[int] = None


class PomodoroSessionRead(BaseModel):
    session_id: UUID
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    pause_start_time: Optional[datetime] = None
    total_paused_duration: timedelta
    state: str
    duration: timedelta
    user_id: UUID
    task_id: Optional[UUID] = None

    class Config:
        from_attributes = True

class PomodoroSessionUpdateState(BaseModel):
    state: str = Field(..., pattern=r"^(paused|resumed|completed)$")
