import pytest
from fastapi.testclient import TestClient
import uuid


def test_register_user(client: TestClient):
    """Test user registration"""
    email = f"test-{uuid.uuid4()}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "id" in data


def test_register_duplicate_email(client: TestClient):
    """Test registration with duplicate email"""
    email = f"test-{uuid.uuid4()}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "pass456"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "email already exists"


def test_login_success(client: TestClient):
    """Test successful login"""
    email = f"test-{uuid.uuid4()}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "pass123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "pass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_email(client: TestClient):
    """Test login with non-existent email"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": f"nonexistent-{uuid.uuid4()}@test.com", "password": "pass123"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid email or password"


def test_login_wrong_password(client: TestClient):
    """Test login with wrong password"""
    email = f"test-{uuid.uuid4()}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correctpass"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrongpass"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid email or password"


def test_get_current_user_success(client: TestClient):
    """Test getting current user info"""
    email = f"test-{uuid.uuid4()}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "pass123"},
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "pass123"},
    )
    token = login_resp.json()["access_token"]
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == email


def test_get_current_user_no_token(client: TestClient):
    """Test accessing protected endpoint without token"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token(client: TestClient):
    """Test accessing protected endpoint with invalid token"""
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
