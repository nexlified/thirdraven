"""
Integration tests for the budgets API.
Mirrors: frontend/src/api/budgets.ts

Note: GET /budgets/ requires ?year and ?month query params (no defaults).
BudgetCreate requires a category slug from expense-categories vocabulary.
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/budgets"

# expense-categories slug confirmed from seeds/seed_data.py
CATEGORY = "groceries"


async def test_create_budget(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.post(
        f"{BASE}/",
        json={
            "category": CATEGORY,
            "year": 2026,
            "month": 4,
            "amount": 5000.0,
            "currency": "INR",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["year"] == 2026
    assert body["month"] == 4
    assert body["amount"] == 5000.0
    assert "id" in body
    assert "owner_id" in body
    # category is a TermSlim (resolved from slug)
    assert "category" in body
    assert body["category"]["slug"] == CATEGORY


async def test_list_budgets_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    # First create a budget so we have something to list
    await api_client.post(
        f"{BASE}/",
        json={"category": CATEGORY, "year": 2026, "month": 5, "amount": 3000.0},
        headers=auth_headers,
    )
    # GET requires year + month — returns list (not paginated)
    resp = await api_client.get(
        f"{BASE}/", params={"year": 2026, "month": 5}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    # BudgetWithSpend shape
    first = body[0]
    assert "id" in first
    assert "amount" in first
    assert "spent" in first
    assert "remaining" in first
    assert "utilization" in first


async def test_update_budget(api_client: AsyncClient, auth_headers: dict) -> None:
    budget_id = (
        await api_client.post(
            f"{BASE}/",
            json={"category": CATEGORY, "year": 2026, "month": 6, "amount": 2000.0},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.patch(
        f"{BASE}/{budget_id}",
        json={"amount": 2500.0, "notes": "Increased budget"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["amount"] == 2500.0
    assert resp.json()["notes"] == "Increased budget"


async def test_delete_budget_returns_204(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    budget_id = (
        await api_client.post(
            f"{BASE}/",
            json={"category": CATEGORY, "year": 2026, "month": 7, "amount": 1000.0},
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.delete(f"{BASE}/{budget_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert resp.content == b""


async def test_list_budgets_missing_params(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    # year and month are required
    resp = await api_client.get(f"{BASE}/", headers=auth_headers)
    assert resp.status_code == 422


async def test_list_budgets_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{BASE}/", params={"year": 2026, "month": 4})
    assert resp.status_code == 401
    assert "detail" in resp.json()
