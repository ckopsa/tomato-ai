import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from tomato_ai.domain import events


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_create_and_get_session(client: TestClient):
    user_id = uuid4()
    response = client.post("/sessions/", json={"user_id": str(user_id)})
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(user_id)
    assert data["state"] == "active"

    session_id = data["session_id"]
    response = client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["user_id"] == str(user_id)


@pytest.mark.asyncio
async def test_events_are_published(client: TestClient):
    with patch("tomato_ai.adapters.event_bus.publish", new_callable=AsyncMock) as mock_publish:
        user_id = uuid4()
        response = client.post("/sessions/", json={"user_id": str(user_id)})
        assert response.status_code == 200
        data = response.json()
        session_id = data["session_id"]

        mock_publish.assert_awaited_once()
        assert isinstance(mock_publish.call_args[0][0], events.SessionStarted)

        mock_publish.reset_mock()

        # Pause the session
        response = client.put(f"/sessions/{session_id}/state", json={"state": "paused"})
        assert response.status_code == 200

        mock_publish.assert_awaited_once()
        assert isinstance(mock_publish.call_args[0][0], events.SessionPaused)

@pytest.mark.asyncio
async def test_telegram_webhook(client: TestClient):
    with patch("telegram.ext.Application.process_update", new_callable=AsyncMock) as mock_process_update:
        update_data = {
            "update_id": 10000,
            "message": {
                "message_id": 1365,
                "date": 1603279327,
                "chat": {"id": 1111, "type": "private", "first_name": "Test"},
                "from": {"id": 1111, "is_bot": False, "first_name": "Test"},
                "text": "/start",
            },
        }
        response = client.post("/telegram/webhook", json=update_data)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        mock_process_update.assert_awaited_once()