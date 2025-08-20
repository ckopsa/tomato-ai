from pydantic import BaseModel


class NotificationDelay(BaseModel):
    delay_in_minutes: int
