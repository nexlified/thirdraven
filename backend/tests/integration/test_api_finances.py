"""
Integration tests for the finances overview API.
Mirrors: frontend/src/api/finances.ts
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/finances"


async def test_finance_overview_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(
        f"{BASE}/overview", params={"currency": "INR"}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    # FinanceOverview fields
    assert "financial_assets" in body
    assert "total_asset_value_by_currency" in body
    assert "outstanding_loans" in body
    assert "total_lent_by_currency" in body
    assert "total_borrowed_by_currency" in body
    assert "current_month_income" in body
    assert "current_month_expenses" in body
    assert "current_month_net" in body
    assert "monthly_subscription_cost_by_currency" in body
    assert "as_of" in body
    assert isinstance(body["financial_assets"], list)
    assert isinstance(body["outstanding_loans"], list)


async def test_finance_overview_default_currency(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    # Default currency is INR if not specified
    resp = await api_client.get(f"{BASE}/overview", headers=auth_headers)
    assert resp.status_code == 200


async def test_finance_overview_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{BASE}/overview")
    assert resp.status_code == 401
    assert "detail" in resp.json()
