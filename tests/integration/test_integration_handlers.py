import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone

from tomato_ai.domain import events
from tomato_ai.domain.agent_actions import TelegramMessageAction, PomodoroScheduleNextAction
from tomato_ai.handlers import start_session_command, handle_nudge, not_now_button
from tomato_ai.adapters import orm
from tomato_ai.config import settings

# The session fixture is now in conftest.py

@pytest.fixture(autouse=True)
def mock_get_session(session):
    with patch('tomato_ai.handlers.get_session') as mock:
        mock.return_value = iter([session])
        yield mock

@pytest.fixture
def mock_telegram_notifier():
    with patch('tomato_ai.adapters.telegram.get_telegram_notifier') as mock_get_notifier:
        mock_notifier = AsyncMock()
        mock_get_notifier.return_value = mock_notifier
        yield mock_notifier

@pytest.mark.asyncio
class TestHandlersIntegration:
    async def test_start_session_command_new_user(self, session, mock_telegram_notifier):
        # Arrange
        chat_id = "12345"
        update = MagicMock()
        update.message.chat_id = chat_id
        update.message.from_user.id = chat_id
        context = MagicMock()

        # Act
        await start_session_command(update, context, "work")

        # Assert
        # Check that a new user was created
        user = session.query(orm.User).filter_by(telegram_chat_id=chat_id).one_or_none()
        assert user is not None
        assert user.telegram_chat_id == chat_id

        # Check that a new session was created
        pomodoro_session = session.query(orm.PomodoroSession).filter_by(user_id=user.id).one_or_none()
        assert pomodoro_session is not None
        assert pomodoro_session.session_type == "work"
        assert pomodoro_session.state == "active"

        # Check that a message was sent
        mock_telegram_notifier.send_message.assert_awaited_once()
        args, kwargs = mock_telegram_notifier.send_message.call_args
        assert kwargs["chat_id"] == chat_id
        assert "session started!" in kwargs["message"]

    async def test_start_session_command_existing_user(self, session, mock_telegram_notifier):
        # Arrange
        chat_id = "12345"
        user = orm.User(telegram_chat_id=chat_id)
        session.add(user)
        session.commit()

        update = MagicMock()
        update.message.chat_id = chat_id
        update.message.from_user.id = chat_id
        context = MagicMock()

        # Act
        await start_session_command(update, context, "short_break")

        # Assert
        # Check that no new user was created
        users = session.query(orm.User).filter_by(telegram_chat_id=chat_id).all()
        assert len(users) == 1

        # Check that a new session was created
        pomodoro_session = session.query(orm.PomodoroSession).filter_by(user_id=user.id).one_or_none()
        assert pomodoro_session is not None
        assert pomodoro_session.session_type == "short_break"
        assert pomodoro_session.state == "active"

        # Check that a message was sent
        mock_telegram_notifier.send_message.assert_awaited_once()

    async def test_handle_nudge_sends_message(self, session, mock_telegram_notifier):
        # Arrange
        chat_id = "12345"
        user = orm.User(telegram_chat_id=chat_id, timezone="UTC")
        session.add(user)
        session.commit()

        event = events.NudgeUser(user_id=user.id, chat_id=int(chat_id), escalation_count=1, session_type="work")

        with patch('tomato_ai.handlers.negotiation_agent') as mock_agent:
            mock_agent.structured_output.return_value = TelegramMessageAction(text="Test message")
            # Act
            await handle_nudge(event)

        # Assert
        mock_telegram_notifier.send_message.assert_awaited_once()
        args, kwargs = mock_telegram_notifier.send_message.call_args
        assert kwargs["chat_id"] == str(chat_id)
        assert kwargs["message"] == "Test message"

    async def test_handle_nudge_schedules_next_nudge(self, session, mock_telegram_notifier):
        # Arrange
        chat_id = "12345"
        user = orm.User(telegram_chat_id=chat_id, timezone="UTC")
        session.add(user)
        session.commit()

        event = events.NudgeUser(user_id=user.id, chat_id=int(chat_id), escalation_count=1, session_type="work")

        class DelayContainer:
            delay_in_minutes: int = 15

        with patch('tomato_ai.handlers.negotiation_agent') as mock_negotiation_agent, \
             patch('tomato_ai.handlers.get_scheduler_agent') as mock_get_scheduler_agent:
            mock_negotiation_agent.structured_output.return_value = PomodoroScheduleNextAction(time="later")
            mock_scheduler_agent = MagicMock()
            mock_scheduler_agent.structured_output.return_value = DelayContainer()
            mock_get_scheduler_agent.return_value = mock_scheduler_agent

            # Act
            await handle_nudge(event)

        # Assert
        # Check that a reminder was scheduled
        reminder = session.query(orm.Reminder).filter_by(user_id=user.id).one_or_none()
        assert reminder is not None
        assert reminder.escalation_count == 2

    async def test_handle_nudge_max_escalations(self, session, mock_telegram_notifier):
        # Arrange
        chat_id = "12345"
        user = orm.User(telegram_chat_id=chat_id, timezone="UTC")
        session.add(user)
        session.commit()

        event = events.NudgeUser(user_id=user.id, chat_id=int(chat_id), escalation_count=settings.MAX_ESCALATIONS, session_type="work")

        # Act
        await handle_nudge(event)

        # Assert
        mock_telegram_notifier.send_message.assert_awaited_once()
        args, kwargs = mock_telegram_notifier.send_message.call_args
        assert "tomorrow morning" in kwargs["message"]

        # Check that a reminder was scheduled for the next day
        reminder = session.query(orm.Reminder).filter_by(user_id=user.id).one_or_none()
        assert reminder is not None
        assert (reminder.send_at - datetime.utcnow()).total_seconds() > 0

    async def test_not_now_button(self, session, mock_telegram_notifier):
        # Arrange
        chat_id = "12345"
        update = AsyncMock()
        update.callback_query.message.chat_id = int(chat_id)
        context = MagicMock()

        # Act
        await not_now_button(update, context)

        # Assert
        # Check that a reminder was scheduled
        user = session.query(orm.User).filter_by(telegram_chat_id=chat_id).one_or_none()
        assert user is not None
        reminder = session.query(orm.Reminder).filter_by(user_id=user.id).one_or_none()
        assert reminder is not None
        assert reminder.escalation_count == 1
