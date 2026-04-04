import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.transactions import router as transactions_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.transaction import TransactionPublic
from app.schemas.vocabulary import TermSlim

OWNER_ID = uuid.uuid4()
TX_ID = uuid.uuid4()
CAT_TERM_ID = uuid.uuid4()
PM_TERM_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)

FOOD_TERM = TermSlim(id=CAT_TERM_ID, name="Food & Dining", slug="food")
UPI_TERM = TermSlim(id=PM_TERM_ID, name="UPI", slug="upi")


def make_transaction(**kwargs) -> TransactionPublic:
    defaults = dict(
        id=TX_ID,
        owner_id=OWNER_ID,
        transaction_type="expense",
        amount=250.0,
        currency="INR",
        transacted_on=date(2026, 4, 1),
        description="Lunch at cafe",
        category=FOOD_TERM,
        payment_method=UPI_TERM,
        asset_id=None,
        subscription_id=None,
        merchant="Cafe Blue",
        reference=None,
        tags=[],
        import_batch_id=None,
        notes=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return TransactionPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(transactions_router, prefix="/api/v1")

    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    async def override_get_current_user():
        return FAKE_USER

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ── POST /transactions/ ────────────────────────────────────────────────────────


def test_create_transaction_success(app_client):
    tx = make_transaction()
    with patch(
        "app.api.v1.transactions.create_transaction",
        new=AsyncMock(return_value=tx),
    ):
        resp = app_client.post(
            "/api/v1/transactions/",
            json={
                "transaction_type": "expense",
                "amount": 250.0,
                "transacted_on": "2026-04-01",
                "description": "Lunch at cafe",
            },
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["transaction_type"] == "expense"
    assert body["amount"] == 250.0
    assert body["owner_id"] == str(OWNER_ID)


def test_create_transaction_invalid_type(app_client):
    resp = app_client.post(
        "/api/v1/transactions/",
        json={
            "transaction_type": "transfer",
            "amount": 100.0,
            "transacted_on": "2026-04-01",
            "description": "Invalid",
        },
    )
    assert resp.status_code == 422


def test_create_transaction_missing_required(app_client):
    resp = app_client.post(
        "/api/v1/transactions/",
        json={"transaction_type": "expense", "amount": 100.0},
    )
    assert resp.status_code == 422


def test_create_transaction_income(app_client):
    tx = make_transaction(transaction_type="income", description="Salary")
    with patch(
        "app.api.v1.transactions.create_transaction",
        new=AsyncMock(return_value=tx),
    ):
        resp = app_client.post(
            "/api/v1/transactions/",
            json={
                "transaction_type": "income",
                "amount": 50000.0,
                "transacted_on": "2026-04-01",
                "description": "Salary",
            },
        )
    assert resp.status_code == 201
    assert resp.json()["transaction_type"] == "income"


# ── POST /transactions/bulk ────────────────────────────────────────────────────


def test_bulk_create_transactions(app_client):
    tx1 = make_transaction(id=uuid.uuid4(), description="Lunch")
    tx2 = make_transaction(id=uuid.uuid4(), description="Dinner")
    with patch(
        "app.api.v1.transactions.create_transactions_bulk",
        new=AsyncMock(return_value=[tx1, tx2]),
    ):
        resp = app_client.post(
            "/api/v1/transactions/bulk",
            json=[
                {
                    "transaction_type": "expense",
                    "amount": 150.0,
                    "transacted_on": "2026-04-01",
                    "description": "Lunch",
                },
                {
                    "transaction_type": "expense",
                    "amount": 200.0,
                    "transacted_on": "2026-04-01",
                    "description": "Dinner",
                },
            ],
        )
    assert resp.status_code == 201
    assert len(resp.json()) == 2


# ── GET /transactions/summary ──────────────────────────────────────────────────


def test_summary_returns_501(app_client):
    resp = app_client.get("/api/v1/transactions/summary")
    assert resp.status_code == 501


# ── GET /transactions/ ─────────────────────────────────────────────────────────


def test_list_transactions(app_client):
    tx = make_transaction()
    with patch(
        "app.api.v1.transactions.list_transactions",
        new=AsyncMock(return_value=([tx], 1)),
    ):
        resp = app_client.get("/api/v1/transactions/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_list_transactions_with_filters(app_client):
    tx = make_transaction()
    with patch(
        "app.api.v1.transactions.list_transactions",
        new=AsyncMock(return_value=([tx], 1)),
    ) as mock_list:
        resp = app_client.get(
            "/api/v1/transactions/",
            params={
                "transaction_type": "expense",
                "category": "food",
                "search": "cafe",
                "date_from": "2026-04-01",
                "date_to": "2026-04-30",
            },
        )
    assert resp.status_code == 200
    _, call_kwargs = mock_list.call_args
    assert call_kwargs["transaction_type"] == "expense"
    assert call_kwargs["category_slug"] == "food"
    assert call_kwargs["search"] == "cafe"


def test_list_transactions_empty(app_client):
    with patch(
        "app.api.v1.transactions.list_transactions",
        new=AsyncMock(return_value=([], 0)),
    ):
        resp = app_client.get("/api/v1/transactions/")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
    assert resp.json()["items"] == []


# ── GET /transactions/{id} ─────────────────────────────────────────────────────


def test_get_transaction_success(app_client):
    tx = make_transaction()
    with patch(
        "app.api.v1.transactions.get_transaction_public",
        new=AsyncMock(return_value=tx),
    ):
        resp = app_client.get(f"/api/v1/transactions/{TX_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(TX_ID)


def test_get_transaction_not_found(app_client):
    with patch(
        "app.api.v1.transactions.get_transaction_public",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.get(f"/api/v1/transactions/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /transactions/{id} ───────────────────────────────────────────────────


def test_patch_transaction_success(app_client):
    tx = make_transaction(amount=300.0)
    with patch(
        "app.api.v1.transactions.update_transaction",
        new=AsyncMock(return_value=tx),
    ):
        resp = app_client.patch(
            f"/api/v1/transactions/{TX_ID}", json={"amount": 300.0}
        )
    assert resp.status_code == 200
    assert resp.json()["amount"] == 300.0


def test_patch_transaction_not_found(app_client):
    with patch(
        "app.api.v1.transactions.update_transaction",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.patch(
            f"/api/v1/transactions/{uuid.uuid4()}", json={"amount": 300.0}
        )
    assert resp.status_code == 404


def test_patch_transaction_invalid_type(app_client):
    resp = app_client.patch(
        f"/api/v1/transactions/{TX_ID}", json={"transaction_type": "invalid"}
    )
    assert resp.status_code == 422


# ── DELETE /transactions/{id} ──────────────────────────────────────────────────


def test_delete_transaction_success(app_client):
    from app.models.transaction import Transaction

    fake_tx = Transaction(
        id=TX_ID,
        owner_id=OWNER_ID,
        transaction_type="expense",
        amount=250.0,
        currency="INR",
        transacted_on=date(2026, 4, 1),
        description="Lunch",
    )
    with patch(
        "app.api.v1.transactions.soft_delete_transaction",
        new=AsyncMock(return_value=fake_tx),
    ):
        resp = app_client.delete(f"/api/v1/transactions/{TX_ID}")
    assert resp.status_code == 204


def test_delete_transaction_not_found(app_client):
    with patch(
        "app.api.v1.transactions.soft_delete_transaction",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.delete(f"/api/v1/transactions/{uuid.uuid4()}")
    assert resp.status_code == 404
