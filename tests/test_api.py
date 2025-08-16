import time
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch
from tomato_ai.domain import events
from tomato_ai.worker import complete_expired_sessions


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
    assert "expires_at" in data

    session_id = data["session_id"]
    response = client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["user_id"] == str(user_id)


def test_pause_and_resume_session(client: TestClient):
    user_id = uuid4()
    response = client.post("/sessions/", json={"user_id": str(user_id)})
    assert response.status_code == 200
    data = response.json()
    session_id = data["session_id"]
    expires_at = datetime.fromisoformat(data["expires_at"])

    # Pause the session
    response = client.put(f"/sessions/{session_id}/state", json={"state": "paused"})
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "paused"
    assert data["expires_at"] is None
    assert "remaining_duration_on_pause" in data

    # Resume the session
    response = client.put(f"/sessions/{session_id}/state", json={"state": "resumed"})
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "active"
    assert "expires_at" in data
    new_expires_at = datetime.fromisoformat(data["expires_at"])
    assert new_expires_at > expires_at


def test_worker_completes_expired_sessions(client: TestClient):
    user_id = uuid4()
    response = client.post(
        "/sessions/",
        json={"user_id": str(user_id), "duration": 1},
    )
    assert response.status_code == 200
    data = response.json()
    session_id = data["session_id"]

    time.sleep(2)

    with patch("tomato_ai.adapters.event_bus.publish") as mock_publish:
        complete_expired_sessions()
        mock_publish.assert_called_once()
        assert isinstance(mock_publish.call_args[0][0], events.SessionCompleted)

    response = client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "completed"