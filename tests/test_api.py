from uuid import uuid4
from fastapi.testclient import TestClient


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


def test_update_session_state(client: TestClient):
    user_id = uuid4()
    response = client.post("/sessions/", json={"user_id": str(user_id)})
    assert response.status_code == 200
    data = response.json()
    session_id = data["session_id"]

    # Pause the session
    response = client.put(f"/sessions/{session_id}/state", json={"state": "paused"})
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "paused"

    # Resume the session
    response = client.put(f"/sessions/{session_id}/state", json={"state": "resumed"})
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "active"

    # Complete the session
    response = client.put(f"/sessions/{session_id}/state", json={"state": "completed"})
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "completed"