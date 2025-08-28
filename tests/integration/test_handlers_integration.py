import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from tomato_ai.adapters import orm
from tomato_ai.adapters.orm import Base
from tomato_ai.config import settings
from tomato_ai.domain import events
from tomato_ai.handlers import (
    send_telegram_notification_on_start, handle_nudge, start_session_command, not_now_button,
    send_telegram_notification, send_telegram_notification_on_expiration, schedule_nudge_on_session_completed,
    cancel_reminder_on_session_started, handle_message
)

# This test file is for integration tests, which make real calls to external services like Telegram and LLMs.
# For these tests to run, you need to have a .env file with the following variables:
# TELEGRAM_BOT_TOKEN: Your Telegram bot token
# TELEGRAM_CHAT_ID: A chat ID to send test messages to.
# OLLAMA_API_KEY: Your Ollama API key (if you are not running it locally)


# Create a new test engine, and create the tables
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
Base.metadata.create_all(bind=test_engine)

# Create a new session for the tests
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def dbsession() -> Session:
    """
    Creates a new database session for a test.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        # Clean up all data from all tables
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        db.close()


@pytest.fixture
def mock_update_and_context():
    """
    Provides a mock Update and Context object for handler tests.
    """
    update = AsyncMock()
    context = AsyncMock()
    return update, context


@pytest.mark.skipif(
    not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID,
    reason="TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env for integration tests"
)
class TestHandlerIntegration:
    @pytest.mark.asyncio
    async def test_send_telegram_notification_on_start(self, dbsession: Session):
        # Arrange
        user_id = uuid.uuid4()
        telegram_chat_id = settings.TELEGRAM_CHAT_ID
        user = orm.User(id=user_id, telegram_chat_id=telegram_chat_id)
        dbsession.add(user)
        dbsession.commit()

        event = events.SessionStarted(user_id=user_id, session_id=uuid.uuid4(), session_type="work")

        with patch("tomato_ai.handlers.get_session", return_value=iter([dbsession])):
            # Act & Assert: This should run without errors
            await send_telegram_notification_on_start(event)

    @pytest.mark.asyncio
    async def test_send_telegram_notification_on_session_completed(self, dbsession: Session):
        # Arrange
        user_id = uuid.uuid4()
        telegram_chat_id = settings.TELEGRAM_CHAT_ID
        user = orm.User(id=user_id, telegram_chat_id=telegram_chat_id)
        dbsession.add(user)
        dbsession.commit()

        event = events.SessionCompleted(user_id=user_id, session_id=uuid.uuid4(), session_type="work")

        with patch("tomato_ai.handlers.get_session", return_value=iter([dbsession])):
            # Act & Assert: This should run without errors
            await send_telegram_notification(event)

    @pytest.mark.asyncio
    async def test_send_telegram_notification_on_expiration(self, dbsession: Session):
        # Arrange
        user_id = uuid.uuid4()
        telegram_chat_id = settings.TELEGRAM_CHAT_ID
        user = orm.User(id=user_id, telegram_chat_id=telegram_chat_id)
        dbsession.add(user)
        dbsession.commit()

        event = events.SessionExpired(user_id=user_id, session_id=uuid.uuid4())

        with patch("tomato_ai.handlers.get_session", return_value=iter([dbsession])):
            # Act & Assert: This should run without errors
            await send_telegram_notification_on_expiration(event)

    def test_schedule_nudge_on_session_completed(self, dbsession: Session):
        # Arrange
        user_id = uuid.uuid4()
        session_id = uuid.uuid4()
        chat_id = int(settings.TELEGRAM_CHAT_ID)
        session = orm.PomodoroSession(
            session_id=session_id, user_id=user_id, chat_id=chat_id, state="completed",
            start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc) + timedelta(minutes=25),
            duration=timedelta(minutes=25)
        )
        dbsession.add(session)
        dbsession.commit()

        event = events.SessionCompleted(user_id=user_id, session_id=session_id, session_type="work")

        with patch("tomato_ai.handlers.get_session", return_value=iter([dbsession])):
            # Act
            schedule_nudge_on_session_completed(event)

            # Assert
            reminder = dbsession.query(orm.Reminder).one()
            assert reminder.user_id == user_id
            assert reminder.escalation_count == 1

    def test_cancel_reminder_on_session_started(self, dbsession: Session):
        # Arrange
        user_id = uuid.uuid4()
        chat_id = int(settings.TELEGRAM_CHAT_ID)
        reminder = orm.Reminder(user_id=user_id, chat_id=chat_id, send_at=datetime.now(timezone.utc))
        dbsession.add(reminder)
        dbsession.commit()

        event = events.SessionStarted(user_id=user_id, session_id=uuid.uuid4(), session_type="work")

        with patch("tomato_ai.handlers.get_session", return_value=iter([dbsession])):
            # Act
            cancel_reminder_on_session_started(event)

            # Assert
            reminder = dbsession.query(orm.Reminder).filter_by(user_id=user_id).first()
            assert reminder.state == "cancelled"

    @pytest.mark.asyncio
    async def test_handle_message(self, dbsession: Session, mock_update_and_context):
        update, context = mock_update_and_context
        telegram_chat_id = settings.TELEGRAM_CHAT_ID
        update.effective_chat.id = int(telegram_chat_id)
        update.message.text = "Hello, agent!"

        with patch("tomato_ai.handlers.get_session", return_value=iter([dbsession])):
            # Act & Assert
            await handle_message(update, context)
            context.bot.send_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_nudge_sends_message(self, dbsession: Session):
        # Arrange
        user_id = uuid.uuid4()
        telegram_chat_id = settings.TELEGRAM_CHAT_ID
        user = orm.User(id=user_id, telegram_chat_id=telegram_chat_id, timezone="UTC")
        dbsession.add(user)
        dbsession.commit()

        event = events.NudgeUser(user_id=user_id, chat_id=int(settings.TELEGRAM_CHAT_ID), escalation_count=1,
                                 session_type="work")

        with patch("tomato_ai.handlers.get_session", return_value=iter([dbsession])):
            # Act & Assert
            await handle_nudge(event)

    @pytest.mark.asyncio
    async def test_handle_nudge_escalates(self, dbsession: Session):
        # Arrange
        user_id = uuid.uuid4()
        telegram_chat_id = settings.TELEGRAM_CHAT_ID
        user = orm.User(id=user_id, telegram_chat_id=telegram_chat_id, timezone="UTC")
        dbsession.add(user)
        dbsession.commit()

        event = events.NudgeUser(user_id=user_id, chat_id=int(settings.TELEGRAM_CHAT_ID), escalation_count=1,
                                 session_type="work")

        with patch("tomato_ai.handlers.get_session", return_value=iter([dbsession])):
            # Act & Assert
            await handle_nudge(event)

    @pytest.mark.asyncio
    async def test_start_session_command(self, dbsession: Session, mock_update_and_context):
        update, context = mock_update_and_context
        telegram_chat_id = settings.TELEGRAM_CHAT_ID
        update.message.chat_id = int(telegram_chat_id)
        update.message.from_user.id = int(telegram_chat_id)

        with patch("tomato_ai.handlers.get_session", return_value=iter([dbsession])):
            await start_session_command(update, context, "work")

    @pytest.mark.asyncio
    async def test_not_now_button(self, dbsession: Session, mock_update_and_context):
        update, context = mock_update_and_context
        telegram_chat_id = settings.TELEGRAM_CHAT_ID
        update.callback_query.message.chat_id = int(telegram_chat_id)
        update.callback_query.from_user.id = int(telegram_chat_id)

        with patch("tomato_ai.handlers.get_session", return_value=iter([dbsession])):
            await not_now_button(update, context)

            # Verify a reminder was created
            reminder = dbsession.query(orm.Reminder).one_or_none()
            assert reminder is not None
            assert reminder.chat_id == int(telegram_chat_id)
