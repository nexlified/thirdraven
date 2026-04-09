"""
Integration tests for the organizations API.
Mirrors: frontend/src/api/organizations.ts
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/organizations"


async def _create_person(api_client: AsyncClient, auth_headers: dict) -> str:
    resp = await api_client.post(
        "/api/v1/persons/",
        json={"first_name": "OrgPerson"},
        headers=auth_headers,
    )
    return resp.json()["id"]


async def test_create_organization(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.post(
        f"{BASE}/",
        json={"name": "Acme Corp", "description": "A test company"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Acme Corp"
    assert "id" in body
    assert "owner_id" in body


async def test_list_organizations_pagination_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(f"{BASE}/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"items", "total", "skip", "limit"}
    assert isinstance(body["items"], list)


async def test_get_organization(api_client: AsyncClient, auth_headers: dict) -> None:
    org_id = (
        await api_client.post(
            f"{BASE}/",
            json={"name": "Fetch Corp"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.get(f"{BASE}/{org_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == org_id


async def test_update_organization(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    org_id = (
        await api_client.post(
            f"{BASE}/",
            json={"name": "Old Corp"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.patch(
        f"{BASE}/{org_id}",
        json={"name": "New Corp", "website": "https://newcorp.example"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Corp"


async def test_delete_organization_returns_204(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    org_id = (
        await api_client.post(
            f"{BASE}/",
            json={"name": "Delete Corp"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.delete(f"{BASE}/{org_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert resp.content == b""


async def test_link_person_to_organization(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    org_id = (
        await api_client.post(
            f"{BASE}/",
            json={"name": "Link Org"},
            headers=auth_headers,
        )
    ).json()["id"]
    person_id = await _create_person(api_client, auth_headers)

    resp = await api_client.post(
        f"/api/v1/persons/{person_id}/organizations/",
        json={"org_id": org_id, "role": "Engineer"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["person_id"] == person_id
    assert body["org"]["id"] == org_id
    assert body["role"] == "Engineer"


async def test_list_organizations_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{BASE}/")
    assert resp.status_code == 401
    assert "detail" in resp.json()
