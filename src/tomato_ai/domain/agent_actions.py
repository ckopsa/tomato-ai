from pydantic import BaseModel, Field
from typing import Literal, Optional, Union


class TelegramMessageAction(BaseModel):
    action: Literal["telegram_message"] = "telegram_message"
    text: str
    buttons: Optional[list[str]] = None


class PomodoroScheduleNextAction(BaseModel):
    action: Literal["pomodoro_schedule_next"] = "pomodoro_schedule_next"
    time: str  # e.g. "15m", "1h", "tomorrow"


class PomodoroStartAction(BaseModel):
    action: Literal["pomodoro_start"] = "pomodoro_start"
    duration: int = 25


AgentAction = Union[TelegramMessageAction, PomodoroScheduleNextAction, PomodoroStartAction]
