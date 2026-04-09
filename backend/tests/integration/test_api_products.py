"""
Integration tests for the products API.
Mirrors: frontend/src/api/products.ts

Note: POST /products/ may return 200 (deduplication) or 201 (new product).
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/products"


async def test_create_product(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.post(
        f"{BASE}/",
        json={"name": "Basmati Rice 5kg", "brand": "India Gate"},
        headers=auth_headers,
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body["name"] == "Basmati Rice 5kg"
    assert body["brand"] == "India Gate"
    assert "id" in body
    assert "owner_id" in body


async def test_create_product_dedup_returns_200(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    payload = {"name": "Unique Product Dedup", "brand": "BrandX"}
    resp1 = await api_client.post(f"{BASE}/", json=payload, headers=auth_headers)
    assert resp1.status_code == 201

    resp2 = await api_client.post(f"{BASE}/", json=payload, headers=auth_headers)
    assert resp2.status_code == 200
    # Same id returned on dedup
    assert resp1.json()["id"] == resp2.json()["id"]


async def test_list_products_pagination_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(f"{BASE}/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"items", "total", "skip", "limit"}
    assert isinstance(body["items"], list)


async def test_get_product(api_client: AsyncClient, auth_headers: dict) -> None:
    product_id = (
        await api_client.post(
            f"{BASE}/",
            json={"name": "Get Me Product"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.get(f"{BASE}/{product_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == product_id


async def test_update_product(api_client: AsyncClient, auth_headers: dict) -> None:
    product_id = (
        await api_client.post(
            f"{BASE}/",
            json={"name": "Old Product Name"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.patch(
        f"{BASE}/{product_id}",
        json={"name": "Updated Product Name", "notes": "Updated"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Product Name"


async def test_delete_product_returns_204(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    product_id = (
        await api_client.post(
            f"{BASE}/",
            json={"name": "Delete Me Product"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.delete(f"{BASE}/{product_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert resp.content == b""


async def test_get_product_items(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    product_id = (
        await api_client.post(
            f"{BASE}/",
            json={"name": "Items Test Product"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.get(f"{BASE}/{product_id}/items", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"items", "total", "skip", "limit"}
    assert isinstance(body["items"], list)


async def test_list_products_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{BASE}/")
    assert resp.status_code == 401
    assert "detail" in resp.json()
