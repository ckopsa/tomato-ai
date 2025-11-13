import logging
import zoneinfo
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from time import strftime

from pydantic_ai import Agent
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram import WebAppInfo
from telegram.ext import CallbackContext

from tomato_ai.adapters import telegram, orm
from tomato_ai.adapters.database import get_session
from tomato_ai.agents import negotiation_agent, TelegramMessageAction, PomodoroScheduleNextAction, PomodoroStartAction
from tomato_ai.config import settings
from tomato_ai.domain import events
from tomato_ai.domain.services import SessionManager, ReminderService

logger = logging.getLogger(__name__)

agent_sessions: dict[str, Agent] = {}
scheduler_agent_sessions: dict[str, Agent] = {}

def get_agent(session_id: str) -> Agent:
    if session_id not in agent_sessions:
        agent_sessions[session_id] = Agent(
            "ollama:gpt-oss:20b",
            instructions="""
            You are a small cog in a large pomodoro timer machine.

            You are responsible for notifying the user about the events of the pomodor session.

            Your responses should be only the message you want to send to the user.
            """
        )
    return agent_sessions[session_id]

class DelayContainer(BaseModel):
    delay_in_minutes: int

def get_scheduler_agent(session_id: str) -> Agent[DelayContainer]:
    if session_id not in scheduler_agent_sessions:
        scheduler_agent_sessions[session_id] = Agent[DelayContainer](
            "ollama:gpt-oss:120b",
            instructions="""
            You are responsible for scheduling reminders for the user. You want the user to be diligent in their adherence to pomodoro sessions.
            You should be stubborn, but not annoying in reminding the user to stay in their pomodoro workflow.

            Use whatever context you have to decide the delay for the reminder.

            Using the is to decide a single number 'delay_in_minutes' for the reminder.
            """,
        )
    return scheduler_agent_sessions[session_id]


def parse_time(time_str: str) -> timedelta:
    if time_str.endswith("m"):
        return timedelta(minutes=int(time_str[:-1]))
    elif time_str.endswith("h"):
        return timedelta(hours=int(time_str[:-1]))
    elif time_str == "tomorrow":
        return timedelta(days=1)
    else:
        return timedelta(minutes=15)  # default


def log_event(event: events.Event):
    """
    A simple event handler that logs the event.
    """
    logger.info(f"Handled event: {event}")


async def send_telegram_notification(event: events.SessionCompleted):
    """
    Sends a telegram notification when a session is completed.
    """
    db_session = next(get_session())
    user = db_session.query(orm.User).filter_by(id=event.user_id).first()
    if not user:
        logger.error(f"User with id {event.user_id} not found.")
        return

    if notifier := telegram.get_telegram_notifier():
        agent = get_agent(str(user.telegram_chat_id))
        result = await agent.run(f"The user completed the pomodoro session of type {event.session_type}!")
        await notifier.send_message(
            chat_id=user.telegram_chat_id,
            message=result.output,
        )


async def send_telegram_notification_on_start(event: events.SessionStarted):
    """
    Sends a telegram notification when a session starts.
    """
    db_session = next(get_session())
    user = db_session.query(orm.User).filter_by(id=event.user_id).first()
    if not user:
        logger.error(f"User with id {event.user_id} not found.")
        return

    if notifier := telegram.get_telegram_notifier():
        agent = get_agent(str(user.telegram_chat_id))
        result = await agent.run(f"The user started a pomodoro session of type {event.session_type}!")
        await notifier.send_message(
            chat_id=user.telegram_chat_id,
            message=result.output,
        )


async def send_telegram_notification_on_expiration(event: events.SessionExpired):
    """
    Sends a telegram notification when a session expires.
    """
    db_session = next(get_session())
    user = db_session.query(orm.User).filter_by(id=event.user_id).first()
    if not user:
        logger.error(f"User with id {event.user_id} not found.")
        return

    if notifier := telegram.get_telegram_notifier():
        await notifier.send_message(
            chat_id=user.telegram_chat_id,
            message=f"Pomodoro session {event.session_id} has expired!",
        )


def schedule_nudge_on_session_completed(event: events.SessionCompleted):
    """
    Schedules a nudge when a session is completed.
    """
    db_session = next(get_session())
    session = db_session.query(orm.PomodoroSession).filter_by(session_id=event.session_id).first()
    if session:
        delay_minutes = 3
        reminder_service = ReminderService(db_session)
        send_at = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
        reminder_service.schedule_reminder(event.user_id, session.chat_id, send_at, escalation_count=1)


def cancel_reminder_on_session_started(event: events.SessionStarted):
    """
    Cancels any pending reminders when a session starts.
    """
    db_session = next(get_session())
    reminder_service = ReminderService(db_session)
    reminder_service.cancel_reminder(event.user_id)


async def handle_nudge(event: events.NudgeUser):
    """
    Handles a nudge event.
    """
    logger.info(f"Handling nudge for user {event.user_id}")
    db_session = next(get_session())
    user = db_session.query(orm.User).filter_by(id=event.user_id).first()

    if event.escalation_count >= settings.MAX_ESCALATIONS:
        logger.info(f"Max escalations reached for user {event.user_id}")
        if notifier := telegram.get_telegram_notifier():
            await notifier.send_message(
                chat_id=str(user.telegram_chat_id),
                message="Looks like today’s a tough one — let’s pick this back up tomorrow morning.",
            )
        reminder_service = ReminderService(db_session)
        send_at = datetime.now(timezone.utc) + timedelta(days=1)
        reminder_service.schedule_reminder(event.user_id, event.chat_id, send_at)
        return

    try:
        user_zone_info: zoneinfo.ZoneInfo = zoneinfo.ZoneInfo(user.timezone)
    except zoneinfo.ZoneInfoNotFoundError:
        user_zone_info: zoneinfo.ZoneInfo = zoneinfo.ZoneInfo("UTC")

    # 1. Gather context
    today = datetime.now(user_zone_info).date()
    sessions_today = (
        db_session.query(orm.PomodoroSession)
        .filter(
            orm.PomodoroSession.user_id == event.user_id,
            orm.PomodoroSession.state == "completed",
            orm.PomodoroSession.start_time >= datetime.combine(today, datetime.min.time(), tzinfo=user_zone_info),
        )
        .count()
    )
    last_session = (
        db_session.query(orm.PomodoroSession)
        .filter(orm.PomodoroSession.user_id == event.user_id, orm.PomodoroSession.state == "completed")
        .order_by(orm.PomodoroSession.end_time.desc())
        .first()
    )
    last_activity = last_session.end_time.astimezone(user_zone_info).strftime("%A, %B %d, %Y %I:%M %p") if last_session else ""

    context = {
        "sessions_today": sessions_today,
        "time": datetime.now(user_zone_info).strftime("%A, %B %d, %Y %I:%M %p"),
        "state": "idle",
        "last_activity": last_activity,
        "escalations_today": event.escalation_count,
        "desired_sessions": user.desired_sessions_per_day
    }

    # 2. Call the negotiation agent
    result = await negotiation_agent.run(str(context))
    action = result.output

    # 3. Execute the action
    if isinstance(action, TelegramMessageAction):
        if notifier := telegram.get_telegram_notifier():
            keyboard = []
            if action.buttons:
                keyboard = [
                    [InlineKeyboardButton(text=button, callback_data=button.lower()) for button in action.buttons]
                ]

            await notifier.send_message(
                chat_id=str(event.chat_id),
                message=action.text,
                reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
            )
        # Schedule the next nudge if the user doesn't respond
        reminder_service = ReminderService(db_session)
        send_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        reminder_service.schedule_reminder(
            event.user_id, event.chat_id, send_at, escalation_count=event.escalation_count + 1
        )

    elif isinstance(action, PomodoroScheduleNextAction):
        scheduler_agent = get_scheduler_agent(str(event.chat_id))
        scheduler_context = {
            "negotiation_agent_output": action.model_dump(),
            "user_history": context,
        }
        try:
            result = await scheduler_agent.run(str(scheduler_context))
            delay_container = result.output
            delay_in_minutes = int(delay_container.delay_in_minutes)
        except Exception:
            logger.warning("Could not parse delay from scheduler agent, defaulting to 15 minutes.")
            delay_in_minutes = 15

        reminder_service = ReminderService(db_session)
        delay = timedelta(minutes=delay_in_minutes)
        send_at = datetime.now(timezone.utc) + delay
        reminder_service.schedule_reminder(
            event.user_id, event.chat_id, send_at, escalation_count=event.escalation_count + 1
        )
    elif isinstance(action, PomodoroStartAction):
        if notifier := telegram.get_telegram_notifier():
            keyboard = [[InlineKeyboardButton(text="Start", callback_data="start")]]
            await notifier.send_message(
                chat_id=str(event.chat_id),
                message="Ready to start a new session?",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
    else:
        logger.warning(f"Unhandled action type: {action}")


async def start_session_command(update: Update, context: CallbackContext, session_type: str) -> None:
    """
    Handles the /start command, starting a new pomodoro session.
    """
    if update.message and update.message.from_user:
        telegram_chat_id = str(update.message.chat_id)
        db_session = next(get_session())

        user = db_session.query(orm.User).filter_by(telegram_chat_id=telegram_chat_id).first()
        if not user:
            user = orm.User(telegram_chat_id=telegram_chat_id)
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)

        session_manager = SessionManager()

        new_session = session_manager.start_new_session(user_id=user.id, session_type=session_type)

        orm_session = orm.PomodoroSession(
            session_id=new_session.session_id,
            chat_id=int(telegram_chat_id),
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

        if (notifier := telegram.get_telegram_notifier()):
            duration_minutes = new_session.duration.total_seconds() / 60
            start_ts = int(new_session.start_time.timestamp())
            end_ts = int((new_session.start_time + new_session.duration).timestamp())  # end time in seconds

            message = (
                f"{new_session.session_type.replace('_', ' ').title()} session started! "
                f"It will last for {duration_minutes:.0f} minutes."
            )

            keyboard = [
                [InlineKeyboardButton(
                    text="⏳ Open Timer",
                    web_app=WebAppInfo(url=f"https://tomato.kopsa.info/telegram-mini-app?start={start_ts}&end={end_ts}")
                )]
            ]

            await notifier.send_message(
                chat_id=telegram_chat_id,
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
        agent = get_agent(str(update.effective_chat.id))
        result = await agent.run(user_message)
        response = result.output
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def start_button(update: Update, context: CallbackContext) -> None:
    """
    Handles the 'Start' button press.
    """
    await start_session_command(update, context, "work")


async def not_now_button(update: Update, context: CallbackContext) -> None:
    """
    Handles the 'Not now' button press.
    """
    query = update.callback_query
    await query.answer()

    db_session = next(get_session())
    reminder_service = ReminderService(db_session)
    send_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    if query.message:
        telegram_chat_id = str(query.message.chat_id)
        user = db_session.query(orm.User).filter_by(telegram_chat_id=telegram_chat_id).first()
        if not user:
            user = orm.User(telegram_chat_id=telegram_chat_id)
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)

        reminder_service.schedule_reminder(user.id, int(telegram_chat_id), send_at, escalation_count=1)
        await query.edit_message_text(text="OK, I'll remind you in 15 minutes.")
