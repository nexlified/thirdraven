"""
Integration tests for the assets API.
Mirrors: frontend/src/api/assets.ts
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/assets"

# Slugs confirmed present in seeds/seed_data.py
CATEGORY = "electronics"   # asset-categories
STATUS = "active"          # asset-statuses


async def test_create_asset(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.post(
        f"{BASE}/",
        json={
            "name": "MacBook Pro",
            "category": CATEGORY,
            "status": STATUS,
            "purchase_price": 150000.0,
            "purchase_price_currency": "INR",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "MacBook Pro"
    assert "id" in body
    assert "owner_id" in body
    assert "category" in body
    assert "status" in body


async def test_list_assets_pagination_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(f"{BASE}/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"items", "total", "skip", "limit"}
    assert isinstance(body["items"], list)
    assert isinstance(body["total"], int)


async def test_get_asset(api_client: AsyncClient, auth_headers: dict) -> None:
    asset_id = (
        await api_client.post(
            f"{BASE}/",
            json={"name": "Get Me", "category": CATEGORY},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.get(f"{BASE}/{asset_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == asset_id


async def test_update_asset(api_client: AsyncClient, auth_headers: dict) -> None:
    asset_id = (
        await api_client.post(
            f"{BASE}/",
            json={"name": "Old Name", "category": CATEGORY},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.patch(
        f"{BASE}/{asset_id}",
        json={"name": "New Name", "status": "retired"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


async def test_delete_asset_returns_204(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    asset_id = (
        await api_client.post(
            f"{BASE}/",
            json={"name": "Delete Me", "category": CATEGORY},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.delete(f"{BASE}/{asset_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert resp.content == b""


async def test_list_assets_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{BASE}/")
    assert resp.status_code == 401
    assert "detail" in resp.json()
