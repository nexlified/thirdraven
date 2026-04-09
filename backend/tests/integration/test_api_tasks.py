"""
Integration tests for the tasks API.
Mirrors: frontend/src/api/tasks.ts
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/tasks"


async def test_create_task(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.post(
        f"{BASE}/",
        json={"title": "Buy oat milk", "status": "todo", "priority": "normal"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Buy oat milk"
    assert body["status"] == "todo"
    assert body["priority"] == "normal"
    assert "id" in body
    assert "owner_id" in body
    assert isinstance(body["tags"], list)


async def test_list_tasks_pagination_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(f"{BASE}/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"items", "total", "skip", "limit"}
    assert isinstance(body["items"], list)
    assert isinstance(body["total"], int)
    assert isinstance(body["skip"], int)
    assert isinstance(body["limit"], int)


async def test_get_task(api_client: AsyncClient, auth_headers: dict) -> None:
    task_id = (
        await api_client.post(
            f"{BASE}/",
            json={"title": "Fetch me"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.get(f"{BASE}/{task_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id


async def test_update_task(api_client: AsyncClient, auth_headers: dict) -> None:
    task_id = (
        await api_client.post(
            f"{BASE}/",
            json={"title": "Old title"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.patch(
        f"{BASE}/{task_id}",
        json={"title": "New title", "status": "done"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New title"
    assert resp.json()["status"] == "done"


async def test_delete_task_returns_204(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    task_id = (
        await api_client.post(
            f"{BASE}/",
            json={"title": "To be deleted"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.delete(f"{BASE}/{task_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert resp.content == b""


async def test_task_summary_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(f"{BASE}/summary", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "total" in body
    assert "by_status" in body
    assert "overdue" in body
    assert "due_today" in body


async def test_list_tasks_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{BASE}/")
    assert resp.status_code == 401
    assert "detail" in resp.json()


async def test_create_task_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.post(f"{BASE}/", json={"title": "Sneaky"})
    assert resp.status_code == 401
