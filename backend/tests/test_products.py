import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.products import router as products_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.product import ProductPublic
from app.schemas.vocabulary import TermSlim

OWNER_ID = uuid.uuid4()
PRODUCT_ID = uuid.uuid4()
CAT_TERM_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)

DAIRY_TERM = TermSlim(id=CAT_TERM_ID, name="Dairy", slug="dairy")


def make_product(**kwargs) -> ProductPublic:
    defaults = dict(
        id=PRODUCT_ID,
        owner_id=OWNER_ID,
        name="Amul Milk 1L",
        brand="Amul",
        category=DAIRY_TERM,
        unit="L",
        barcode="8901030890512",
        priceraven_product_id=None,
        notes=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return ProductPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(products_router, prefix="/api/v1")

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


# ── POST /products/ ────────────────────────────────────────────────────────────


def test_create_product_success(app_client):
    product = make_product()
    with patch(
        "app.api.v1.products.create_product",
        new=AsyncMock(return_value=(product, True)),
    ):
        resp = app_client.post(
            "/api/v1/products/",
            json={"name": "Amul Milk 1L", "brand": "Amul", "unit": "L"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Amul Milk 1L"
    assert body["brand"] == "Amul"
    assert body["owner_id"] == str(OWNER_ID)


def test_create_product_returns_200_on_duplicate(app_client):
    """When create_product returns an existing product, endpoint returns 200."""
    product = make_product()
    with patch(
        "app.api.v1.products.create_product",
        new=AsyncMock(return_value=(product, False)),
    ):
        resp = app_client.post(
            "/api/v1/products/",
            json={"name": "Amul Milk 1L", "brand": "Amul"},
        )
    # CRUD signals duplicate via (product, is_new=False) tuple
    assert resp.status_code == 200
    assert resp.json()["name"] == "Amul Milk 1L"


def test_create_product_missing_name(app_client):
    resp = app_client.post(
        "/api/v1/products/",
        json={"brand": "Amul"},
    )
    assert resp.status_code == 422


def test_create_product_minimal(app_client):
    product = make_product(brand=None, category=None, unit=None, barcode=None)
    with patch(
        "app.api.v1.products.create_product",
        new=AsyncMock(return_value=(product, True)),
    ):
        resp = app_client.post("/api/v1/products/", json={"name": "Generic Item"})
    assert resp.status_code == 201


# ── GET /products/ ─────────────────────────────────────────────────────────────


def test_list_products(app_client):
    product = make_product()
    with patch(
        "app.api.v1.products.list_products",
        new=AsyncMock(return_value=([product], 1)),
    ):
        resp = app_client.get("/api/v1/products/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["name"] == "Amul Milk 1L"


def test_list_products_with_filters(app_client):
    product = make_product()
    with patch(
        "app.api.v1.products.list_products",
        new=AsyncMock(return_value=([product], 1)),
    ) as mock_list:
        resp = app_client.get(
            "/api/v1/products/",
            params={"category": "dairy", "search": "amul"},
        )
    assert resp.status_code == 200
    _, call_kwargs = mock_list.call_args
    assert call_kwargs["category_slug"] == "dairy"
    assert call_kwargs["search"] == "amul"


def test_list_products_empty(app_client):
    with patch(
        "app.api.v1.products.list_products",
        new=AsyncMock(return_value=([], 0)),
    ):
        resp = app_client.get("/api/v1/products/")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
    assert resp.json()["items"] == []


# ── GET /products/{id} ─────────────────────────────────────────────────────────


def test_get_product_success(app_client):
    product = make_product()
    with patch(
        "app.api.v1.products.get_product_public",
        new=AsyncMock(return_value=product),
    ):
        resp = app_client.get(f"/api/v1/products/{PRODUCT_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(PRODUCT_ID)


def test_get_product_not_found(app_client):
    with patch(
        "app.api.v1.products.get_product_public",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.get(f"/api/v1/products/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /products/{id} ───────────────────────────────────────────────────────


def test_patch_product_success(app_client):
    updated = make_product(brand="Mother Dairy")
    with patch(
        "app.api.v1.products.update_product",
        new=AsyncMock(return_value=updated),
    ):
        resp = app_client.patch(
            f"/api/v1/products/{PRODUCT_ID}", json={"brand": "Mother Dairy"}
        )
    assert resp.status_code == 200
    assert resp.json()["brand"] == "Mother Dairy"


def test_patch_product_not_found(app_client):
    with patch(
        "app.api.v1.products.update_product",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.patch(f"/api/v1/products/{uuid.uuid4()}", json={"brand": "X"})
    assert resp.status_code == 404


# ── DELETE /products/{id} ──────────────────────────────────────────────────────


def test_delete_product_success(app_client):
    with patch(
        "app.api.v1.products.soft_delete_product",
        new=AsyncMock(return_value=True),
    ):
        resp = app_client.delete(f"/api/v1/products/{PRODUCT_ID}")
    assert resp.status_code == 204


def test_delete_product_not_found(app_client):
    with patch(
        "app.api.v1.products.soft_delete_product",
        new=AsyncMock(return_value=False),
    ):
        resp = app_client.delete(f"/api/v1/products/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_delete_product_conflict(app_client):
    from fastapi import HTTPException

    with patch(
        "app.api.v1.products.soft_delete_product",
        new=AsyncMock(side_effect=HTTPException(status_code=409, detail="In use")),
    ):
        resp = app_client.delete(f"/api/v1/products/{PRODUCT_ID}")
    assert resp.status_code == 409


# ── GET /products/{id}/items ───────────────────────────────────────────────────


def test_get_product_items_returns_paginated(app_client):
    with patch(
        "app.api.v1.products.get_product_public",
        new=AsyncMock(return_value=make_product()),
    ):
        resp = app_client.get(f"/api/v1/products/{PRODUCT_ID}/items")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert body["items"] == []
    assert body["total"] == 0


def test_get_product_items_product_not_found(app_client):
    with patch(
        "app.api.v1.products.get_product_public",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.get(f"/api/v1/products/{uuid.uuid4()}/items")
    assert resp.status_code == 404
