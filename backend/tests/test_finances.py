import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.finances import router as finances_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.finance import (
    AssetSummaryItem,
    FinanceOverview,
    LoanSummaryItem,
)
from app.schemas.transaction import CategoryBreakdown

OWNER_ID = uuid.uuid4()
ASSET_ID = uuid.uuid4()
LOAN_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)


def make_overview(**kwargs) -> FinanceOverview:
    defaults = dict(
        financial_assets=[
            AssetSummaryItem(
                asset_id=ASSET_ID,
                name="HDFC Savings",
                account_type="Savings Account",
                institution="HDFC Bank",
                current_balance=150000.0,
                currency="INR",
            )
        ],
        total_asset_value_by_currency={"INR": 150000.0},
        outstanding_loans=[
            LoanSummaryItem(
                loan_id=LOAN_ID,
                direction="lent",
                person_name="Alice Smith",
                amount=5000.0,
                currency="INR",
                status="outstanding",
                due_on=date(2026, 6, 1),
            )
        ],
        total_lent_by_currency={"INR": 5000.0},
        total_borrowed_by_currency={},
        current_month_income=50000.0,
        current_month_expenses=12500.0,
        current_month_net=37500.0,
        current_month_savings_rate=0.75,
        current_month_currency="INR",
        top_expense_categories=[
            CategoryBreakdown(
                category_slug="food",
                category_name="Food & Dining",
                total=5000.0,
                count=10,
                percentage=40.0,
            )
        ],
        monthly_subscription_cost_by_currency={"INR": 1299.0},
        as_of=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return FinanceOverview(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(finances_router, prefix="/api/v1")

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


# ── GET /finances/overview ─────────────────────────────────────────────────────


def test_overview_success(app_client):
    ov = make_overview()
    with patch(
        "app.api.v1.finances.get_finance_overview",
        new=AsyncMock(return_value=ov),
    ):
        resp = app_client.get("/api/v1/finances/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_month_income"] == 50000.0
    assert body["current_month_expenses"] == 12500.0
    assert body["current_month_net"] == 37500.0
    assert body["current_month_savings_rate"] == 0.75
    assert body["current_month_currency"] == "INR"


def test_overview_financial_assets(app_client):
    ov = make_overview()
    with patch(
        "app.api.v1.finances.get_finance_overview",
        new=AsyncMock(return_value=ov),
    ):
        resp = app_client.get("/api/v1/finances/overview")
    body = resp.json()
    assert len(body["financial_assets"]) == 1
    asset = body["financial_assets"][0]
    assert asset["name"] == "HDFC Savings"
    assert asset["institution"] == "HDFC Bank"
    assert asset["current_balance"] == 150000.0
    assert body["total_asset_value_by_currency"] == {"INR": 150000.0}


def test_overview_outstanding_loans(app_client):
    ov = make_overview()
    with patch(
        "app.api.v1.finances.get_finance_overview",
        new=AsyncMock(return_value=ov),
    ):
        resp = app_client.get("/api/v1/finances/overview")
    body = resp.json()
    assert len(body["outstanding_loans"]) == 1
    loan = body["outstanding_loans"][0]
    assert loan["direction"] == "lent"
    assert loan["person_name"] == "Alice Smith"
    assert loan["amount"] == 5000.0
    assert body["total_lent_by_currency"] == {"INR": 5000.0}
    assert body["total_borrowed_by_currency"] == {}


def test_overview_top_expense_categories(app_client):
    ov = make_overview()
    with patch(
        "app.api.v1.finances.get_finance_overview",
        new=AsyncMock(return_value=ov),
    ):
        resp = app_client.get("/api/v1/finances/overview")
    body = resp.json()
    assert len(body["top_expense_categories"]) == 1
    cat = body["top_expense_categories"][0]
    assert cat["category_slug"] == "food"
    assert cat["percentage"] == 40.0


def test_overview_subscription_burn_rate(app_client):
    ov = make_overview()
    with patch(
        "app.api.v1.finances.get_finance_overview",
        new=AsyncMock(return_value=ov),
    ):
        resp = app_client.get("/api/v1/finances/overview")
    body = resp.json()
    assert body["monthly_subscription_cost_by_currency"] == {"INR": 1299.0}


def test_overview_null_savings_rate(app_client):
    ov = make_overview(
        current_month_income=0.0,
        current_month_net=-12500.0,
        current_month_savings_rate=None,
    )
    with patch(
        "app.api.v1.finances.get_finance_overview",
        new=AsyncMock(return_value=ov),
    ):
        resp = app_client.get("/api/v1/finances/overview")
    assert resp.status_code == 200
    assert resp.json()["current_month_savings_rate"] is None


def test_overview_custom_currency(app_client):
    ov = make_overview(current_month_currency="USD")
    with patch(
        "app.api.v1.finances.get_finance_overview",
        new=AsyncMock(return_value=ov),
    ) as mock_fn:
        resp = app_client.get("/api/v1/finances/overview", params={"currency": "USD"})
    assert resp.status_code == 200
    # currency is passed as positional arg[2]
    assert mock_fn.call_args.args[2] == "USD"


def test_overview_empty_state(app_client):
    ov = make_overview(
        financial_assets=[],
        total_asset_value_by_currency={},
        outstanding_loans=[],
        total_lent_by_currency={},
        top_expense_categories=[],
        monthly_subscription_cost_by_currency={},
        current_month_income=0.0,
        current_month_expenses=0.0,
        current_month_net=0.0,
        current_month_savings_rate=None,
    )
    with patch(
        "app.api.v1.finances.get_finance_overview",
        new=AsyncMock(return_value=ov),
    ):
        resp = app_client.get("/api/v1/finances/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["financial_assets"] == []
    assert body["outstanding_loans"] == []
    assert body["top_expense_categories"] == []
