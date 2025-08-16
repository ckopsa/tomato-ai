import logging
import asyncio

from tomato_ai.domain import events
from tomato_ai.adapters import telegram
from tomato_ai.config import settings


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
        loop = asyncio.get_running_loop()
        loop.create_task(
            notifier.send_message(
                chat_id=settings.TELEGRAM_CHAT_ID,
                message=f"Pomodoro session {event.session_id} completed!",
            )
        )


def send_telegram_notification_on_start(event: events.SessionStarted):
    """
    Sends a telegram notification when a session starts.
    """
    if (notifier := telegram.get_telegram_notifier()) and settings.TELEGRAM_CHAT_ID:
        loop = asyncio.get_running_loop()
        loop.create_task(
            notifier.send_message(
                chat_id=settings.TELEGRAM_CHAT_ID,
                message=f"Pomodoro session {event.session_id} started!",
            )
        )
