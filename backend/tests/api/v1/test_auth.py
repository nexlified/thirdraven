import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

import app.api.v1.auth as auth_module


def test_register_success(
    client: TestClient,
    fake_db: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_user_mock = AsyncMock(return_value=None)
    created_user = SimpleNamespace(
        id=uuid.uuid4(),
        username="alice",
        email="alice@example.com",
        created_at=datetime.now(UTC),
        hashed_password="hashed",
        is_active=True,
    )
    create_user_mock = AsyncMock(return_value=created_user)

    monkeypatch.setattr(auth_module, "get_user_by_username", get_user_mock)
    monkeypatch.setattr(auth_module, "create_user", create_user_mock)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret123",
            "first_name": "Alice",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == str(created_user.id)
    assert payload["username"] == "alice"
    assert payload["email"] == "alice@example.com"
    assert "created_at" in payload
    assert "hashed_password" not in payload

    get_user_mock.assert_awaited_once_with(fake_db, "alice")
    create_user_mock.assert_awaited_once()


def test_register_duplicate_username_returns_400(
    client: TestClient,
    fake_db: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_user_mock = AsyncMock(return_value=SimpleNamespace(username="alice"))
    create_user_mock = AsyncMock()

    monkeypatch.setattr(auth_module, "get_user_by_username", get_user_mock)
    monkeypatch.setattr(auth_module, "create_user", create_user_mock)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret123",
            "first_name": "Alice",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}

    get_user_mock.assert_awaited_once_with(fake_db, "alice")
    create_user_mock.assert_not_called()


def test_register_invalid_email_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "email": "not-an-email",
            "password": "secret123",
            "first_name": "Alice",
        },
    )

    assert response.status_code == 422


def test_register_missing_required_field_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
        },
    )

    assert response.status_code == 422


def test_login_success(
    client: TestClient,
    fake_db: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = SimpleNamespace(username="alice", hashed_password="hashed-password")
    get_user_mock = AsyncMock(return_value=user)
    verify_password_mock = Mock(return_value=True)
    create_access_token_mock = Mock(return_value="signed.jwt.token")

    monkeypatch.setattr(auth_module, "get_user_by_username", get_user_mock)
    monkeypatch.setattr(auth_module, "verify_password", verify_password_mock)
    monkeypatch.setattr(auth_module, "create_access_token", create_access_token_mock)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "alice", "password": "secret123"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "signed.jwt.token",
        "token_type": "bearer",
    }

    get_user_mock.assert_awaited_once_with(fake_db, "alice")
    verify_password_mock.assert_called_once_with("secret123", "hashed-password")
    create_access_token_mock.assert_called_once_with(data={"sub": "alice"})


def test_login_unknown_username_returns_401(
    client: TestClient,
    fake_db: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_user_mock = AsyncMock(return_value=None)
    verify_password_mock = Mock()

    monkeypatch.setattr(auth_module, "get_user_by_username", get_user_mock)
    monkeypatch.setattr(auth_module, "verify_password", verify_password_mock)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "unknown", "password": "secret123"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}
    assert response.headers["www-authenticate"] == "Bearer"

    get_user_mock.assert_awaited_once_with(fake_db, "unknown")
    verify_password_mock.assert_not_called()


def test_login_wrong_password_returns_401(
    client: TestClient,
    fake_db: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = SimpleNamespace(username="alice", hashed_password="hashed-password")
    get_user_mock = AsyncMock(return_value=user)
    verify_password_mock = Mock(return_value=False)
    create_access_token_mock = Mock()

    monkeypatch.setattr(auth_module, "get_user_by_username", get_user_mock)
    monkeypatch.setattr(auth_module, "verify_password", verify_password_mock)
    monkeypatch.setattr(auth_module, "create_access_token", create_access_token_mock)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "alice", "password": "wrong-pass"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}
    assert response.headers["www-authenticate"] == "Bearer"

    get_user_mock.assert_awaited_once_with(fake_db, "alice")
    verify_password_mock.assert_called_once_with("wrong-pass", "hashed-password")
    create_access_token_mock.assert_not_called()


def test_login_missing_form_field_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "alice"},
    )

    assert response.status_code == 422
