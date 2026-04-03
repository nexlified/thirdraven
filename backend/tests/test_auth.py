import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.auth import router as auth_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserPublic

OWNER_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)

FAKE_USER_PUBLIC = UserPublic(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    created_at=datetime.now(UTC),
    person_id=None,
)


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def authed_client():
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    async def override_get_current_user():
        return FAKE_USER

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


# ── POST /auth/register ────────────────────────────────────────────────────────


def test_register_success(client):
    with (
        patch("app.api.v1.auth.get_user_by_username", new=AsyncMock(return_value=None)),
        patch(
            "app.api.v1.auth.create_user", new=AsyncMock(return_value=FAKE_USER_PUBLIC)
        ),
    ):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "secret123",
                "first_name": "Test",
            },
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "testuser"
    assert body["email"] == "test@example.com"


def test_register_duplicate_username(client):
    with patch(
        "app.api.v1.auth.get_user_by_username",
        new=AsyncMock(return_value=FAKE_USER),
    ):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "secret123",
                "first_name": "Test",
            },
        )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_register_missing_required_fields(client):
    resp = client.post("/api/v1/auth/register", json={"username": "only"})
    assert resp.status_code == 422


# ── POST /auth/login ───────────────────────────────────────────────────────────


def test_login_success(client):
    with (
        patch(
            "app.api.v1.auth.get_user_by_username",
            new=AsyncMock(return_value=FAKE_USER),
        ),
        patch("app.api.v1.auth.verify_password", return_value=True),
        patch("app.api.v1.auth.create_access_token", return_value="fake-jwt-token"),
    ):
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "secret123"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"] == "fake-jwt-token"
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client):
    with (
        patch(
            "app.api.v1.auth.get_user_by_username",
            new=AsyncMock(return_value=FAKE_USER),
        ),
        patch("app.api.v1.auth.verify_password", return_value=False),
    ):
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "wrong"},
        )
    assert resp.status_code == 401


def test_login_unknown_user(client):
    with patch(
        "app.api.v1.auth.get_user_by_username", new=AsyncMock(return_value=None)
    ):
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "ghost", "password": "secret123"},
        )
    assert resp.status_code == 401


# ── GET /auth/me ───────────────────────────────────────────────────────────────


def test_get_me_success(authed_client):
    resp = authed_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


def test_get_me_unauthenticated(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 422, 500)


# ── GET /auth/me/preferences ───────────────────────────────────────────────────


def test_get_preferences(authed_client):
    fake_prefs = {
        "default_country": "US",
        "default_timezone": "UTC",
        "default_relationship_nature": "personal",
        "default_visibility": "private",
        "default_closeness_level": None,
        "default_languages": [],
    }
    with patch("app.api.v1.auth.get_user_preferences", return_value=fake_prefs):
        resp = authed_client.get("/api/v1/auth/me/preferences")
    assert resp.status_code == 200
    assert resp.json()["default_country"] == "US"


# ── PATCH /auth/me/preferences ─────────────────────────────────────────────────


def test_patch_preferences(authed_client):
    updated_prefs = {
        "default_country": "IN",
        "default_timezone": "Asia/Kolkata",
        "default_relationship_nature": "personal",
        "default_visibility": "private",
        "default_closeness_level": None,
        "default_languages": [],
    }
    with patch(
        "app.api.v1.auth.update_user_preferences",
        new=AsyncMock(return_value=updated_prefs),
    ):
        resp = authed_client.patch(
            "/api/v1/auth/me/preferences",
            json={"default_country": "IN", "default_timezone": "Asia/Kolkata"},
        )
    assert resp.status_code == 200
    assert resp.json()["default_country"] == "IN"


# ── POST /auth/forgot-password ─────────────────────────────────────────────────


def test_forgot_password_returns_token(client):
    with patch(
        "app.api.v1.auth.create_password_reset_token",
        new=AsyncMock(return_value="reset-token-abc"),
    ):
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "test@example.com"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["reset_token"] == "reset-token-abc"


def test_forgot_password_invalid_email(client):
    resp = client.post("/api/v1/auth/forgot-password", json={"email": "not-an-email"})
    assert resp.status_code == 422


# ── POST /auth/reset-password ──────────────────────────────────────────────────


def test_reset_password_success(client):
    with patch(
        "app.api.v1.auth.reset_password_with_token",
        new=AsyncMock(return_value=True),
    ):
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={"reset_token": "valid-token", "new_password": "newpassword123"},
        )
    assert resp.status_code == 200
    assert "updated" in resp.json()["message"].lower()


def test_reset_password_too_short(client):
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"reset_token": "valid-token", "new_password": "short"},
    )
    assert resp.status_code == 400
    assert "8 characters" in resp.json()["detail"]


def test_reset_password_invalid_token(client):
    with patch(
        "app.api.v1.auth.reset_password_with_token",
        new=AsyncMock(return_value=False),
    ):
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={"reset_token": "bad-token", "new_password": "newpassword123"},
        )
    assert resp.status_code == 400
    assert "Invalid" in resp.json()["detail"]
