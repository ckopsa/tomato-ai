
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PomodoroSessionCreate(BaseModel):
    user_id: UUID
    task_id: Optional[UUID] = None
    session_type: str = "work"


from pydantic import computed_field

class PomodoroSessionRead(BaseModel):
    session_id: UUID
    session_type: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    pause_start_time: Optional[datetime] = None
    total_paused_duration: timedelta
    state: str
    duration: timedelta
    user_id: UUID
    task_id: Optional[UUID] = None

    @computed_field
    @property
    def duration_seconds(self) -> int:
        return int(self.duration.total_seconds())

    @computed_field
    @property
    def total_paused_duration_seconds(self) -> int:
        return int(self.total_paused_duration.total_seconds())

    class Config:
        from_attributes = True

class PomodoroSessionUpdateState(BaseModel):
    state: str = Field(..., pattern=r"^(paused|resumed|completed)$")
