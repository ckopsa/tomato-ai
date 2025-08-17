
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from tomato_ai.adapters import event_bus, orm
from tomato_ai.domain import events, models
from tomato_ai.domain.models import PomodoroSession, WORK


class SessionManager:
    """
    A domain service for managing Pomodoro sessions.
    """

    def start_new_session(self, user_id: UUID, task_id: UUID | None = None) -> PomodoroSession:
        """
        Starts a new Pomodoro session.
        """
        session = PomodoroSession(
            user_id=user_id,
            task_id=task_id,
            duration=WORK.default_duration,
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
            if orm_session.expires_at and orm_session.expires_at < datetime.now():
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
