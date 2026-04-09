"""
Integration tests for the events API.
Mirrors: frontend/src/api/events.ts

Tests CRUD on events plus the event persons sub-resource.
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/events"


async def _create_person(api_client: AsyncClient, auth_headers: dict) -> str:
    resp = await api_client.post(
        "/api/v1/persons/",
        json={"first_name": "EventPerson"},
        headers=auth_headers,
    )
    return resp.json()["id"]


async def test_create_event(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.post(
        f"{BASE}/",
        json={"title": "Team dinner", "occurred_on": "2026-03-15", "location": "Café"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Team dinner"
    assert "id" in body
    assert "owner_id" in body
    assert isinstance(body["persons"], list)


async def test_list_events_pagination_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(f"{BASE}/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"items", "total", "skip", "limit"}
    assert isinstance(body["items"], list)


async def test_get_event(api_client: AsyncClient, auth_headers: dict) -> None:
    event_id = (
        await api_client.post(
            f"{BASE}/",
            json={"title": "Fetch me"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.get(f"{BASE}/{event_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == event_id


async def test_update_event(api_client: AsyncClient, auth_headers: dict) -> None:
    event_id = (
        await api_client.post(
            f"{BASE}/",
            json={"title": "Old title"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.patch(
        f"{BASE}/{event_id}",
        json={"title": "New title", "location": "Office"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New title"
    assert resp.json()["location"] == "Office"


async def test_delete_event_returns_204(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    event_id = (
        await api_client.post(
            f"{BASE}/",
            json={"title": "Delete me"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.delete(f"{BASE}/{event_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert resp.content == b""


async def test_add_person_to_event(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    event_id = (
        await api_client.post(
            f"{BASE}/",
            json={"title": "Event with Person"},
            headers=auth_headers,
        )
    ).json()["id"]
    person_id = await _create_person(api_client, auth_headers)

    resp = await api_client.post(
        f"{BASE}/{event_id}/persons/",
        json={"person_id": person_id, "role": "attendee"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["event_id"] == event_id
    assert body["role"] == "attendee"
    assert "person" in body


async def test_list_event_persons(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    event_id = (
        await api_client.post(
            f"{BASE}/",
            json={"title": "Event persons list"},
            headers=auth_headers,
        )
    ).json()["id"]
    person_id = await _create_person(api_client, auth_headers)
    await api_client.post(
        f"{BASE}/{event_id}/persons/",
        json={"person_id": person_id},
        headers=auth_headers,
    )

    resp = await api_client.get(f"{BASE}/{event_id}/persons/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1


async def test_remove_person_from_event(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    event_id = (
        await api_client.post(
            f"{BASE}/",
            json={"title": "Remove person event"},
            headers=auth_headers,
        )
    ).json()["id"]
    person_id = await _create_person(api_client, auth_headers)
    # event_person_id is the junction table record id (not person_id)
    event_person_id = (
        await api_client.post(
            f"{BASE}/{event_id}/persons/",
            json={"person_id": person_id},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.delete(
        f"{BASE}/{event_id}/persons/{event_person_id}", headers=auth_headers
    )
    assert resp.status_code == 204
    assert resp.content == b""


async def test_list_events_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{BASE}/")
    assert resp.status_code == 401
    assert "detail" in resp.json()
