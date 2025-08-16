from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from tomato_ai.adapters.database import get_session
from tomato_ai.adapters import orm
from tomato_ai.entrypoints.schemas import (
    PomodoroSessionCreate,
    PomodoroSessionRead,
    PomodoroSessionUpdateState,
)
from tomato_ai.service_layer import services, unit_of_work


def get_uow():
    return unit_of_work.SqlAlchemyUnitOfWork()


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/")
    def root():
        return {"message": "Hello Tomato AI"}

    @app.post("/sessions/", response_model=PomodoroSessionRead)
    def create_session(
        session_data: PomodoroSessionCreate,
        uow: unit_of_work.SqlAlchemyUnitOfWork = Depends(get_uow),
    ):
        try:
            session = services.create_session(
                user_id=session_data.user_id,
                task_id=session_data.task_id,
                uow=uow,
            )
            return session
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/sessions/{session_id}", response_model=PomodoroSessionRead)
    def get_session_by_id(
        session_id: UUID,
        db_session: Session = Depends(get_session),
    ):
        session = db_session.get(orm.PomodoroSession, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

    @app.put("/sessions/{session_id}/state", response_model=PomodoroSessionRead)
    def update_session_state(
        session_id: UUID,
        state_data: PomodoroSessionUpdateState,
        uow: unit_of_work.SqlAlchemyUnitOfWork = Depends(get_uow),
    ):
        try:
            session = services.update_session_state(
                session_id=session_id,
                state=state_data.state,
                uow=uow,
            )
            return session
        except services.SessionNotFound as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return app