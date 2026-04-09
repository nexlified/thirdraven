"""
Integration tests for the subscriptions API.
Mirrors: frontend/src/api/subscriptions.ts
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/subscriptions"


async def test_create_subscription(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.post(
        f"{BASE}/",
        json={
            "name": "Netflix",
            "cost": 499.0,
            "currency": "INR",
            "billing_cycle": "monthly",
            "status": "active",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Netflix"
    assert body["cost"] == 499.0
    assert "id" in body
    assert "owner_id" in body
    assert isinstance(body["tags"], list)


async def test_list_subscriptions_pagination_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(f"{BASE}/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"items", "total", "skip", "limit"}
    assert isinstance(body["items"], list)


async def test_get_subscription(api_client: AsyncClient, auth_headers: dict) -> None:
    sub_id = (
        await api_client.post(
            f"{BASE}/",
            json={"name": "Spotify", "cost": 199.0, "currency": "INR"},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.get(f"{BASE}/{sub_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == sub_id


async def test_update_subscription(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    sub_id = (
        await api_client.post(
            f"{BASE}/",
            json={"name": "Old Name", "cost": 100.0},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.patch(
        f"{BASE}/{sub_id}",
        json={"name": "New Name", "cost": 150.0},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"
    assert resp.json()["cost"] == 150.0


async def test_delete_subscription_returns_204(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    sub_id = (
        await api_client.post(
            f"{BASE}/",
            json={"name": "Delete Me", "cost": 99.0},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.delete(f"{BASE}/{sub_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert resp.content == b""


async def test_subscription_summary_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(f"{BASE}/summary", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "total_active" in body
    assert "monthly_cost_by_currency" in body
    assert "upcoming_renewals" in body
    assert "cost_by_category" in body


async def test_list_subscriptions_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{BASE}/")
    assert resp.status_code == 401
    assert "detail" in resp.json()
