
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PomodoroSessionCreate(BaseModel):
    user_id: UUID
    task_id: Optional[UUID] = None
    duration: Optional[int] = None


class PomodoroSessionRead(BaseModel):
    session_id: UUID
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    state: str
    duration: timedelta
    user_id: UUID
    task_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None
    remaining_duration_on_pause: Optional[timedelta] = None

    class Config:
        from_attributes = True

class PomodoroSessionUpdateState(BaseModel):
    state: str = Field(..., pattern=r"^(paused|resumed|completed)$")
