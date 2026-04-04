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
from app.schemas.transaction import (
    CategoryBreakdown,
    DailyTotal,
    TransactionPublic,
    TransactionSummary,
)
from app.schemas.transaction_item import TransactionItemPublic
from app.schemas.vocabulary import TermSlim

OWNER_ID = uuid.uuid4()
TX_ID = uuid.uuid4()
CAT_TERM_ID = uuid.uuid4()
PM_TERM_ID = uuid.uuid4()
ITEM_ID = uuid.uuid4()
PRODUCT_ID = uuid.uuid4()

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


def make_transaction_item(**kwargs) -> TransactionItemPublic:
    defaults = dict(
        id=ITEM_ID,
        transaction_id=TX_ID,
        product_id=PRODUCT_ID,
        product=None,
        raw_name="AMUL MILK 1L",
        quantity=1.0,
        unit="L",
        unit_price=65.0,
        total_price=65.0,
        currency="INR",
        discount=0.0,
        store_name="DMart",
        import_batch_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return TransactionItemPublic(**defaults)


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


def _make_summary(**kwargs) -> TransactionSummary:
    defaults = dict(
        period_from=date(2026, 4, 1),
        period_to=date(2026, 4, 30),
        total_income=50000.0,
        total_expense=12500.0,
        net=37500.0,
        savings_rate=0.75,
        expense_by_category=[
            CategoryBreakdown(
                category_slug="food",
                category_name="Food & Dining",
                total=5000.0,
                count=10,
                percentage=40.0,
            )
        ],
        income_by_category=[
            CategoryBreakdown(
                category_slug="salary",
                category_name="Salary",
                total=50000.0,
                count=1,
                percentage=100.0,
            )
        ],
        daily_totals=[DailyTotal(date=date(2026, 4, 1), income=50000.0, expense=500.0)],
        currency="INR",
    )
    defaults.update(kwargs)
    return TransactionSummary(**defaults)


def test_summary_default_params(app_client):
    s = _make_summary()
    with patch(
        "app.api.v1.transactions.get_transaction_summary",
        new=AsyncMock(return_value=s),
    ):
        resp = app_client.get("/api/v1/transactions/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_income"] == 50000.0
    assert body["total_expense"] == 12500.0
    assert body["net"] == 37500.0
    assert body["savings_rate"] == 0.75
    assert body["currency"] == "INR"


def test_summary_with_date_range(app_client):
    s = _make_summary()
    with patch(
        "app.api.v1.transactions.get_transaction_summary",
        new=AsyncMock(return_value=s),
    ) as mock_summary:
        resp = app_client.get(
            "/api/v1/transactions/summary",
            params={"date_from": "2026-04-01", "date_to": "2026-04-30"},
        )
    assert resp.status_code == 200
    call_args = mock_summary.call_args
    # positional: (db, owner_id, date_from, date_to, currency)
    assert str(call_args.args[2]) == "2026-04-01"
    assert str(call_args.args[3]) == "2026-04-30"


def test_summary_custom_currency(app_client):
    s = _make_summary(currency="USD")
    with patch(
        "app.api.v1.transactions.get_transaction_summary",
        new=AsyncMock(return_value=s),
    ) as mock_summary:
        resp = app_client.get(
            "/api/v1/transactions/summary", params={"currency": "USD"}
        )
    assert resp.status_code == 200
    call_args = mock_summary.call_args
    # positional: (db, owner_id, date_from, date_to, currency)
    assert call_args.args[4] == "USD"


def test_summary_null_savings_rate(app_client):
    s = _make_summary(total_income=0.0, net=-5000.0, savings_rate=None)
    with patch(
        "app.api.v1.transactions.get_transaction_summary",
        new=AsyncMock(return_value=s),
    ):
        resp = app_client.get("/api/v1/transactions/summary")
    assert resp.status_code == 200
    assert resp.json()["savings_rate"] is None


def test_summary_category_breakdown(app_client):
    s = _make_summary()
    with patch(
        "app.api.v1.transactions.get_transaction_summary",
        new=AsyncMock(return_value=s),
    ):
        resp = app_client.get("/api/v1/transactions/summary")
    body = resp.json()
    assert len(body["expense_by_category"]) == 1
    cat = body["expense_by_category"][0]
    assert cat["category_slug"] == "food"
    assert cat["percentage"] == 40.0
    assert cat["count"] == 10


def test_summary_daily_totals(app_client):
    s = _make_summary()
    with patch(
        "app.api.v1.transactions.get_transaction_summary",
        new=AsyncMock(return_value=s),
    ):
        resp = app_client.get("/api/v1/transactions/summary")
    body = resp.json()
    assert len(body["daily_totals"]) == 1
    assert body["daily_totals"][0]["date"] == "2026-04-01"
    assert body["daily_totals"][0]["income"] == 50000.0


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
        resp = app_client.patch(f"/api/v1/transactions/{TX_ID}", json={"amount": 300.0})
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


# ── POST /transactions/parse ───────────────────────────────────────────────────

EXPENSE_SLUGS = {"fuel", "groceries", "food", "shopping"}
INCOME_SLUGS = {"salary", "freelance"}


def test_parse_transaction_expense(app_client):
    from app.core.transaction_parser import ParsedTransaction

    parsed = ParsedTransaction(
        transaction_type="expense",
        amount=500.0,
        description="",
        category_slug="fuel",
        merchant="fuel",
        transacted_on=date(2026, 4, 1),
    )
    with (
        patch(
            "app.api.v1.transactions.get_vocabulary_slugs",
            new=AsyncMock(side_effect=[EXPENSE_SLUGS, INCOME_SLUGS]),
        ),
        patch(
            "app.core.transaction_parser.parse_transaction_input",
            return_value=parsed,
        ),
    ):
        resp = app_client.post(
            "/api/v1/transactions/parse",
            json={"input": "500 fuel"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["transaction_type"] == "expense"
    assert body["amount"] == 500.0
    assert body["category"] == "fuel"
    assert body["merchant"] == "fuel"


def test_parse_transaction_income(app_client):
    from app.core.transaction_parser import ParsedTransaction

    parsed = ParsedTransaction(
        transaction_type="income",
        amount=50000.0,
        description="",
        category_slug="salary",
        merchant=None,
        transacted_on=date(2026, 4, 1),
    )
    with (
        patch(
            "app.api.v1.transactions.get_vocabulary_slugs",
            new=AsyncMock(side_effect=[EXPENSE_SLUGS, INCOME_SLUGS]),
        ),
        patch(
            "app.core.transaction_parser.parse_transaction_input",
            return_value=parsed,
        ),
    ):
        resp = app_client.post(
            "/api/v1/transactions/parse",
            json={"input": "salary 50000"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["transaction_type"] == "income"
    assert body["amount"] == 50000.0
    assert body["category"] == "salary"


def test_parse_transaction_no_amount_returns_400(app_client):
    with (
        patch(
            "app.api.v1.transactions.get_vocabulary_slugs",
            new=AsyncMock(side_effect=[EXPENSE_SLUGS, INCOME_SLUGS]),
        ),
        patch(
            "app.api.v1.transactions.parse_transaction_input",
            side_effect=ValueError("No numeric amount found in input"),
        ),
    ):
        resp = app_client.post(
            "/api/v1/transactions/parse",
            json={"input": "fuel random stuff"},
        )
    assert resp.status_code == 400
    assert "No numeric amount" in resp.json()["detail"]


def test_parse_transaction_custom_currency(app_client):
    from app.core.transaction_parser import ParsedTransaction

    parsed = ParsedTransaction(
        transaction_type="expense",
        amount=100.0,
        description="",
        category_slug="food",
        merchant="food",
        transacted_on=date(2026, 4, 1),
    )
    with (
        patch(
            "app.api.v1.transactions.get_vocabulary_slugs",
            new=AsyncMock(side_effect=[EXPENSE_SLUGS, INCOME_SLUGS]),
        ),
        patch(
            "app.core.transaction_parser.parse_transaction_input",
            return_value=parsed,
        ),
    ):
        resp = app_client.post(
            "/api/v1/transactions/parse",
            json={"input": "100 food", "currency": "USD"},
        )
    assert resp.status_code == 200
    assert resp.json()["currency"] == "USD"


def test_parse_transaction_no_category(app_client):
    from app.core.transaction_parser import ParsedTransaction

    parsed = ParsedTransaction(
        transaction_type="expense",
        amount=99.0,
        description="random stuff",
        category_slug=None,
        merchant=None,
        transacted_on=date(2026, 4, 1),
    )
    with (
        patch(
            "app.api.v1.transactions.get_vocabulary_slugs",
            new=AsyncMock(side_effect=[EXPENSE_SLUGS, INCOME_SLUGS]),
        ),
        patch(
            "app.core.transaction_parser.parse_transaction_input",
            return_value=parsed,
        ),
    ):
        resp = app_client.post(
            "/api/v1/transactions/parse",
            json={"input": "random stuff 99"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"] is None
    assert body["description"] == "random stuff"


# ── POST /transactions/quick-add ──────────────────────────────────────────────


def test_quick_add_transaction_success(app_client):
    from app.core.transaction_parser import ParsedTransaction

    parsed = ParsedTransaction(
        transaction_type="expense",
        amount=500.0,
        description="",
        category_slug="fuel",
        merchant="fuel",
        transacted_on=date(2026, 4, 1),
    )
    tx = make_transaction(
        transaction_type="expense",
        amount=500.0,
        description="fuel",
        merchant="fuel",
    )
    with (
        patch(
            "app.api.v1.transactions.get_vocabulary_slugs",
            new=AsyncMock(side_effect=[EXPENSE_SLUGS, INCOME_SLUGS]),
        ),
        patch(
            "app.core.transaction_parser.parse_transaction_input",
            return_value=parsed,
        ),
        patch(
            "app.api.v1.transactions.create_transaction",
            new=AsyncMock(return_value=tx),
        ),
    ):
        resp = app_client.post(
            "/api/v1/transactions/quick-add",
            json={"input": "500 fuel"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["transaction_type"] == "expense"
    assert body["amount"] == 500.0


# -- /transactions/{id}/items -------------------------------------------------


def test_create_transaction_item_success(app_client):
    item = make_transaction_item()
    with patch(
        "app.api.v1.transactions.create_transaction_item",
        new=AsyncMock(return_value=item),
    ):
        resp = app_client.post(
            f"/api/v1/transactions/{TX_ID}/items/",
            json={
                "raw_name": "AMUL MILK 1L",
                "quantity": 1,
                "unit": "L",
                "unit_price": 65,
                "total_price": 65,
            },
        )
    assert resp.status_code == 201
    assert resp.json()["id"] == str(ITEM_ID)


def test_create_transaction_item_not_found(app_client):
    with patch(
        "app.api.v1.transactions.create_transaction_item",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.post(
            f"/api/v1/transactions/{uuid.uuid4()}/items/",
            json={
                "raw_name": "AMUL MILK 1L",
                "quantity": 1,
                "unit_price": 65,
                "total_price": 65,
            },
        )
    assert resp.status_code == 404


def test_bulk_create_transaction_items_success(app_client):
    item = make_transaction_item()
    with patch(
        "app.api.v1.transactions.create_transaction_items_bulk",
        new=AsyncMock(return_value=[item]),
    ):
        resp = app_client.post(
            f"/api/v1/transactions/{TX_ID}/items/bulk",
            json=[
                {
                    "raw_name": "AMUL MILK 1L",
                    "quantity": 1,
                    "unit_price": 65,
                    "total_price": 65,
                }
            ],
        )
    assert resp.status_code == 201
    assert len(resp.json()) == 1


def test_bulk_create_transaction_items_not_found(app_client):
    with patch(
        "app.api.v1.transactions.create_transaction_items_bulk",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.post(
            f"/api/v1/transactions/{uuid.uuid4()}/items/bulk",
            json=[
                {
                    "raw_name": "AMUL MILK 1L",
                    "quantity": 1,
                    "unit_price": 65,
                    "total_price": 65,
                }
            ],
        )
    assert resp.status_code == 404


def test_list_transaction_items_success(app_client):
    item = make_transaction_item()
    with patch(
        "app.api.v1.transactions.list_transaction_items",
        new=AsyncMock(return_value=[item]),
    ):
        resp = app_client.get(f"/api/v1/transactions/{TX_ID}/items/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_transaction_items_not_found(app_client):
    with patch(
        "app.api.v1.transactions.list_transaction_items",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.get(f"/api/v1/transactions/{uuid.uuid4()}/items/")
    assert resp.status_code == 404


def test_patch_transaction_item_success(app_client):
    item = make_transaction_item(quantity=2.0, total_price=130.0)
    with patch(
        "app.api.v1.transactions.update_transaction_item",
        new=AsyncMock(return_value=item),
    ):
        resp = app_client.patch(
            f"/api/v1/transactions/{TX_ID}/items/{ITEM_ID}",
            json={"quantity": 2.0, "total_price": 130.0},
        )
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 2.0


def test_patch_transaction_item_not_found(app_client):
    with patch(
        "app.api.v1.transactions.update_transaction_item",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.patch(
            f"/api/v1/transactions/{TX_ID}/items/{uuid.uuid4()}",
            json={"quantity": 2.0},
        )
    assert resp.status_code == 404


def test_delete_transaction_item_success(app_client):
    with patch(
        "app.api.v1.transactions.delete_transaction_item",
        new=AsyncMock(return_value=True),
    ):
        resp = app_client.delete(f"/api/v1/transactions/{TX_ID}/items/{ITEM_ID}")
    assert resp.status_code == 204


def test_delete_transaction_item_not_found(app_client):
    with patch(
        "app.api.v1.transactions.delete_transaction_item",
        new=AsyncMock(return_value=False),
    ):
        resp = app_client.delete(f"/api/v1/transactions/{TX_ID}/items/{uuid.uuid4()}")
    assert resp.status_code == 404
