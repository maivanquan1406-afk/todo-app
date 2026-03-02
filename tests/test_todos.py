import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from zoneinfo import ZoneInfo

from app.core.config import settings


@pytest.fixture
def user_a_token(client: TestClient) -> str:
    """Create user A and get auth token"""
    email = f"alice-{uuid.uuid4()}@test.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "pass123"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "pass123"},
    )
    return resp.json()["access_token"]


@pytest.fixture
def user_b_token(client: TestClient) -> str:
    """Create user B and get auth token"""
    email = f"bob-{uuid.uuid4()}@test.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "pass456"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "pass456"},
    )
    return resp.json()["access_token"]


def test_create_todo(client: TestClient, user_a_token: str):
    """Test creating a todo"""
    response = client.post(
        "/api/v1/todos/",
        json={"title": "Test Task", "description": "Test description"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test description"
    assert data["is_done"] is False
    assert "id" in data


def test_create_todo_invalid_title(client: TestClient, user_a_token: str):
    """Test creating todo with invalid title length"""
    response = client.post(
        "/api/v1/todos/",
        json={"title": "AB"},  # Too short
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 422


def test_list_todos(client: TestClient, user_a_token: str):
    """Test listing todos"""
    client.post(
        "/api/v1/todos/",
        json={"title": "Task 1"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    client.post(
        "/api/v1/todos/",
        json={"title": "Task 2"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    response = client.get(
        "/api/v1/todos/", headers={"Authorization": f"Bearer {user_a_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_get_todo(client: TestClient, user_a_token: str):
    """Test getting single todo"""
    create_resp = client.post(
        "/api/v1/todos/",
        json={"title": "Single Task"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    todo_id = create_resp.json()["id"]
    response = client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Single Task"


def test_update_todo_patch(client: TestClient, user_a_token: str):
    """Test updating todo with PATCH"""
    create_resp = client.post(
        "/api/v1/todos/",
        json={"title": "Original Task"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    todo_id = create_resp.json()["id"]
    response = client.patch(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Task", "is_done": True},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Task"
    assert data["is_done"] is True


def test_delete_todo(client: TestClient, user_a_token: str):
    """Test deleting todo"""
    create_resp = client.post(
        "/api/v1/todos/",
        json={"title": "Task to delete"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    todo_id = create_resp.json()["id"]
    response = client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 204
    # Verify it's deleted
    get_resp = client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert get_resp.status_code == 404


def test_cross_user_isolation(
    client: TestClient, user_a_token: str, user_b_token: str
):
    """Test that users cannot access each other's todos"""
    # User A creates a todo
    create_resp = client.post(
        "/api/v1/todos/",
        json={"title": "Alice's Task"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    todo_id = create_resp.json()["id"]
    
    # User B tries to access it
    response = client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert response.status_code == 404


def test_list_todos_isolation(
    client: TestClient, user_a_token: str, user_b_token: str
):
    """Test that list only shows current user's todos"""
    # User A creates 2 todos
    client.post(
        "/api/v1/todos/",
        json={"title": "A Task 1"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    client.post(
        "/api/v1/todos/",
        json={"title": "A Task 2"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    # User B creates 1 todo
    client.post(
        "/api/v1/todos/",
        json={"title": "B Task 1"},
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    # Check A's list - should have 2
    resp_a = client.get(
        "/api/v1/todos/", headers={"Authorization": f"Bearer {user_a_token}"}
    )
    assert resp_a.json()["total"] == 2
    # Check B's list - should have 1
    resp_b = client.get(
        "/api/v1/todos/", headers={"Authorization": f"Bearer {user_b_token}"}
    )
    assert resp_b.json()["total"] == 1


def test_todo_with_due_date(client: TestClient, user_a_token: str):
    """Test creating todo with due_date"""
    due_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    response = client.post(
        "/api/v1/todos/",
        json={
            "title": "Task with deadline",
            "due_date": due_date,
            "tags": "important",
        },
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["due_date"] is not None
    assert data["tags"] == "important"


def test_reminder_scheduler_honors_local_timezone(monkeypatch, client: TestClient, user_a_token: str):
    """Ensure reminders trigger when due times are provided without timezone info"""
    from app.services import reminder_service

    due_local = datetime.now(ZoneInfo(settings.APP_TIMEZONE)).replace(second=0, microsecond=0) + timedelta(minutes=9)
    due_str = due_local.strftime("%Y-%m-%dT%H:%M:%S")

    response = client.post(
        "/api/v1/todos/",
        json={
            "title": "Timezone task",
            "due_date": due_str,
            "tags": json.dumps({"reminder_minutes": 10}),
        },
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 200

    sent_messages: list[dict] = []

    def fake_send_email(**kwargs):  # type: ignore[no-untyped-def]
        sent_messages.append(kwargs)

    monkeypatch.setattr(reminder_service, "send_email", fake_send_email)

    reminder_service.reminder_scheduler._process_once()

    assert len(sent_messages) == 1
    assert "nhắc nhở" in sent_messages[0]["subject"].lower()


def test_reminder_scheduler_does_not_require_smtp_from(monkeypatch):
    from app.services.reminder_service import ReminderScheduler
    from app.core import config

    monkeypatch.setattr(config.settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(config.settings, "SMTP_USERNAME", "user@test")
    monkeypatch.setattr(config.settings, "SMTP_PASSWORD", "secret")
    monkeypatch.setattr(config.settings, "SMTP_FROM", None)

    scheduler = ReminderScheduler()
    assert scheduler._smtp_ready() is True


def test_overdue_endpoint(client: TestClient, user_a_token: str):
    """Test overdue todos endpoint"""
    past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    client.post(
        "/api/v1/todos/",
        json={"title": "Overdue Task", "due_date": past_date},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    response = client.get(
        "/api/v1/todos/overdue",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_today_endpoint(client: TestClient, user_a_token: str):
    """Test today's todos endpoint"""
    today_date = datetime.now(timezone.utc).isoformat()
    client.post(
        "/api/v1/todos/",
        json={"title": "Today Task", "due_date": today_date},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    response = client.get(
        "/api/v1/todos/today",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_create_todo(client: TestClient, user_a_token: str):
    """Test creating a todo"""
    response = client.post(
        "/api/v1/todos/",
        json={"title": "Test Task", "description": "Test description"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test description"
    assert data["is_done"] is False
    assert "id" in data


def test_create_todo_invalid_title(client: TestClient, user_a_token: str):
    """Test creating todo with invalid title length"""
    response = client.post(
        "/api/v1/todos/",
        json={"title": "AB"},  # Too short
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 422


def test_list_todos(client: TestClient, user_a_token: str):
    """Test listing todos"""
    client.post(
        "/api/v1/todos/",
        json={"title": "Task 1"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    client.post(
        "/api/v1/todos/",
        json={"title": "Task 2"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    response = client.get(
        "/api/v1/todos/", headers={"Authorization": f"Bearer {user_a_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_get_todo(client: TestClient, user_a_token: str):
    """Test getting single todo"""
    create_resp = client.post(
        "/api/v1/todos/",
        json={"title": "Single Task"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    todo_id = create_resp.json()["id"]
    response = client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Single Task"


def test_update_todo_patch(client: TestClient, user_a_token: str):
    """Test updating todo with PATCH"""
    create_resp = client.post(
        "/api/v1/todos/",
        json={"title": "Original Task"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    todo_id = create_resp.json()["id"]
    response = client.patch(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Task", "is_done": True},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Task"
    assert data["is_done"] is True


def test_delete_todo(client: TestClient, user_a_token: str):
    """Test deleting todo"""
    create_resp = client.post(
        "/api/v1/todos/",
        json={"title": "Task to delete"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    todo_id = create_resp.json()["id"]
    response = client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 204
    # Verify it's deleted
    get_resp = client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert get_resp.status_code == 404


def test_cross_user_isolation(
    client: TestClient, user_a_token: str, user_b_token: str
):
    """Test that users cannot access each other's todos"""
    # User A creates a todo
    create_resp = client.post(
        "/api/v1/todos/",
        json={"title": "Alice's Task"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    todo_id = create_resp.json()["id"]
    
    # User B tries to access it
    response = client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert response.status_code == 404


def test_list_todos_isolation(
    client: TestClient, user_a_token: str, user_b_token: str
):
    """Test that list only shows current user's todos"""
    # User A creates 2 todos
    client.post(
        "/api/v1/todos/",
        json={"title": "A Task 1"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    client.post(
        "/api/v1/todos/",
        json={"title": "A Task 2"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    # User B creates 1 todo
    client.post(
        "/api/v1/todos/",
        json={"title": "B Task 1"},
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    # Check A's list - should have 2
    resp_a = client.get(
        "/api/v1/todos/", headers={"Authorization": f"Bearer {user_a_token}"}
    )
    assert resp_a.json()["total"] == 2
    # Check B's list - should have 1
    resp_b = client.get(
        "/api/v1/todos/", headers={"Authorization": f"Bearer {user_b_token}"}
    )
    assert resp_b.json()["total"] == 1


def test_todo_with_due_date(client: TestClient, user_a_token: str):
    """Test creating todo with due_date"""
    due_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    response = client.post(
        "/api/v1/todos/",
        json={
            "title": "Task with deadline",
            "due_date": due_date,
            "tags": "important",
        },
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["due_date"] is not None
    assert data["tags"] == "important"


def test_overdue_endpoint(client: TestClient, user_a_token: str):
    """Test overdue todos endpoint"""
    past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    client.post(
        "/api/v1/todos/",
        json={"title": "Overdue Task", "due_date": past_date},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    response = client.get(
        "/api/v1/todos/overdue",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_today_endpoint(client: TestClient, user_a_token: str):
    """Test today's todos endpoint"""
    today_date = datetime.now(timezone.utc).isoformat()
    client.post(
        "/api/v1/todos/",
        json={"title": "Today Task", "due_date": today_date},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    response = client.get(
        "/api/v1/todos/today",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
