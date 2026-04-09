"""
Integration tests for the loans API.
Mirrors: frontend/src/api/loans.ts

Loans require a person_id. We create a person first via the persons API.
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/loans"


async def _create_person(api_client: AsyncClient, auth_headers: dict) -> str:
    resp = await api_client.post(
        "/api/v1/persons/",
        json={"first_name": "LoanPerson"},
        headers=auth_headers,
    )
    return resp.json()["id"]


async def test_create_loan(api_client: AsyncClient, auth_headers: dict) -> None:
    person_id = await _create_person(api_client, auth_headers)
    resp = await api_client.post(
        f"{BASE}/",
        json={
            "person_id": person_id,
            "direction": "lent",
            "loan_type": "money",
            "description": "Lunch money",
            "amount": 500.0,
            "currency": "INR",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["direction"] == "lent"
    assert body["amount"] == 500.0
    assert body["person_id"] == person_id
    assert "id" in body
    assert "owner_id" in body


async def test_list_loans_pagination_shape(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(f"{BASE}/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"items", "total", "skip", "limit"}
    assert isinstance(body["items"], list)


async def test_get_loan(api_client: AsyncClient, auth_headers: dict) -> None:
    person_id = await _create_person(api_client, auth_headers)
    loan_id = (
        await api_client.post(
            f"{BASE}/",
            json={
                "person_id": person_id,
                "direction": "borrowed",
                "loan_type": "money",
                "description": "Book",
                "amount": 200.0,
            },
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.get(f"{BASE}/{loan_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == loan_id


async def test_update_loan(api_client: AsyncClient, auth_headers: dict) -> None:
    person_id = await _create_person(api_client, auth_headers)
    loan_id = (
        await api_client.post(
            f"{BASE}/",
            json={
                "person_id": person_id,
                "direction": "lent",
                "loan_type": "item",
                "description": "Camera",
            },
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.patch(
        f"{BASE}/{loan_id}",
        json={"status": "returned", "description": "Camera returned"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "returned"


async def test_delete_loan_returns_204(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    person_id = await _create_person(api_client, auth_headers)
    loan_id = (
        await api_client.post(
            f"{BASE}/",
            json={
                "person_id": person_id,
                "direction": "lent",
                "loan_type": "money",
                "description": "Delete me",
                "amount": 100.0,
            },
            headers=auth_headers,
        )
    ).json()["id"]

    resp = await api_client.delete(f"{BASE}/{loan_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert resp.content == b""


async def test_list_loans_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{BASE}/")
    assert resp.status_code == 401
    assert "detail" in resp.json()
