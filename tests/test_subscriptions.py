import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.subscriptions import router as subscriptions_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.subscription import (
    BillPaymentPublicRead,
    CategorySpend,
    SubscriptionPublicRead,
    SubscriptionSummary,
    UpcomingRenewal,
)
from app.schemas.vocabulary import TermSlim

OWNER_ID = uuid.uuid4()
SUB_ID = uuid.uuid4()
PAYMENT_ID = uuid.uuid4()
CAT_TERM_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.utcnow(),
)

STREAMING_TERM = TermSlim(id=CAT_TERM_ID, name="Streaming", slug="streaming")


def make_subscription(**kwargs) -> SubscriptionPublicRead:
    defaults = dict(
        id=SUB_ID,
        owner_id=OWNER_ID,
        name="Netflix",
        provider="Netflix Inc.",
        category=STREAMING_TERM,
        status="active",
        cost=649.0,
        currency="INR",
        payment_mode="auto_debit",
        billing_cycle="monthly",
        billing_cycle_days=None,
        started_on=date(2023, 1, 1),
        next_billing_date=date(2026, 4, 1),
        trial_ends_on=None,
        cancelled_on=None,
        auto_renews=True,
        url="https://netflix.com",
        notes=None,
        asset_id=None,
        tags=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return SubscriptionPublicRead(**defaults)


def make_payment(**kwargs) -> BillPaymentPublicRead:
    defaults = dict(
        id=PAYMENT_ID,
        subscription_id=SUB_ID,
        owner_id=OWNER_ID,
        amount=649.0,
        currency="INR",
        paid_amount=649.0,
        paid_currency="INR",
        exchange_rate=None,
        payment_mode="auto_debit",
        billing_date=date(2026, 3, 1),
        due_date=None,
        paid_on=date(2026, 3, 1),
        status="paid",
        notes=None,
        created_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return BillPaymentPublicRead(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(subscriptions_router, prefix="/api/v1")

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


# ── POST /subscriptions/ ───────────────────────────────────────────────────────


def test_create_subscription_success(app_client):
    sub = make_subscription()
    with patch(
        "app.api.v1.subscriptions.create_subscription",
        new=AsyncMock(return_value=sub),
    ):
        resp = app_client.post(
            "/api/v1/subscriptions/",
            json={"name": "Netflix", "cost": 649.0},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Netflix"
    assert body["cost"] == 649.0
    assert body["owner_id"] == str(OWNER_ID)


def test_create_subscription_missing_required_field(app_client):
    # Missing required `cost`
    resp = app_client.post("/api/v1/subscriptions/", json={"name": "Netflix"})
    assert resp.status_code == 422


def test_create_subscription_with_all_fields(app_client):
    sub = make_subscription(
        provider="Netflix Inc.",
        billing_cycle="annual",
        started_on=date(2023, 1, 1),
        next_billing_date=date(2026, 1, 1),
        url="https://netflix.com",
        notes="Family plan",
    )
    with patch(
        "app.api.v1.subscriptions.create_subscription",
        new=AsyncMock(return_value=sub),
    ):
        resp = app_client.post(
            "/api/v1/subscriptions/",
            json={
                "name": "Netflix",
                "cost": 649.0,
                "provider": "Netflix Inc.",
                "billing_cycle": "annual",
                "started_on": "2023-01-01",
                "next_billing_date": "2026-01-01",
                "url": "https://netflix.com",
                "notes": "Family plan",
            },
        )
    assert resp.status_code == 201
    assert resp.json()["billing_cycle"] == "annual"


# ── GET /subscriptions/summary ─────────────────────────────────────────────────


def test_get_subscription_summary(app_client):
    summary = SubscriptionSummary(
        total_active=3,
        monthly_cost_by_currency={"INR": 1299.0, "USD": 15.99},
        upcoming_renewals=[
            UpcomingRenewal(
                id=SUB_ID,
                name="Netflix",
                cost=649.0,
                currency="INR",
                next_billing_date=date(2026, 4, 1),
            )
        ],
        cost_by_category=[
            CategorySpend(category="Streaming", monthly_cost=649.0)
        ],
    )
    with patch(
        "app.api.v1.subscriptions.get_summary",
        new=AsyncMock(return_value=summary),
    ):
        resp = app_client.get("/api/v1/subscriptions/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_active"] == 3
    assert body["monthly_cost_by_currency"]["INR"] == 1299.0
    assert len(body["upcoming_renewals"]) == 1
    assert len(body["cost_by_category"]) == 1


# ── GET /subscriptions/ ────────────────────────────────────────────────────────


def test_list_subscriptions_returns_list(app_client):
    subs = [make_subscription(), make_subscription(id=uuid.uuid4(), name="Spotify")]
    with patch(
        "app.api.v1.subscriptions.list_subscriptions",
        new=AsyncMock(return_value=subs),
    ):
        resp = app_client.get("/api/v1/subscriptions/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_subscriptions_empty(app_client):
    with patch(
        "app.api.v1.subscriptions.list_subscriptions",
        new=AsyncMock(return_value=[]),
    ):
        resp = app_client.get("/api/v1/subscriptions/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_subscriptions_filters(app_client):
    with patch(
        "app.api.v1.subscriptions.list_subscriptions",
        new=AsyncMock(return_value=[]),
    ) as mock_list:
        resp = app_client.get(
            "/api/v1/subscriptions/?status=active&category=streaming&billing_cycle=monthly"
        )
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["status"] == "active"
    assert call_kwargs["category"] == "streaming"
    assert call_kwargs["billing_cycle"] == "monthly"


# ── GET /subscriptions/{subscription_id} ───────────────────────────────────────


def test_get_subscription_found(app_client):
    sub = make_subscription()
    with patch(
        "app.api.v1.subscriptions.get_subscription_public",
        new=AsyncMock(return_value=sub),
    ):
        resp = app_client.get(f"/api/v1/subscriptions/{SUB_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(SUB_ID)


def test_get_subscription_not_found(app_client):
    with patch(
        "app.api.v1.subscriptions.get_subscription_public",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.get(f"/api/v1/subscriptions/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /subscriptions/{subscription_id} ─────────────────────────────────────


def test_patch_subscription_success(app_client):
    updated = make_subscription(name="Netflix Premium", cost=799.0)
    with patch(
        "app.api.v1.subscriptions.update_subscription",
        new=AsyncMock(return_value=updated),
    ):
        resp = app_client.patch(
            f"/api/v1/subscriptions/{SUB_ID}",
            json={"name": "Netflix Premium", "cost": 799.0},
        )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Netflix Premium"
    assert resp.json()["cost"] == 799.0


def test_patch_subscription_not_found(app_client):
    with patch(
        "app.api.v1.subscriptions.update_subscription",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.patch(
            f"/api/v1/subscriptions/{uuid.uuid4()}", json={"name": "Ghost"}
        )
    assert resp.status_code == 404


# ── DELETE /subscriptions/{subscription_id} ────────────────────────────────────


def test_delete_subscription_success(app_client):
    with patch(
        "app.api.v1.subscriptions.soft_delete_subscription",
        new=AsyncMock(return_value=object()),
    ):
        resp = app_client.delete(f"/api/v1/subscriptions/{SUB_ID}")
    assert resp.status_code == 204


def test_delete_subscription_not_found(app_client):
    with patch(
        "app.api.v1.subscriptions.soft_delete_subscription",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.delete(f"/api/v1/subscriptions/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── POST /subscriptions/{subscription_id}/payments ─────────────────────────────


def test_log_payment_success(app_client):
    sub = make_subscription()
    payment = make_payment()
    with (
        patch(
            "app.api.v1.subscriptions.get_subscription_public",
            new=AsyncMock(return_value=sub),
        ),
        patch(
            "app.api.v1.subscriptions.create_payment",
            new=AsyncMock(return_value=payment),
        ),
    ):
        resp = app_client.post(
            f"/api/v1/subscriptions/{SUB_ID}/payments",
            json={"amount": 649.0, "billing_date": "2026-03-01"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["amount"] == 649.0
    assert body["subscription_id"] == str(SUB_ID)


def test_log_payment_subscription_not_found(app_client):
    with patch(
        "app.api.v1.subscriptions.get_subscription_public",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.post(
            f"/api/v1/subscriptions/{uuid.uuid4()}/payments",
            json={"amount": 649.0, "billing_date": "2026-03-01"},
        )
    assert resp.status_code == 404


def test_log_payment_missing_required_fields(app_client):
    sub = make_subscription()
    with patch(
        "app.api.v1.subscriptions.get_subscription_public",
        new=AsyncMock(return_value=sub),
    ):
        # Missing billing_date
        resp = app_client.post(
            f"/api/v1/subscriptions/{SUB_ID}/payments",
            json={"amount": 649.0},
        )
    assert resp.status_code == 422


# ── GET /subscriptions/{subscription_id}/payments ──────────────────────────────


def test_list_payments_success(app_client):
    sub = make_subscription()
    payments = [
        make_payment(),
        make_payment(id=uuid.uuid4(), billing_date=date(2026, 2, 1)),
    ]
    with (
        patch(
            "app.api.v1.subscriptions.get_subscription_public",
            new=AsyncMock(return_value=sub),
        ),
        patch(
            "app.api.v1.subscriptions.list_payments",
            new=AsyncMock(return_value=payments),
        ),
    ):
        resp = app_client.get(f"/api/v1/subscriptions/{SUB_ID}/payments")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_payments_empty(app_client):
    sub = make_subscription()
    with (
        patch(
            "app.api.v1.subscriptions.get_subscription_public",
            new=AsyncMock(return_value=sub),
        ),
        patch(
            "app.api.v1.subscriptions.list_payments",
            new=AsyncMock(return_value=[]),
        ),
    ):
        resp = app_client.get(f"/api/v1/subscriptions/{SUB_ID}/payments")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_payments_subscription_not_found(app_client):
    with patch(
        "app.api.v1.subscriptions.get_subscription_public",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.get(f"/api/v1/subscriptions/{uuid.uuid4()}/payments")
    assert resp.status_code == 404


# ── PATCH /subscriptions/{subscription_id}/payments/{payment_id} ──────────────


def test_patch_payment_success(app_client):
    updated = make_payment(status="paid", paid_on=date(2026, 3, 2))
    with patch(
        "app.api.v1.subscriptions.update_payment",
        new=AsyncMock(return_value=updated),
    ):
        resp = app_client.patch(
            f"/api/v1/subscriptions/{SUB_ID}/payments/{PAYMENT_ID}",
            json={"status": "paid", "paid_on": "2026-03-02"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "paid"


def test_patch_payment_not_found(app_client):
    with patch(
        "app.api.v1.subscriptions.update_payment",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.patch(
            f"/api/v1/subscriptions/{SUB_ID}/payments/{uuid.uuid4()}",
            json={"status": "paid"},
        )
    assert resp.status_code == 404


# ── DELETE /subscriptions/{subscription_id}/payments/{payment_id} ─────────────


def test_delete_payment_success(app_client):
    with patch(
        "app.api.v1.subscriptions.delete_payment",
        new=AsyncMock(return_value=True),
    ):
        resp = app_client.delete(
            f"/api/v1/subscriptions/{SUB_ID}/payments/{PAYMENT_ID}"
        )
    assert resp.status_code == 204


def test_delete_payment_not_found(app_client):
    with patch(
        "app.api.v1.subscriptions.delete_payment",
        new=AsyncMock(return_value=False),
    ):
        resp = app_client.delete(
            f"/api/v1/subscriptions/{SUB_ID}/payments/{uuid.uuid4()}"
        )
    assert resp.status_code == 404
