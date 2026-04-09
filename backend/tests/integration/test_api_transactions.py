"""
Integration tests for the transactions API.
Mirrors: frontend/src/api/transactions.ts
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/transactions"

_TX = {
    "transaction_type": "expense",
    "amount": 250.0,
    "currency": "INR",
    "transacted_on": "2026-04-01",
    "description": "Lunch at café",
    "category": "food",
}


async def test_create_transaction(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.post(f"{BASE}/", json=_TX, headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["transaction_type"] == "expense"
    assert body["amount"] == 250.0
    assert "id" in body
    assert "owner_id" in body


async def test_list_transactions_pagination_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(f"{BASE}/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"items", "total", "skip", "limit"}
    assert isinstance(body["items"], list)


async def test_get_transaction(api_client: AsyncClient, auth_headers: dict) -> None:
    tx_id = (
        await api_client.post(f"{BASE}/", json=_TX, headers=auth_headers)
    ).json()["id"]

    resp = await api_client.get(f"{BASE}/{tx_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == tx_id


async def test_update_transaction(api_client: AsyncClient, auth_headers: dict) -> None:
    tx_id = (
        await api_client.post(f"{BASE}/", json=_TX, headers=auth_headers)
    ).json()["id"]

    resp = await api_client.patch(
        f"{BASE}/{tx_id}",
        json={"amount": 300.0, "description": "Updated"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["amount"] == 300.0
    assert resp.json()["description"] == "Updated"


async def test_delete_transaction_returns_204(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    tx_id = (
        await api_client.post(f"{BASE}/", json=_TX, headers=auth_headers)
    ).json()["id"]

    resp = await api_client.delete(f"{BASE}/{tx_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert resp.content == b""


async def test_bulk_create_transactions(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    payload = [
        {**_TX, "description": "Bulk 1"},
        {
            **_TX,
            "transaction_type": "income",
            "description": "Bulk 2",
            "category": "salary",
        },
    ]
    resp = await api_client.post(f"{BASE}/bulk", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 2


async def test_transaction_summary_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(
        f"{BASE}/summary",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31", "currency": "INR"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "total_income" in body
    assert "total_expense" in body
    assert "net" in body
    assert "period_from" in body
    assert "period_to" in body


async def test_parse_transaction(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.post(
        f"{BASE}/parse",
        json={"input": "spent 500 on groceries", "currency": "INR"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    # Returns TransactionCreate shape
    assert "transaction_type" in body
    assert "amount" in body
    assert "description" in body


async def test_list_transactions_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{BASE}/")
    assert resp.status_code == 401
    assert "detail" in resp.json()
