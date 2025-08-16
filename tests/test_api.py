from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch
from tomato_ai.domain import events


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_and_get_session(client: TestClient):
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


def test_events_are_published(client: TestClient):
    with patch("tomato_ai.adapters.event_bus.publish") as mock_publish:
        user_id = uuid4()
        response = client.post("/sessions/", json={"user_id": str(user_id)})
        assert response.status_code == 200
        data = response.json()
        session_id = data["session_id"]

        mock_publish.assert_called_once()
        assert isinstance(mock_publish.call_args[0][0], events.SessionStarted)

        mock_publish.reset_mock()

        # Pause the session
        response = client.put(f"/sessions/{session_id}/state", json={"state": "paused"})
        assert response.status_code == 200

        mock_publish.assert_called_once()
        assert isinstance(mock_publish.call_args[0][0], events.SessionPaused)