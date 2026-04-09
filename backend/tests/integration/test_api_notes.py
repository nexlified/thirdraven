"""
Integration tests for the notes API.
Mirrors: frontend/src/api/notes.ts
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/notes"


async def test_create_note(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.post(
        f"{BASE}/",
        json={"title": "My first note", "body": "Hello world", "pinned": False},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "My first note"
    assert body["body"] == "Hello world"
    assert body["pinned"] is False
    assert "id" in body
    assert "owner_id" in body
    assert isinstance(body["tags"], list)


async def test_list_notes_pagination_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(f"{BASE}/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"items", "total", "skip", "limit"}
    assert isinstance(body["items"], list)
    assert isinstance(body["total"], int)


async def test_get_note(api_client: AsyncClient, auth_headers: dict) -> None:
    note_id = (
        await api_client.post(
            f"{BASE}/",
            json={"title": "Fetch me"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.get(f"{BASE}/{note_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == note_id


async def test_update_note(api_client: AsyncClient, auth_headers: dict) -> None:
    note_id = (
        await api_client.post(
            f"{BASE}/",
            json={"title": "Old title"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.patch(
        f"{BASE}/{note_id}",
        json={"title": "New title", "pinned": True},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New title"
    assert resp.json()["pinned"] is True


async def test_delete_note_returns_204(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    note_id = (
        await api_client.post(
            f"{BASE}/",
            json={"title": "To be deleted"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.delete(f"{BASE}/{note_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert resp.content == b""


async def test_note_statistics_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(f"{BASE}/statistics", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "total" in body
    assert "pinned" in body
    assert "by_attachment" in body


async def test_list_notes_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{BASE}/")
    assert resp.status_code == 401
    assert "detail" in resp.json()
