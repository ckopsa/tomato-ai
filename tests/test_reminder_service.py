import pytest
from unittest.mock import MagicMock, AsyncMock, patch, ANY
from uuid import uuid4
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tomato_ai.domain.services import ReminderService
from tomato_ai.adapters import orm

@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)

@pytest.fixture
def mock_scheduler():
    return MagicMock(spec=AsyncIOScheduler)

@pytest.mark.asyncio
class TestReminderService:
    async def test_schedule_reminder(self, mock_db_session, mock_scheduler):
        # Arrange
        service = ReminderService(db_session=mock_db_session, scheduler=mock_scheduler)
        user_id = uuid4()
        chat_id = 12345
        mock_scheduler.add_job.return_value = MagicMock(id='test_job_id')

        # Act
        await service.schedule_reminder(user_id, chat_id)

        # Assert
        mock_scheduler.add_job.assert_called_once_with(
            service.check_in, "date", run_date=ANY, args=[str(user_id), ANY]
        )
        mock_db_session.add.assert_called_once()
        added_reminder = mock_db_session.add.call_args[0][0]
        assert isinstance(added_reminder, orm.Reminder)
        assert added_reminder.user_id == user_id
        assert added_reminder.chat_id == chat_id
        mock_db_session.commit.assert_called_once()

    async def test_cancel_reminder(self, mock_db_session, mock_scheduler):
        # Arrange
        service = ReminderService(db_session=mock_db_session, scheduler=mock_scheduler)
        user_id = uuid4()
        reminder = orm.Reminder(id=uuid4(), user_id=user_id, job_id='test_job_id', state='pending')
        mock_db_session.query.return_value.filter_by.return_value.all.return_value = [reminder]

        # Act
        await service.cancel_reminder(user_id)

        # Assert
        mock_scheduler.remove_job.assert_called_once_with('test_job_id')
        assert reminder.state == 'cancelled'
        mock_db_session.add.assert_called_once_with(reminder)
        mock_db_session.commit.assert_called_once()

    @patch('tomato_ai.adapters.telegram.get_telegram_notifier')
    async def test_check_in_sends_notification_when_no_active_session(
        self, mock_get_notifier, mock_db_session, mock_scheduler
    ):
        # Arrange
        service = ReminderService(db_session=mock_db_session, scheduler=mock_scheduler)
        user_id = uuid4()
        reminder_id = uuid4()

        reminder = orm.Reminder(id=reminder_id, user_id=user_id, chat_id=12345, job_id='test_job_id', state='pending')

        # First query for active session, second for reminder
        mock_db_session.query.return_value.filter_by.return_value.first.side_effect = [
            None,  # No active session
            reminder,
        ]

        mock_notifier = AsyncMock()
        mock_get_notifier.return_value = mock_notifier

        # Act
        await service.check_in(str(user_id), reminder_id)

        # Assert
        mock_notifier.send_message.assert_awaited_once()
        assert reminder.state == 'triggered'
        mock_db_session.add.assert_called_once_with(reminder)
        mock_db_session.commit.assert_called_once()

    @patch('tomato_ai.adapters.telegram.get_telegram_notifier')
    async def test_check_in_does_not_send_notification_when_active_session_exists(
        self, mock_get_notifier, mock_db_session, mock_scheduler
    ):
        # Arrange
        service = ReminderService(db_session=mock_db_session, scheduler=mock_scheduler)
        user_id = uuid4()
        reminder_id = uuid4()

        reminder = orm.Reminder(id=reminder_id, user_id=user_id, chat_id=12345, job_id='test_job_id', state='pending')

        # First query for active session, second for reminder
        mock_db_session.query.return_value.filter_by.return_value.first.side_effect = [
            orm.PomodoroSession(), # Active session found
            reminder,
        ]

        mock_notifier = AsyncMock()
        mock_get_notifier.return_value = mock_notifier

        # Act
        await service.check_in(str(user_id), reminder_id)

        # Assert
        mock_notifier.send_message.assert_not_awaited()
        # Check that the reminder state is still updated
        assert reminder.state == 'triggered'
        mock_db_session.add.assert_called_once_with(reminder)
        mock_db_session.commit.assert_called_once()
