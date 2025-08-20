
from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy.orm import Session

from tomato_ai.adapters import event_bus, orm, telegram
from tomato_ai.domain import events, models
from tomato_ai.domain.models import PomodoroSession, WORK, SHORT_BREAK, LONG_BREAK


class SessionManager:
    """
    A domain service for managing Pomodoro sessions.
    """

    def start_new_session(
        self, user_id: UUID, task_id: UUID | None = None, session_type: str = "work"
    ) -> PomodoroSession:
        """
        Starts a new Pomodoro session.
        """
        session_types = {
            "work": WORK,
            "short_break": SHORT_BREAK,
            "long_break": LONG_BREAK,
        }
        selected_session_type = session_types.get(session_type, WORK)

        session = PomodoroSession(
            user_id=user_id,
            task_id=task_id,
            session_type=selected_session_type.type,
            duration=selected_session_type.default_duration,
        )
        session.start()
        return session


class SessionNotifier:
    """
    A domain service for notifying users about session events.
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session

    async def check_and_notify_expired_sessions(self):
        """
        Checks for expired sessions and notifies the user.
        """
        active_sessions = self.db_session.query(orm.PomodoroSession).filter_by(state="active").all()
        for orm_session in active_sessions:
            if orm_session.expires_at and orm_session.expires_at < datetime.now(timezone.utc):
                domain_session = models.PomodoroSession(
                    user_id=orm_session.user_id,
                    session_id=orm_session.session_id,
                    start_time=orm_session.start_time,
                    end_time=orm_session.end_time,
                    state=orm_session.state,
                    duration=orm_session.duration,
                    task_id=orm_session.task_id,
                    expires_at=orm_session.expires_at,
                    pause_start_time=orm_session.pause_start_time,
                    total_paused_duration=orm_session.total_paused_duration,
                )
                domain_session.complete()
                orm_session.state = domain_session.state
                orm_session.end_time = domain_session.end_time

                for event in domain_session.events:
                    await event_bus.publish(event)

                await event_bus.publish(
                    events.SessionExpired(session_id=domain_session.session_id, user_id=domain_session.user_id)
                )
                self.db_session.add(orm_session)
        self.db_session.commit()


class ReminderNotifier:
    """
    A domain service for notifying users about reminders.
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session

    async def check_and_send_reminders(self):
        """
        Checks for pending reminders and sends a notification if the user does not have an active session.
        """
        now = datetime.now(timezone.utc)
        pending_reminders = (
            self.db_session.query(orm.Reminder)
            .filter(orm.Reminder.state == "pending", orm.Reminder.send_at <= now)
            .all()
        )
        for reminder in pending_reminders:
            active_session = (
                self.db_session.query(orm.PomodoroSession)
                .filter_by(user_id=reminder.user_id, state="active")
                .first()
            )
            if not active_session:
                if notifier := telegram.get_telegram_notifier():
                    await notifier.send_message(
                        chat_id=reminder.chat_id,
                        message="You don't have an active pomodoro session. Would you like to start one?",
                    )
            reminder.state = "triggered"
            reminder.triggered_at = now
            self.db_session.add(reminder)
        self.db_session.commit()


from uuid import uuid4

class ReminderService:
    """
    A domain service for scheduling and canceling reminders.
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def schedule_reminder(self, user_id: UUID, chat_id: int, send_at: datetime):
        """
        Schedules a reminder for the user.
        """
        reminder = orm.Reminder(
            id=uuid4(),
            user_id=user_id,
            chat_id=chat_id,
            created_at=datetime.now(timezone.utc),
            send_at=send_at,
            state="pending",
        )
        self.db_session.add(reminder)
        self.db_session.commit()

    def cancel_reminder(self, user_id: UUID):
        """
        Cancels any pending reminders for the user.
        """
        reminders = self.db_session.query(orm.Reminder).filter_by(user_id=user_id, state="pending").all()
        for reminder in reminders:
            reminder.state = "cancelled"
            self.db_session.add(reminder)
        self.db_session.commit()
