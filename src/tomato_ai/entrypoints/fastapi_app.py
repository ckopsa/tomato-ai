import asyncio
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from tomato_ai.adapters import database
from tomato_ai.domain.services import SessionManager
from tomato_ai.entrypoints.schemas import PomodoroSessionCreate, PomodoroSessionRead, PomodoroSessionUpdateState
from tomato_ai.adapters import orm, telegram, event_bus
from tomato_ai.domain import models, events
from tomato_ai.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    engine = database.get_engine()
    orm.Base.metadata.create_all(engine)
    app.state.db_engine = engine
    app.state.session_manager = SessionManager(uow=database.SqlAlchemyUnitOfWork())
    if settings.TELEGRAM_BOT_TOKEN:
        app.state.telegram_notifier = telegram.TelegramNotifier(
            token=settings.TELEGRAM_BOT_TOKEN,
        )
        await app.state.telegram_notifier.start()
    event_bus.register(events.SessionCompleted, lambda e: print(f"Session completed: {e}"))
    yield
    # Shutdown
    if hasattr(app.state, "telegram_notifier") and app.state.telegram_notifier:
        await app.state.telegram_notifier.stop()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    def get_session_manager(request: Request) -> SessionManager:
        return request.app.state.session_manager

    def get_session():
        with Session(app.state.db_engine) as session:
            yield session

    @app.get("/")
    def root():
        return {"message": "Hello Tomato AI"}

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    @app.post("/sessions/", response_model=PomodoroSessionRead)
    def create_session(
        session_data: PomodoroSessionCreate,
        db_session: Session = Depends(get_session),
        session_manager: SessionManager = Depends(get_session_manager),
    ):
        new_session = session_manager.start_new_session(
            user_id=session_data.user_id,
            task_id=session_data.task_id,
            duration=session_data.duration,
        )

        orm_session = orm.PomodoroSession(
            session_id=new_session.session_id,
            start_time=new_session.start_time,
            end_time=new_session.end_time,
            state=new_session.state,
            duration=new_session.duration,
            user_id=new_session.user_id,
            task_id=new_session.task_id,
            expires_at=new_session.expires_at,
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
    async def update_session_state(
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
            expires_at=orm_session.expires_at,
            remaining_duration_on_pause=orm_session.remaining_duration_on_pause,
        )

        original_state = domain_session.state
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
        orm_session.expires_at = domain_session.expires_at
        orm_session.remaining_duration_on_pause = (
            domain_session.remaining_duration_on_pause
        )

        db_session.commit()
        db_session.refresh(orm_session)

        if original_state != "completed" and domain_session.state == "completed":
            event_bus.publish(events.SessionCompleted(session_id=domain_session.session_id))
        return orm_session

    return app