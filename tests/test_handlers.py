import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from tomato_ai.domain import events
from tomato_ai.handlers import schedule_nudge_on_session_completed, handle_nudge, start_button, not_now_button
from tomato_ai.adapters import orm
from tomato_ai.domain.agent_actions import TelegramMessageAction, PomodoroScheduleNextAction
from tomato_ai.config import settings

@pytest.fixture
def mock_db_session():
    return MagicMock()

class TestNudgeHandlers:
    def test_schedule_nudge_on_session_completed(self, mock_db_session):
        # Arrange
        user_id = uuid4()
        session_id = uuid4()
        chat_id = 12345
        session = orm.PomodoroSession(session_id=session_id, user_id=user_id, chat_id=chat_id)
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = session

        with patch('tomato_ai.handlers.get_session') as mock_get_session:
            mock_get_session.return_value = iter([mock_db_session])

            # Act
            event = events.SessionCompleted(user_id=user_id, session_id=session_id, session_type="work")
            schedule_nudge_on_session_completed(event)

            # Assert
            mock_db_session.add.assert_called_once()
            added_reminder = mock_db_session.add.call_args[0][0]
            assert isinstance(added_reminder, orm.Reminder)
            assert added_reminder.user_id == user_id
            assert added_reminder.escalation_count == 1

    @pytest.mark.asyncio
    async def test_handle_nudge_sends_message(self, mock_db_session):
        # Arrange
        user_id = uuid4()
        chat_id = 12345
        event = events.NudgeUser(user_id=user_id, chat_id=chat_id, escalation_count=1, session_type="work")

        mock_db_session.query.return_value.filter.return_value.count.return_value = 1
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = orm.PomodoroSession(end_time=datetime.now(timezone.utc))

        with patch('tomato_ai.handlers.get_session') as mock_get_session, \
             patch('tomato_ai.handlers.negotiation_agent') as mock_agent, \
             patch('tomato_ai.adapters.telegram.get_telegram_notifier') as mock_get_notifier:

            mock_get_session.return_value = iter([mock_db_session])
            mock_agent.structured_output.return_value = TelegramMessageAction(text="Test message")
            mock_notifier = AsyncMock()
            mock_get_notifier.return_value = mock_notifier

            # Act
            await handle_nudge(event)

            # Assert
            mock_agent.structured_output.assert_called_once()
            mock_notifier.send_message.assert_awaited_once_with(
                chat_id=str(chat_id), message="Test message", reply_markup=None
            )

    @pytest.mark.asyncio
    async def test_handle_nudge_schedules_next_nudge(self, mock_db_session):
        # Arrange
        user_id = uuid4()
        chat_id = 12345
        event = events.NudgeUser(user_id=user_id, chat_id=chat_id, escalation_count=1, session_type="work")

        mock_db_session.query.return_value.filter.return_value.count.return_value = 1
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = orm.PomodoroSession(end_time=datetime.now(timezone.utc))

        with patch('tomato_ai.handlers.get_session') as mock_get_session, \
             patch('tomato_ai.handlers.negotiation_agent') as mock_agent, \
             patch('tomato_ai.adapters.telegram.get_telegram_notifier'):

            mock_get_session.return_value = iter([mock_db_session])
            mock_agent.structured_output.return_value = PomodoroScheduleNextAction(time="15m")

            # Act
            await handle_nudge(event)

            # Assert
            mock_db_session.add.assert_called_once()
            added_reminder = mock_db_session.add.call_args[0][0]
            assert isinstance(added_reminder, orm.Reminder)
            assert added_reminder.user_id == user_id
            assert added_reminder.escalation_count == 2

    @pytest.mark.asyncio
    async def test_handle_nudge_max_escalations(self, mock_db_session):
        # Arrange
        user_id = uuid4()
        chat_id = 12345
        event = events.NudgeUser(user_id=user_id, chat_id=chat_id, escalation_count=settings.MAX_ESCALATIONS, session_type="work")

        with patch('tomato_ai.handlers.get_session') as mock_get_session, \
             patch('tomato_ai.adapters.telegram.get_telegram_notifier') as mock_get_notifier:

            mock_get_session.return_value = iter([mock_db_session])
            mock_notifier = AsyncMock()
            mock_get_notifier.return_value = mock_notifier

            # Act
            await handle_nudge(event)

            # Assert
            mock_notifier.send_message.assert_awaited_once()
            mock_db_session.add.assert_called_once()  # For scheduling for the next day
            added_reminder = mock_db_session.add.call_args[0][0]
            assert added_reminder.escalation_count == 0

    @pytest.mark.asyncio
    async def test_start_button(self):
        with patch('tomato_ai.handlers.start_session_command', new_callable=AsyncMock) as mock_start_session:
            update = MagicMock()
            context = MagicMock()
            await start_button(update, context)
            mock_start_session.assert_awaited_once_with(update, context, "work")

    @pytest.mark.asyncio
    async def test_not_now_button(self, mock_db_session):
        with patch('tomato_ai.handlers.get_session') as mock_get_session:
            mock_get_session.return_value = iter([mock_db_session])
            update = AsyncMock()
            update.callback_query.from_user.id = 12345
            update.callback_query.message.chat_id = 12345
            context = MagicMock()
            await not_now_button(update, context)
            mock_db_session.add.assert_called_once()
            added_reminder = mock_db_session.add.call_args[0][0]
            assert isinstance(added_reminder, orm.Reminder)
            assert added_reminder.escalation_count == 1
