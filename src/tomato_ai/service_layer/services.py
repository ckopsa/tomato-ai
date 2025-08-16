from uuid import UUID
from tomato_ai.domain import models
from tomato_ai.adapters import orm
from tomato_ai.service_layer import unit_of_work, event_bus
from tomato_ai.domain.services import SessionManager


class SessionNotFound(Exception):
    pass


def create_session(
    user_id: UUID,
    task_id: UUID | None,
    uow: unit_of_work.SqlAlchemyUnitOfWork,
) -> models.PomodoroSession:
    with uow:
        session_manager = SessionManager()
        domain_session = session_manager.start_new_session(
            user_id=user_id, task_id=task_id
        )

        orm_session = orm.PomodoroSession(
            session_id=domain_session.session_id,
            start_time=domain_session.start_time,
            end_time=domain_session.end_time,
            state=domain_session.state,
            duration=domain_session.duration,
            user_id=domain_session.user_id,
            task_id=domain_session.task_id,
        )

        uow.session.add(orm_session)
        uow.commit()

        for event in domain_session.events:
            event_bus.publish(event)

        return domain_session


def update_session_state(
    session_id: UUID,
    state: str,
    uow: unit_of_work.SqlAlchemyUnitOfWork,
) -> models.PomodoroSession:
    with uow:
        orm_session = uow.session.get(orm.PomodoroSession, session_id)
        if orm_session is None:
            raise SessionNotFound(f"Session with id {session_id} not found")

        # Map ORM model to domain model
        domain_session = models.PomodoroSession(
            user_id=orm_session.user_id,
            session_id=orm_session.session_id,
            start_time=orm_session.start_time,
            end_time=orm_session.end_time,
            state=orm_session.state,
            duration=orm_session.duration,
            task_id=orm_session.task_id,
        )

        # Call domain logic
        try:
            if state == "paused":
                domain_session.pause()
            elif state == "resumed":
                domain_session.resume()
            elif state == "completed":
                domain_session.complete()
            else:
                raise ValueError(f"Invalid state transition: {state}")
        except ValueError as e:
            raise e

        # Update ORM model from domain model
        orm_session.state = domain_session.state
        orm_session.end_time = domain_session.end_time

        uow.commit()

        # Publish events
        for event in domain_session.events:
            event_bus.publish(event)

        return domain_session
