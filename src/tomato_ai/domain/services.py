
from uuid import UUID
from tomato_ai.domain.models import PomodoroSession, WORK
from tomato_ai.domain.uow import UnitOfWork


class SessionManager:
    """
    A domain service for managing Pomodoro sessions.
    """

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def start_new_session(
        self, user_id: UUID, task_id: UUID | None = None, duration: int | None = None
    ) -> PomodoroSession:
        """
        Starts a new Pomodoro session.
        """
        from datetime import timedelta

        session = PomodoroSession(
            user_id=user_id,
            task_id=task_id,
            duration=timedelta(seconds=duration)
            if duration
            else WORK.default_duration,
        )
        session.start()
        return session

    def complete_session(self, session_id: UUID):
        """
        Completes a session.
        """
        with self._uow:
            session = self._uow.repository.get(session_id)
            session.complete()
            self._uow.commit()
