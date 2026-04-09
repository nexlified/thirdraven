"""
Integration tests for the reminders API.
Mirrors: frontend/src/api/reminders.ts
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/reminders"
DUE_AT = "2027-01-15T10:00:00"


async def test_create_reminder(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.post(
        f"{BASE}/",
        json={"title": "Call dentist", "due_at": DUE_AT},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Call dentist"
    assert body["is_done"] is False
    assert "id" in body
    assert "owner_id" in body
    assert "due_at" in body


async def test_list_reminders_pagination_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(f"{BASE}/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"items", "total", "skip", "limit"}
    assert isinstance(body["items"], list)
    assert isinstance(body["total"], int)


async def test_get_reminder(api_client: AsyncClient, auth_headers: dict) -> None:
    reminder_id = (
        await api_client.post(
            f"{BASE}/",
            json={"title": "Fetch me", "due_at": DUE_AT},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.get(f"{BASE}/{reminder_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == reminder_id


async def test_update_reminder(api_client: AsyncClient, auth_headers: dict) -> None:
    reminder_id = (
        await api_client.post(
            f"{BASE}/",
            json={"title": "Old title", "due_at": DUE_AT},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.patch(
        f"{BASE}/{reminder_id}",
        json={"title": "Updated title", "is_done": True},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated title"
    assert resp.json()["is_done"] is True


async def test_delete_reminder_returns_204(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    reminder_id = (
        await api_client.post(
            f"{BASE}/",
            json={"title": "Delete me", "due_at": DUE_AT},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.delete(f"{BASE}/{reminder_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert resp.content == b""


async def test_list_reminders_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{BASE}/")
    assert resp.status_code == 401
    assert "detail" in resp.json()
