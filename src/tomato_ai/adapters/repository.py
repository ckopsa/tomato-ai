from typing import Protocol
from uuid import UUID

from tomato_ai.domain import models
from tomato_ai.adapters import orm


class AbstractRepository(Protocol):
    def get(self, session_id: UUID) -> models.PomodoroSession:
        ...

    def add(self, session: models.PomodoroSession):
        ...


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def get(self, session_id: UUID) -> models.PomodoroSession:
        orm_session = (
            self.session.query(orm.PomodoroSession)
            .filter_by(session_id=session_id)
            .one()
        )
        return models.PomodoroSession(
            user_id=orm_session.user_id,
            session_id=orm_session.session_id,
            start_time=orm_session.start_time,
            end_time=orm_session.end_time,
            state=orm_session.state,
            duration=orm_session.duration,
            task_id=orm_session.task_id,
            pause_start_time=orm_session.pause_start_time,
        )

    def add(self, session: models.PomodoroSession):
        orm_session = orm.PomodoroSession(
            user_id=session.user_id,
            session_id=session.session_id,
            start_time=session.start_time,
            end_time=session.end_time,
            state=session.state,
            duration=session.duration,
            task_id=session.task_id,
            pause_start_time=session.pause_start_time,
        )
        self.session.add(orm_session)
