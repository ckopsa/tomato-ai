from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler
from telegram.ext import filters

from tomato_ai import handlers
from tomato_ai.adapters import orm, event_bus
from tomato_ai.adapters.database import get_session
from tomato_ai.app_state import scheduler
from tomato_ai.config import settings
from tomato_ai.domain import models
from tomato_ai.domain.services import SessionManager, SessionNotifier
from tomato_ai.entrypoints.schemas import PomodoroSessionCreate, PomodoroSessionRead, PomodoroSessionUpdateState


async def run_scheduler():
    db_session = next(get_session())
    notifier = SessionNotifier(db_session)
    await notifier.check_and_notify_expired_sessions()


async def lifespan(app: FastAPI):
    scheduler.add_job(run_scheduler, "interval", seconds=10)
    scheduler.start()

    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_TOKEN != "dummy-token":
        ptb_app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
        ptb_app.add_handler(CommandHandler("start", handlers.start_command))
        ptb_app.add_handler(CommandHandler("break", handlers.start_short_break_command))
        ptb_app.add_handler(CommandHandler("short_break", handlers.start_short_break_command))
        ptb_app.add_handler(CommandHandler("long_break", handlers.start_long_break_command))
        await ptb_app.initialize()
        app.state.ptb_app = ptb_app

    yield

    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_TOKEN != "dummy-token":
        await app.state.ptb_app.shutdown()
    scheduler.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.mount("/static", StaticFiles(directory="telegram_mini_app"), name="telegram_mini_app")

    @app.get("/telegram-mini-app")
    async def get_pomodoro():
        return FileResponse("telegram_mini_app/index.html")

    @app.get("/")
    def root():
        return {"message": "Hello Tomato AI"}

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    @app.post("/sessions/", response_model=PomodoroSessionRead)
    async def create_session(
            session_data: PomodoroSessionCreate,
            db_session: Session = Depends(get_session),
    ):
        session_manager = SessionManager()
        new_session = session_manager.start_new_session(
            user_id=session_data.user_id,
            task_id=session_data.task_id,
            session_type=session_data.session_type,
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
            pause_start_time=new_session.pause_start_time,
            total_paused_duration=new_session.total_paused_duration,
            session_type=new_session.session_type,
        )

        db_session.add(orm_session)
        db_session.commit()
        db_session.refresh(orm_session)

        for event in new_session.events:
            await event_bus.publish(event)

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
            pause_start_time=orm_session.pause_start_time,
            total_paused_duration=orm_session.total_paused_duration,
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
        orm_session.pause_start_time = domain_session.pause_start_time
        orm_session.total_paused_duration = domain_session.total_paused_duration

        db_session.commit()
        db_session.refresh(orm_session)

        for event in domain_session.events:
            await event_bus.publish(event)
        return orm_session

    if settings.TELEGRAM_BOT_TOKEN:
        @app.post("/telegram/webhook")
        async def telegram_webhook(request: Request):
            ptb_app = request.app.state.ptb_app
            update_data = await request.json()
            update = Update.de_json(update_data, ptb_app.bot)
            await ptb_app.process_update(update)
            return {"status": "ok"}

    return app
