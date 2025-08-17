import asyncio
import logging

from strands import Agent
from tomato_ai.adapters import telegram
from tomato_ai.config import settings
from tomato_ai.domain import events
from tomato_ai.agents import turbo_20_ollama_model

agent = Agent(
    model=turbo_20_ollama_model,
    system_prompt="""
    You are a small cog in a large pomodoro timer machine.
    
    You are responsible for notifying the user about the events of the pomodor session.
    
    Your reponses should be only the message you want to send to the user.
    """
)

logger = logging.getLogger(__name__)


def log_event(event: events.Event):
    """
    A simple event handler that logs the event.
    """
    logger.info(f"Handled event: {event}")


def send_telegram_notification(event: events.SessionCompleted):
    """
    Sends a telegram notification when a session is completed.
    """
    if (notifier := telegram.get_telegram_notifier()) and settings.TELEGRAM_CHAT_ID:
        asyncio.run(
            notifier.send_message(
                chat_id=settings.TELEGRAM_CHAT_ID,
                message=str(agent("The user completed the pomodoro session!")),
            )
        )


def send_telegram_notification_on_start(event: events.SessionStarted):
    """
    Sends a telegram notification when a session starts.
    """
    if (notifier := telegram.get_telegram_notifier()) and settings.TELEGRAM_CHAT_ID:
        asyncio.run(
            notifier.send_message(
                chat_id=settings.TELEGRAM_CHAT_ID,
                message=str(agent("The user started a pomodoro session!")),
            )
        )


def send_telegram_notification_on_expiration(event: events.SessionExpired):
    """
    Sends a telegram notification when a session expires.
    """
    if (notifier := telegram.get_telegram_notifier()) and settings.TELEGRAM_CHAT_ID:
        asyncio.run(
            notifier.send_message(
                chat_id=settings.TELEGRAM_CHAT_ID,
                message=f"Pomodoro session {event.session_id} has expired!",
            )
        )
