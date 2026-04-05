import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.inventory import router as inventory_router
from app.api.v1.products import router as products_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.inventory import InventoryProfilePublic
from app.schemas.product import ProductSlim

OWNER_ID = uuid.uuid4()
PRODUCT_ID = uuid.uuid4()
PROFILE_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)

PRODUCT_SLIM = ProductSlim(
    id=PRODUCT_ID,
    name="Amul Milk 1L",
    brand="Amul",
    unit="L",
)


def make_profile(**kwargs) -> InventoryProfilePublic:
    defaults = dict(
        id=PROFILE_ID,
        owner_id=OWNER_ID,
        product=PRODUCT_SLIM,
        is_consumable=True,
        restock_unit="L",
        reorder_threshold=2.0,
        typical_monthly_usage=10.0,
        current_stock=5.0,
        last_restocked_on=date(2026, 4, 1),
        estimated_depletion_date=date(2026, 4, 16),
        preferred_source="BigBasket",
        notes=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return InventoryProfilePublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(products_router, prefix="/api/v1")
    app.include_router(inventory_router, prefix="/api/v1")

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


# ── POST /products/{id}/inventory ─────────────────────────────────────────────


def test_create_inventory_profile_success(app_client):
    profile = make_profile()
    with patch(
        "app.api.v1.products.create_inventory_profile",
        new=AsyncMock(return_value=profile),
    ):
        resp = app_client.post(
            f"/api/v1/products/{PRODUCT_ID}/inventory",
            json={
                "restock_unit": "L",
                "reorder_threshold": 2.0,
                "typical_monthly_usage": 10.0,
                "current_stock": 5.0,
            },
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["restock_unit"] == "L"
    assert body["current_stock"] == 5.0
    assert body["is_low_stock"] is False
    assert body["days_until_depletion"] is not None
    assert body["product"]["name"] == "Amul Milk 1L"


def test_create_inventory_profile_missing_required(app_client):
    resp = app_client.post(
        f"/api/v1/products/{PRODUCT_ID}/inventory",
        json={"restock_unit": "L"},
    )
    assert resp.status_code == 422


def test_create_inventory_profile_product_not_found(app_client):
    from fastapi import HTTPException

    with patch(
        "app.api.v1.products.create_inventory_profile",
        new=AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Product not found")
        ),
    ):
        resp = app_client.post(
            f"/api/v1/products/{uuid.uuid4()}/inventory",
            json={
                "restock_unit": "L",
                "reorder_threshold": 2.0,
                "typical_monthly_usage": 10.0,
                "current_stock": 5.0,
            },
        )
    assert resp.status_code == 404


def test_create_inventory_profile_conflict(app_client):
    from fastapi import HTTPException

    with patch(
        "app.api.v1.products.create_inventory_profile",
        new=AsyncMock(
            side_effect=HTTPException(
                status_code=409,
                detail="Inventory profile already exists",
            )
        ),
    ):
        resp = app_client.post(
            f"/api/v1/products/{PRODUCT_ID}/inventory",
            json={
                "restock_unit": "L",
                "reorder_threshold": 2.0,
                "typical_monthly_usage": 10.0,
                "current_stock": 5.0,
            },
        )
    assert resp.status_code == 409


# ── GET /products/{id}/inventory ──────────────────────────────────────────────


def test_get_inventory_profile_success(app_client):
    profile = make_profile()
    with patch(
        "app.api.v1.products.get_inventory_profile",
        new=AsyncMock(return_value=profile),
    ):
        resp = app_client.get(f"/api/v1/products/{PRODUCT_ID}/inventory")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(PROFILE_ID)


def test_get_inventory_profile_not_found(app_client):
    with patch(
        "app.api.v1.products.get_inventory_profile",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.get(f"/api/v1/products/{uuid.uuid4()}/inventory")
    assert resp.status_code == 404


# ── PATCH /products/{id}/inventory ────────────────────────────────────────────


def test_patch_inventory_profile_success(app_client):
    updated = make_profile(current_stock=1.0)
    with patch(
        "app.api.v1.products.update_inventory_profile",
        new=AsyncMock(return_value=updated),
    ):
        resp = app_client.patch(
            f"/api/v1/products/{PRODUCT_ID}/inventory",
            json={"current_stock": 1.0},
        )
    assert resp.status_code == 200
    assert resp.json()["current_stock"] == 1.0


def test_patch_inventory_profile_not_found(app_client):
    with patch(
        "app.api.v1.products.update_inventory_profile",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.patch(
            f"/api/v1/products/{uuid.uuid4()}/inventory",
            json={"current_stock": 1.0},
        )
    assert resp.status_code == 404


# ── GET /inventory/low-stock ──────────────────────────────────────────────────


def test_get_low_stock_returns_list(app_client):
    low_profile = make_profile(current_stock=1.5, reorder_threshold=2.0)
    with patch(
        "app.api.v1.inventory.list_low_stock",
        new=AsyncMock(return_value=[low_profile]),
    ):
        resp = app_client.get("/api/v1/inventory/low-stock")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["is_low_stock"] is True
    assert body[0]["current_stock"] == 1.5


def test_get_low_stock_empty(app_client):
    with patch(
        "app.api.v1.inventory.list_low_stock",
        new=AsyncMock(return_value=[]),
    ):
        resp = app_client.get("/api/v1/inventory/low-stock")
    assert resp.status_code == 200
    assert resp.json() == []


# ── Computed fields ───────────────────────────────────────────────────────────


def test_is_low_stock_true_when_at_threshold():
    profile = make_profile(current_stock=2.0, reorder_threshold=2.0)
    assert profile.is_low_stock is True


def test_is_low_stock_false_when_above_threshold():
    profile = make_profile(current_stock=3.0, reorder_threshold=2.0)
    assert profile.is_low_stock is False


def test_days_until_depletion_none_when_no_date():
    profile = make_profile(estimated_depletion_date=None)
    assert profile.days_until_depletion is None


def test_days_until_depletion_when_date_set():
    from datetime import timedelta

    future_date = date.today() + timedelta(days=5)
    profile = make_profile(estimated_depletion_date=future_date)
    assert profile.days_until_depletion == 5
