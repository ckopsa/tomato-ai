
from uuid import UUID
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
