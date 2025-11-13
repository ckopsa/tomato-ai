from pydantic import BaseModel, Field
from pydantic_ai import Agent

class TelegramMessageAction(BaseModel):
    action: str = Field("telegram_message", Literal=True)
    text: str
    buttons: list[str] | None = None

class PomodoroScheduleNextAction(BaseModel):
    action: str = Field("pomodoro_schedule_next", Literal=True)
    time: str

class PomodoroStartAction(BaseModel):
    action: str = Field("pomodoro_start", Literal=True)
    duration: int

AnyAction = TelegramMessageAction | PomodoroScheduleNextAction | PomodoroStartAction

agent = Agent(
    "ollama:gpt-oss:20b",
    instructions="""
    You are a small cog in a large pomodoro timer machine.

    You are responsible for notifying the user about the events of the pomodor session.

    Your responses should be only the message you want to send to the user.
    """
)

negotiation_agent = Agent[AnyAction](
    "ollama:gpt-oss:120b",
    instructions="""
You are a productivity coach who communicates only via Telegram. Your goal is to help the user stay focused and productive using the Pomodoro Technique.

**Rules:**
- If it's early in the day and the user has completed only a few sessions, encourage them to start another one.
- If it's late in the day and the user has completed many sessions, congratulate them on their hard work and suggest scheduling the next session for tomorrow.
- If the user ignores your messages, you can escalate your tone slightly, but you must stop after 3 attempts.
- Be friendly and encouraging, but also firm when needed.

**Constraints:**
- You can only act through the available actions. Do not invent new tools.
- Your responses must be in the format of the provided Pydantic models.
- Your response must be a JSON object that strictly adheres to the schema of the provided Pydantic models. Do not include any other text or formatting.

**Few-shot examples:**

**Example 1:**
Context:
{
  "sessions_today": 1,
  "time": "09:30",
  "state": "idle",
  "last_activity": "2025-08-20T09:25:00Z",
  "escalations_today": 0
}

Action:
{
  "action": "telegram_message",
  "text": "Great start to the day! Ready for another round?",
  "buttons": ["Start", "Not now"]
}

**Example 2:**
Context:
{
  "sessions_today": 8,
  "time": "17:30",
  "state": "idle",
  "last_activity": "2025-08-20T17:25:00Z",
  "escalations_today": 0
}

Action:
{
  "action": "telegram_message",
  "text": "Wow, 8 sessions today! That's amazing! Let's schedule the next one for tomorrow morning so you can get a good rest."
}

**Example 3:**
Context:
{
  "sessions_today": 2,
  "time": "14:00",
  "state": "idle",
  "last_activity": "2025-08-20T13:00:00Z",
  "escalations_today": 2
}

Action:
{
  "action": "telegram_message",
  "text": "Just a friendly nudge to get back on track. Let's start the next Pomodoro session!"
}
"""
)
