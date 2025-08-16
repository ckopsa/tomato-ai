from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from tomato_ai.adapters.database import get_engine, get_session
from tomato_ai.adapters.orm import Base
from tomato_ai.domain.services import SessionManager
from tomato_ai.entrypoints.schemas import PomodoroSessionCreate, PomodoroSessionRead, PomodoroSessionUpdateState
from tomato_ai.adapters import orm
from tomato_ai.domain import models
from tomato_ai.config import settings


def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    @app.get("/")
    def root():
        return {"message": "Hello Tomato AI"}

    @app.post("/sessions/", response_model=PomodoroSessionRead)
    def create_session(
        session_data: PomodoroSessionCreate,
        db_session: Session = Depends(get_session),
    ):
        session_manager = SessionManager()
        new_session = session_manager.start_new_session(
            user_id=session_data.user_id, task_id=session_data.task_id
        )

        orm_session = orm.PomodoroSession(
            session_id=new_session.session_id,
            start_time=new_session.start_time,
            end_time=new_session.end_time,
            state=new_session.state,
            duration=new_session.duration,
            user_id=new_session.user_id,
            task_id=new_session.task_id,
        )

        db_session.add(orm_session)
        db_session.commit()
        db_session.refresh(orm_session)
        return orm_session

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
        db_session: Session = Depends(get_session),
    ):
        orm_session = db_session.get(orm.PomodoroSession, session_id)
        if orm_session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        domain_session = models.PomodoroSession(
            user_id=orm_session.user_id,
            session_id=orm_session.session_id,
            start_time=orm_session.start_time,
            end_time=orm_session.end_time,
            state=orm_session.state,
            duration=orm_session.duration,
            task_id=orm_session.task_id,
        )

        try:
            if state_data.state == "paused":
                domain_session.pause()
            elif state_data.state == "resumed":
                domain_session.resume()
            elif state_data.state == "completed":
                domain_session.complete()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        orm_session.state = domain_session.state
        orm_session.end_time = domain_session.end_time

        db_session.commit()
        db_session.refresh(orm_session)
        return orm_session

    return app