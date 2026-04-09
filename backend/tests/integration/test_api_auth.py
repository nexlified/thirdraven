"""
Integration tests for the auth API.
Mirrors: frontend/src/api/auth.ts
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/auth"


async def test_register(api_client: AsyncClient) -> None:
    resp = await api_client.post(
        f"{BASE}/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "first_name": "New",
            "last_name": "User",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "newuser"
    assert body["email"] == "newuser@example.com"
    assert "id" in body
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_duplicate_username(api_client: AsyncClient) -> None:
    payload = {
        "username": "dupuser",
        "email": "dup@example.com",
        "password": "SecurePass123!",
        "first_name": "Dup",
    }
    await api_client.post(f"{BASE}/register", json=payload)
    resp = await api_client.post(f"{BASE}/register", json=payload)
    assert resp.status_code == 400
    assert "detail" in resp.json()


async def test_login(api_client: AsyncClient) -> None:
    # Register first
    await api_client.post(
        f"{BASE}/register",
        json={
            "username": "loginuser",
            "email": "loginuser@example.com",
            "password": "LoginPass123!",
            "first_name": "Login",
        },
    )
    # Login with form-encoded data (OAuth2PasswordRequestForm)
    resp = await api_client.post(
        f"{BASE}/login",
        data={"username": "loginuser", "password": "LoginPass123!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


async def test_login_wrong_password(api_client: AsyncClient) -> None:
    await api_client.post(
        f"{BASE}/register",
        json={
            "username": "wrongpass_user",
            "email": "wrongpass@example.com",
            "password": "CorrectPass123!",
            "first_name": "Wrong",
        },
    )
    resp = await api_client.post(
        f"{BASE}/login",
        data={"username": "wrongpass_user", "password": "WrongPassword"},
    )
    assert resp.status_code == 401
    assert "detail" in resp.json()


async def test_get_me(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.get(f"{BASE}/me", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "integration_user"
    assert "id" in body
    assert "email" in body


async def test_get_me_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{BASE}/me")
    assert resp.status_code == 401
    assert "detail" in resp.json()


async def test_get_preferences(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.get(f"{BASE}/me/preferences", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    # All 6 keys from UserPreferencesPublic must be present
    assert "default_country" in body
    assert "default_timezone" in body
    assert "default_relationship_nature" in body
    assert "default_visibility" in body
    assert "default_closeness_level" in body
    assert "default_languages" in body


async def test_patch_preferences(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.patch(
        f"{BASE}/me/preferences",
        json={"default_country": "IN"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["default_country"] == "IN"


async def test_forgot_password(api_client: AsyncClient) -> None:
    await api_client.post(
        f"{BASE}/register",
        json={
            "username": "resetuser",
            "email": "resetuser@example.com",
            "password": "OldPass123!",
            "first_name": "Reset",
        },
    )
    resp = await api_client.post(
        f"{BASE}/forgot-password",
        json={"email": "resetuser@example.com"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "message" in body
    # reset_token is returned in dev mode
    assert "reset_token" in body


async def test_reset_password(api_client: AsyncClient) -> None:
    await api_client.post(
        f"{BASE}/register",
        json={
            "username": "resetflow",
            "email": "resetflow@example.com",
            "password": "OldPass123!",
            "first_name": "ResetFlow",
        },
    )
    # Get reset token
    fp_resp = await api_client.post(
        f"{BASE}/forgot-password",
        json={"email": "resetflow@example.com"},
    )
    reset_token = fp_resp.json()["reset_token"]
    assert reset_token is not None

    # Reset password
    resp = await api_client.post(
        f"{BASE}/reset-password",
        json={"reset_token": reset_token, "new_password": "NewPass123!"},
    )
    assert resp.status_code == 200
    assert "message" in resp.json()

    # Login with new password
    login_resp = await api_client.post(
        f"{BASE}/login",
        data={"username": "resetflow", "password": "NewPass123!"},
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()
