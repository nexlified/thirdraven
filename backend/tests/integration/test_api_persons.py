"""
Integration tests for the persons API.
Mirrors: frontend/src/api/persons.ts
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/persons"


async def test_create_person(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.post(
        f"{BASE}/",
        json={"first_name": "Alice", "last_name": "Smith"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["first_name"] == "Alice"
    assert body["last_name"] == "Smith"
    assert "id" in body
    assert "owner_id" in body
    assert isinstance(body["tags"], list)


async def test_list_persons_pagination_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(f"{BASE}/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"items", "total", "skip", "limit"}
    assert isinstance(body["items"], list)
    assert isinstance(body["total"], int)


async def test_get_person(api_client: AsyncClient, auth_headers: dict) -> None:
    person_id = (
        await api_client.post(
            f"{BASE}/",
            json={"first_name": "Bob"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.get(f"{BASE}/{person_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == person_id


async def test_update_person(api_client: AsyncClient, auth_headers: dict) -> None:
    person_id = (
        await api_client.post(
            f"{BASE}/",
            json={"first_name": "Charlie"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.patch(
        f"{BASE}/{person_id}",
        json={"first_name": "Charles", "notes": "Updated note"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Charles"
    assert resp.json()["notes"] == "Updated note"


async def test_delete_person_returns_204(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    person_id = (
        await api_client.post(
            f"{BASE}/",
            json={"first_name": "DeleteMe"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.delete(f"{BASE}/{person_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert resp.content == b""


async def test_schema_endpoint(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.get(f"{BASE}/schema", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "prefixes" in body
    assert "genders" in body
    assert "channel_types" in body
    assert "address_types" in body
    assert isinstance(body["channel_types"], list)


async def test_list_persons_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{BASE}/")
    assert resp.status_code == 401
    assert "detail" in resp.json()


async def test_create_person_channel(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    person_id = (
        await api_client.post(
            f"{BASE}/",
            json={"first_name": "Channels"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.post(
        f"{BASE}/{person_id}/channels/",
        json={"type": "email", "value": "test@example.com", "is_primary": True},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "email"
    assert body["value"] == "test@example.com"
    assert "id" in body


async def test_list_person_channels_via_include(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    """Channels are listed via GET /persons/{id}?include=channels (no standalone list)."""
    person_id = (
        await api_client.post(
            f"{BASE}/",
            json={"first_name": "ListChannels"},
            headers=auth_headers,
        )
    ).json()["id"]
    await api_client.post(
        f"{BASE}/{person_id}/channels/",
        json={"type": "mobile", "value": "+911234567890"},
        headers=auth_headers,
    )

    resp = await api_client.get(
        f"{BASE}/{person_id}",
        params={"include": "channels"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "channels" in body
    assert isinstance(body["channels"], list)
    assert len(body["channels"]) >= 1


async def test_create_person_address(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    person_id = (
        await api_client.post(
            f"{BASE}/",
            json={"first_name": "Address"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.post(
        f"{BASE}/{person_id}/addresses/",
        json={"type": "home", "city": "Mumbai", "country": "IN"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["city"] == "Mumbai"
    assert "id" in body
