import logging
from datetime import datetime, timezone
from uuid import UUID

from strands import Agent
from strands.session.file_session_manager import FileSessionManager
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram import Update
from telegram.ext import CallbackContext
from tomato_ai.adapters import telegram, orm
from tomato_ai.adapters.database import get_session
from tomato_ai.agents import turbo_20_ollama_model
from tomato_ai.config import settings
from tomato_ai.domain import events
from tomato_ai.domain.services import SessionManager

logger = logging.getLogger(__name__)


def get_agent(session_id: str):
    return Agent(
        model=turbo_20_ollama_model,
        session_manager=FileSessionManager(session_id),
        system_prompt="""
    You are a small cog in a large pomodoro timer machine.
    
    You are responsible for notifying the user about the events of the pomodor session.
    
    Your reponses should be only the message you want to send to the user.
    """
    )


def log_event(event: events.Event):
    """
    A simple event handler that logs the event.
    """
    logger.info(f"Handled event: {event}")


async def send_telegram_notification(event: events.SessionCompleted):
    """
    Sends a telegram notification when a session is completed.
    """
    if (notifier := telegram.get_telegram_notifier()) and settings.TELEGRAM_CHAT_ID:
        await notifier.send_message(
            chat_id=settings.TELEGRAM_CHAT_ID,
            message=str(get_agent(str(event.user_id))(
                f"The user completed the pomodoro session of type {event.session_type}!")),
        )


async def send_telegram_notification_on_start(event: events.SessionStarted):
    """
    Sends a telegram notification when a session starts.
    """
    if (notifier := telegram.get_telegram_notifier()) and settings.TELEGRAM_CHAT_ID:
        await notifier.send_message(
            chat_id=str(int(event.user_id)),
            message=str(
                get_agent(str(event.user_id))(f"The user started a pomodoro session of type {event.session_type}!")),
        )


async def send_telegram_notification_on_expiration(event: events.SessionExpired):
    """
    Sends a telegram notification when a session expires.
    """
    if (notifier := telegram.get_telegram_notifier()) and settings.TELEGRAM_CHAT_ID:
        await notifier.send_message(
            chat_id=settings.TELEGRAM_CHAT_ID,
            message=f"Pomodoro session {event.session_id} has expired!",
        )


async def start_session_command(update: Update, context: CallbackContext, session_type: str) -> None:
    """
    Handles the /start command, starting a new pomodoro session.
    """
    if update.message and update.message.from_user:
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id

        session_manager = SessionManager()
        # This is a hack to convert telegram's integer user_id to a UUID.
        # A proper implementation would have a user management system.
        user_uuid = UUID(int=user_id)

        new_session = session_manager.start_new_session(user_id=user_uuid, session_type=session_type)

        db_session = next(get_session())
        orm_session = orm.PomodoroSession(
            session_id=new_session.session_id,
            start_time=new_session.start_time,
            end_time=new_session.end_time,
            state=new_session.state,
            duration=new_session.duration,
            user_id=new_session.user_id,
            task_id=new_session.task_id,
            expires_at=new_session.expires_at,
            pause_start_time=new_session.pause_start_time,
            total_paused_duration=new_session.total_paused_duration,
            session_type=new_session.session_type,
        )

        db_session.add(orm_session)
        db_session.commit()
        db_session.refresh(orm_session)

        # We don't publish the SessionStarted event to avoid a duplicate notification
        # because we are sending a direct message to the user.
        # for event in new_session.events:
        #     if not isinstance(event, events.SessionStarted):
        #         await event_bus.publish(event)

        if (notifier := telegram.get_telegram_notifier()):
            duration_minutes = new_session.duration.total_seconds() / 60
            start_ts = int(new_session.start_time.timestamp())
            nd_ts = int((datetime.now(timezone.utc) + new_session.duration).timestamp())  # end time in seconds

            message = (
                f"{new_session.session_type.replace('_', ' ').title()} session started! "
                f"It will last for {duration_minutes:.0f} minutes."
            )

            # Inline keyboard with WebApp button
            keyboard = [
                [InlineKeyboardButton(
                    text="⏳ Open Timer",
                    web_app=WebAppInfo(url=f"https://tomato.kopsa.info/telegram-mini-app?start={start_ts}end={end_ts}")
                )]
            ]

            await notifier.send_message(
                chat_id=str(chat_id),
                message=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )


async def start_command(update: Update, context: CallbackContext) -> None:
    """
    Handles the /start command, starting a new pomodoro session.
    """
    await start_session_command(update, context, "work")


async def start_short_break_command(update: Update, context: CallbackContext) -> None:
    """
    Handles the /short_break command, starting a new short break session.
    """
    await start_session_command(update, context, "short_break")


async def start_long_break_command(update: Update, context: CallbackContext) -> None:
    """
    Handles the /long_break command, starting a new long break session.
    """
    await start_session_command(update, context, "long_break")


async def handle_message(update: Update, context: CallbackContext) -> None:
    """
    Handles incoming messages and responds with a simple echo.
    """
    if update.message and update.message.text:
        user_message = update.message.text
        agent_response = get_agent(str(update.effective_chat.id))(user_message)
        response = str(agent_response)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
