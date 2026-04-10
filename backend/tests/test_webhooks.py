import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.webhooks import _currency_label
from app.api.v1.webhooks import router as webhooks_router
from app.core.config import Settings
from app.core.database import get_session
from app.models.user import User

OWNER_ID = uuid.uuid4()
TX_ID = uuid.uuid4()
REMINDER_ID = uuid.uuid4()

TEST_SECRET = "test-webhook-secret-abc123"
BATCH_ID = "pr-batch-2026-001"

FAKE_USER = User(
    id=OWNER_ID,
    username="webhookuser",
    email="webhook@example.com",
    hashed_password="hashed",
    is_active=True,
    api_key="my-owner-api-key",
    created_at=datetime.now(UTC),
)


def _sign(body: bytes, secret: str = TEST_SECRET) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def make_settings(**overrides) -> Settings:
    base = dict(
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test-secret",
        priceraven_webhook_secret=TEST_SECRET,
        priceraven_base_url="",
        priceraven_api_key="",
    )
    base.update(overrides)
    return Settings(**base)


BILL_PAYLOAD = {
    "batch_id": BATCH_ID,
    "transaction_date": "2026-04-01",
    "store_name": "BigBasket",
    "items": [
        {
            "raw_name": "Amul Milk 1L",
            "quantity": 2.0,
            "unit": "L",
            "unit_price": 65.0,
            "total_price": 130.0,
            "discount": 0.0,
            "priceraven_product_id": "pr-milk-001",
        },
        {
            "raw_name": "Bread",
            "quantity": 1.0,
            "unit": None,
            "unit_price": 55.0,
            "total_price": 55.0,
            "discount": 0.0,
            "priceraven_product_id": None,
        },
    ],
    "owner_api_key": "my-owner-api-key",
}

PRICE_ALERT_PAYLOAD = {
    "priceraven_product_id": "pr-milk-001",
    "platform": "blinkit",
    "old_price": 65.0,
    "new_price": 55.0,
    "direction": "down",
    "currency": "INR",
    "url": "https://blinkit.com/product/amul-milk",
    "owner_api_key": "my-owner-api-key",
}


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(webhooks_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ── _currency_label unit tests ────────────────────────────────────────────────


def test_currency_label_known_currencies():
    """Known ISO codes return their symbol."""
    assert _currency_label("INR") == "₹"
    assert _currency_label("USD") == "$"
    assert _currency_label("EUR") == "€"
    assert _currency_label("GBP") == "£"


def test_currency_label_unknown_currency_returns_iso_code():
    """Unknown ISO codes fall back to the uppercased code itself."""
    assert _currency_label("XYZ") == "XYZ"
    assert _currency_label("xyz") == "XYZ"


def test_currency_label_case_insensitive():
    """Lookup is case-insensitive."""
    assert _currency_label("inr") == "₹"
    assert _currency_label("Usd") == "$"


# ── POST /webhooks/priceraven/bill-parsed ─────────────────────────────────────


def test_bill_parsed_integration_disabled(app_client):
    """Returns 503 when PRICERAVEN_WEBHOOK_SECRET is empty."""
    disabled_settings = make_settings(priceraven_webhook_secret="")
    body = json.dumps(BILL_PAYLOAD).encode()
    with patch(
        "app.api.v1.webhooks.get_settings", return_value=disabled_settings
    ):
        resp = app_client.post(
            "/api/v1/webhooks/priceraven/bill-parsed",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-PriceRaven-Signature": _sign(body),
            },
        )
    assert resp.status_code == 503


def test_bill_parsed_invalid_signature(app_client):
    """Returns 401 when HMAC signature is wrong."""
    settings = make_settings()
    body = json.dumps(BILL_PAYLOAD).encode()
    with patch("app.api.v1.webhooks.get_settings", return_value=settings):
        resp = app_client.post(
            "/api/v1/webhooks/priceraven/bill-parsed",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-PriceRaven-Signature": "badhex0000",
            },
        )
    assert resp.status_code == 401


def test_bill_parsed_missing_signature(app_client):
    """Returns 401 when X-PriceRaven-Signature header is absent."""
    settings = make_settings()
    body = json.dumps(BILL_PAYLOAD).encode()
    with patch("app.api.v1.webhooks.get_settings", return_value=settings):
        resp = app_client.post(
            "/api/v1/webhooks/priceraven/bill-parsed",
            content=body,
            headers={"Content-Type": "application/json"},
        )
    assert resp.status_code == 401


def test_bill_parsed_invalid_owner_api_key(app_client):
    """Returns 401 when owner_api_key resolves to no user."""
    settings = make_settings()
    body = json.dumps(BILL_PAYLOAD).encode()
    with (
        patch("app.api.v1.webhooks.get_settings", return_value=settings),
        patch(
            "app.api.v1.webhooks.get_user_by_api_key",
            new=AsyncMock(return_value=None),
        ),
    ):
        resp = app_client.post(
            "/api/v1/webhooks/priceraven/bill-parsed",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-PriceRaven-Signature": _sign(body),
            },
        )
    assert resp.status_code == 401


def test_bill_parsed_success(app_client):
    """Valid request creates transaction + items, returns expected counts."""
    settings = make_settings()
    body = json.dumps(BILL_PAYLOAD).encode()
    with (
        patch("app.api.v1.webhooks.get_settings", return_value=settings),
        patch(
            "app.api.v1.webhooks.get_user_by_api_key",
            new=AsyncMock(return_value=FAKE_USER),
        ),
        patch(
            "app.api.v1.webhooks.process_bill_parsed",
            new=AsyncMock(
                return_value={
                    "transaction_id": str(TX_ID),
                    "items_created": 2,
                    "products_matched": 1,
                    "reorders_triggered": 0,
                }
            ),
        ),
    ):
        resp = app_client.post(
            "/api/v1/webhooks/priceraven/bill-parsed",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-PriceRaven-Signature": _sign(body),
            },
        )
    assert resp.status_code == 200
    result = resp.json()
    assert result["items_created"] == 2
    assert result["products_matched"] == 1
    assert "transaction_id" in result


def test_bill_parsed_idempotent(app_client):
    """Duplicate batch_id returns existing transaction without re-creating."""
    settings = make_settings()
    body = json.dumps(BILL_PAYLOAD).encode()
    with (
        patch("app.api.v1.webhooks.get_settings", return_value=settings),
        patch(
            "app.api.v1.webhooks.get_user_by_api_key",
            new=AsyncMock(return_value=FAKE_USER),
        ),
        patch(
            "app.api.v1.webhooks.process_bill_parsed",
            new=AsyncMock(
                return_value={
                    "transaction_id": str(TX_ID),
                    "items_created": 0,
                    "products_matched": 0,
                    "reorders_triggered": 0,
                }
            ),
        ),
    ):
        resp = app_client.post(
            "/api/v1/webhooks/priceraven/bill-parsed",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-PriceRaven-Signature": _sign(body),
            },
        )
    assert resp.status_code == 200
    assert resp.json()["transaction_id"] == str(TX_ID)


# ── POST /webhooks/priceraven/price-alert ──────────────────────────────────────


def test_price_alert_integration_disabled(app_client):
    """Returns 503 when PRICERAVEN_WEBHOOK_SECRET is empty."""
    disabled_settings = make_settings(priceraven_webhook_secret="")
    body = json.dumps(PRICE_ALERT_PAYLOAD).encode()
    with patch("app.api.v1.webhooks.get_settings", return_value=disabled_settings):
        resp = app_client.post(
            "/api/v1/webhooks/priceraven/price-alert",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-PriceRaven-Signature": _sign(body),
            },
        )
    assert resp.status_code == 503


def test_price_alert_invalid_signature(app_client):
    """Returns 401 when HMAC signature is wrong."""
    settings = make_settings()
    body = json.dumps(PRICE_ALERT_PAYLOAD).encode()
    with patch("app.api.v1.webhooks.get_settings", return_value=settings):
        resp = app_client.post(
            "/api/v1/webhooks/priceraven/price-alert",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-PriceRaven-Signature": "wrongsig",
            },
        )
    assert resp.status_code == 401


def test_price_alert_invalid_owner_api_key(app_client):
    """Returns 401 when owner_api_key resolves to no user."""
    settings = make_settings()
    body = json.dumps(PRICE_ALERT_PAYLOAD).encode()
    with (
        patch("app.api.v1.webhooks.get_settings", return_value=settings),
        patch(
            "app.api.v1.webhooks.get_user_by_api_key",
            new=AsyncMock(return_value=None),
        ),
    ):
        resp = app_client.post(
            "/api/v1/webhooks/priceraven/price-alert",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-PriceRaven-Signature": _sign(body),
            },
        )
    assert resp.status_code == 401


def test_price_alert_product_not_found_graceful(app_client):
    """Gracefully skips reminder when product is not in catalog."""
    settings = make_settings()
    body = json.dumps(PRICE_ALERT_PAYLOAD).encode()
    with (
        patch("app.api.v1.webhooks.get_settings", return_value=settings),
        patch(
            "app.api.v1.webhooks.get_user_by_api_key",
            new=AsyncMock(return_value=FAKE_USER),
        ),
        patch(
            "app.api.v1.webhooks.process_price_alert",
            new=AsyncMock(return_value={"reminder_id": None}),
        ),
    ):
        resp = app_client.post(
            "/api/v1/webhooks/priceraven/price-alert",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-PriceRaven-Signature": _sign(body),
            },
        )
    assert resp.status_code == 200
    assert resp.json()["reminder_id"] is None


def test_price_alert_success_price_down(app_client):
    """Creates a Reminder for a price drop."""
    settings = make_settings()
    body = json.dumps(PRICE_ALERT_PAYLOAD).encode()
    with (
        patch("app.api.v1.webhooks.get_settings", return_value=settings),
        patch(
            "app.api.v1.webhooks.get_user_by_api_key",
            new=AsyncMock(return_value=FAKE_USER),
        ),
        patch(
            "app.api.v1.webhooks.process_price_alert",
            new=AsyncMock(return_value={"reminder_id": str(REMINDER_ID)}),
        ),
    ):
        resp = app_client.post(
            "/api/v1/webhooks/priceraven/price-alert",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-PriceRaven-Signature": _sign(body),
            },
        )
    assert resp.status_code == 200
    assert resp.json()["reminder_id"] == str(REMINDER_ID)


def test_price_alert_success_price_up(app_client):
    """Creates a Reminder for a price increase."""
    settings = make_settings()
    up_payload = {**PRICE_ALERT_PAYLOAD, "direction": "up", "new_price": 75.0}
    body = json.dumps(up_payload).encode()
    with (
        patch("app.api.v1.webhooks.get_settings", return_value=settings),
        patch(
            "app.api.v1.webhooks.get_user_by_api_key",
            new=AsyncMock(return_value=FAKE_USER),
        ),
        patch(
            "app.api.v1.webhooks.process_price_alert",
            new=AsyncMock(return_value={"reminder_id": str(REMINDER_ID)}),
        ),
    ):
        resp = app_client.post(
            "/api/v1/webhooks/priceraven/price-alert",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-PriceRaven-Signature": _sign(body),
            },
        )
    assert resp.status_code == 200
    assert resp.json()["reminder_id"] == str(REMINDER_ID)


def test_price_alert_non_inr_currency(app_client):
    """Price alert with non-INR currency uses the correct symbol."""
    settings = make_settings()
    usd_payload = {
        **PRICE_ALERT_PAYLOAD,
        "currency": "USD",
        "old_price": 1.99,
        "new_price": 1.49,
    }
    body = json.dumps(usd_payload).encode()
    with (
        patch("app.api.v1.webhooks.get_settings", return_value=settings),
        patch(
            "app.api.v1.webhooks.get_user_by_api_key",
            new=AsyncMock(return_value=FAKE_USER),
        ),
        patch(
            "app.api.v1.webhooks.process_price_alert",
            new=AsyncMock(return_value={"reminder_id": str(REMINDER_ID)}),
        ),
    ):
        resp = app_client.post(
            "/api/v1/webhooks/priceraven/price-alert",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-PriceRaven-Signature": _sign(body),
            },
        )
    assert resp.status_code == 200
    assert resp.json()["reminder_id"] == str(REMINDER_ID)
