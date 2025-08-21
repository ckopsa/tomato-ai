import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from tomato_ai.domain.services import ReminderService, ReminderNotifier
from tomato_ai.adapters import orm

@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)

class TestReminderService:
    def test_schedule_reminder(self, mock_db_session):
        # Arrange
        service = ReminderService(db_session=mock_db_session)
        user_id = uuid4()
        chat_id = 12345
        send_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        # Act
        service.schedule_reminder(user_id, chat_id, send_at)

        # Assert
        mock_db_session.add.assert_called_once()
        added_reminder = mock_db_session.add.call_args[0][0]
        assert isinstance(added_reminder, orm.Reminder)
        assert added_reminder.user_id == user_id
        assert added_reminder.chat_id == chat_id
        assert added_reminder.send_at == send_at
        mock_db_session.commit.assert_called_once()

    def test_cancel_reminder(self, mock_db_session):
        # Arrange
        service = ReminderService(db_session=mock_db_session)
        user_id = uuid4()
        reminder = orm.Reminder(id=uuid4(), user_id=user_id, state='pending')
        mock_db_session.query.return_value.filter_by.return_value.all.return_value = [reminder]

        # Act
        service.cancel_reminder(user_id)

        # Assert
        assert reminder.state == 'cancelled'
        mock_db_session.add.assert_called_once_with(reminder)
        mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
class TestReminderNotifier:
    @patch('tomato_ai.domain.services.event_bus.publish')
    async def test_check_and_send_reminders_publishes_nudge_event(self, mock_publish, mock_db_session):
        # Arrange
        notifier = ReminderNotifier(db_session=mock_db_session)
        user_id = uuid4()
        reminder = orm.Reminder(
            id=uuid4(),
            user_id=user_id,
            chat_id=12345,
            state='pending',
            send_at=datetime.now(timezone.utc) - timedelta(minutes=5)
        )
        mock_db_session.query.return_value.filter.return_value.all.return_value = [reminder]
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None  # No active session

        # Act
        await notifier.check_and_send_reminders()

        # Assert
        mock_publish.assert_awaited_once()
        assert reminder.state == 'triggered'
        mock_db_session.add.assert_called_once_with(reminder)
        mock_db_session.commit.assert_called_once()

    @patch('tomato_ai.domain.services.event_bus.publish')
    async def test_check_and_send_reminders_does_not_publish_if_active_session(
        self, mock_publish, mock_db_session
    ):
        # Arrange
        notifier = ReminderNotifier(db_session=mock_db_session)
        user_id = uuid4()
        reminder = orm.Reminder(
            id=uuid4(),
            user_id=user_id,
            chat_id=12345,
            state='pending',
            send_at=datetime.now(timezone.utc) - timedelta(minutes=5)
        )
        mock_db_session.query.return_value.filter.return_value.all.return_value = [reminder]
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = orm.PomodoroSession() # Active session

        # Act
        await notifier.check_and_send_reminders()

        # Assert
        mock_publish.assert_not_awaited()
        assert reminder.state == 'triggered'
        mock_db_session.add.assert_called_once_with(reminder)
        mock_db_session.commit.assert_called_once()
