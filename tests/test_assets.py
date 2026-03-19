import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.assets import router as assets_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.asset import AssetPublicRead
from app.schemas.vocabulary import TermSlim

OWNER_ID = uuid.uuid4()
ASSET_ID = uuid.uuid4()
CAT_TERM_ID = uuid.uuid4()
STATUS_TERM_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.utcnow(),
)

HARDWARE_TERM = TermSlim(id=CAT_TERM_ID, name="Hardware", slug="hardware")
ACTIVE_TERM = TermSlim(id=STATUS_TERM_ID, name="Active", slug="active")
SOLD_TERM = TermSlim(id=uuid.uuid4(), name="Sold", slug="sold")


def make_asset_public(**kwargs) -> AssetPublicRead:
    defaults = dict(
        id=ASSET_ID,
        owner_id=OWNER_ID,
        name="MacBook Pro",
        category=HARDWARE_TERM,
        status=ACTIVE_TERM,
        description=None,
        serial_number=None,
        vendor=None,
        purchase_date=None,
        purchase_price=None,
        current_value=None,
        tags=[],
        notes=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return AssetPublicRead(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(assets_router, prefix="/api/v1")

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


@pytest.fixture
def unauthed_client():
    app = FastAPI()
    app.include_router(assets_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


# ── POST /assets/ ─────────────────────────────────────────────────────────────


def test_create_asset_success(app_client):
    asset = make_asset_public()
    with patch("app.api.v1.assets.create_asset", new=AsyncMock(return_value=asset)):
        resp = app_client.post(
            "/api/v1/assets/",
            json={"name": "MacBook Pro", "category": "hardware"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "MacBook Pro"
    assert body["category"]["slug"] == "hardware"
    assert body["status"]["slug"] == "active"


def test_create_asset_missing_required_fields(app_client):
    resp = app_client.post("/api/v1/assets/", json={"name": "No Category"})
    assert resp.status_code == 422


def test_create_asset_unauthenticated(unauthed_client):
    resp = unauthed_client.post(
        "/api/v1/assets/",
        json={"name": "MacBook Pro", "category": "hardware"},
    )
    assert resp.status_code in (401, 422, 500)


# ── GET /assets/ ──────────────────────────────────────────────────────────────


def test_list_assets_returns_list(app_client):
    assets = [make_asset_public(), make_asset_public(id=uuid.uuid4(), name="Hammer")]
    with patch("app.api.v1.assets.list_assets", new=AsyncMock(return_value=assets)):
        resp = app_client.get("/api/v1/assets/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_assets_empty(app_client):
    with patch("app.api.v1.assets.list_assets", new=AsyncMock(return_value=[])):
        resp = app_client.get("/api/v1/assets/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_assets_category_filter(app_client):
    with patch(
        "app.api.v1.assets.list_assets", new=AsyncMock(return_value=[])
    ) as mock_list:
        resp = app_client.get("/api/v1/assets/?category=hardware")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["category"] == "hardware"


# ── GET /assets/{asset_id} ────────────────────────────────────────────────────


def test_get_asset_found(app_client):
    asset = make_asset_public()
    with patch("app.api.v1.assets.get_asset_public", new=AsyncMock(return_value=asset)):
        resp = app_client.get(f"/api/v1/assets/{ASSET_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(ASSET_ID)


def test_get_asset_not_found(app_client):
    with patch("app.api.v1.assets.get_asset_public", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"/api/v1/assets/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_get_asset_wrong_owner(app_client):
    # CRUD returns None when owner doesn't match — router raises 404
    with patch("app.api.v1.assets.get_asset_public", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"/api/v1/assets/{ASSET_ID}")
    assert resp.status_code == 404


# ── PATCH /assets/{asset_id} ──────────────────────────────────────────────────


def test_patch_asset_success(app_client):
    updated = make_asset_public(name="MacBook Air", status=SOLD_TERM)
    with patch("app.api.v1.assets.update_asset", new=AsyncMock(return_value=updated)):
        resp = app_client.patch(
            f"/api/v1/assets/{ASSET_ID}",
            json={"name": "MacBook Air", "status": "sold"},
        )
    assert resp.status_code == 200
    assert resp.json()["name"] == "MacBook Air"
    assert resp.json()["status"]["slug"] == "sold"


def test_patch_asset_not_found(app_client):
    with patch("app.api.v1.assets.update_asset", new=AsyncMock(return_value=None)):
        resp = app_client.patch(
            f"/api/v1/assets/{uuid.uuid4()}", json={"name": "Ghost"}
        )
    assert resp.status_code == 404


def test_patch_asset_partial_update(app_client):
    # Only updating vendor — other fields stay unchanged
    updated = make_asset_public(vendor="Apple")
    with patch(
        "app.api.v1.assets.update_asset", new=AsyncMock(return_value=updated)
    ) as mock_update:
        resp = app_client.patch(f"/api/v1/assets/{ASSET_ID}", json={"vendor": "Apple"})
    assert resp.status_code == 200
    update_data = mock_update.call_args.args[3]  # AssetUpdate positional arg
    assert update_data.vendor == "Apple"
    assert update_data.name is None  # not sent — should be unset


# ── DELETE /assets/{asset_id} ─────────────────────────────────────────────────


def test_delete_asset_success(app_client):
    # soft_delete_asset returns raw Asset; router just checks for None
    with patch(
        "app.api.v1.assets.soft_delete_asset", new=AsyncMock(return_value=object())
    ):
        resp = app_client.delete(f"/api/v1/assets/{ASSET_ID}")
    assert resp.status_code == 204


def test_delete_asset_not_found(app_client):
    with patch("app.api.v1.assets.soft_delete_asset", new=AsyncMock(return_value=None)):
        resp = app_client.delete(f"/api/v1/assets/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_delete_then_get_returns_404(app_client):
    # After soft delete, get_asset_public returns None (deleted_at IS NOT NULL filtered)
    with patch(
        "app.api.v1.assets.soft_delete_asset",
        new=AsyncMock(return_value=object()),
    ):
        del_resp = app_client.delete(f"/api/v1/assets/{ASSET_ID}")
    assert del_resp.status_code == 204

    with patch("app.api.v1.assets.get_asset_public", new=AsyncMock(return_value=None)):
        get_resp = app_client.get(f"/api/v1/assets/{ASSET_ID}")
    assert get_resp.status_code == 404


# ── Additional field coverage ─────────────────────────────────────────────────


def test_create_asset_with_all_fields(app_client):
    work_tag = TermSlim(id=uuid.uuid4(), name="Work", slug="work")
    laptop_tag = TermSlim(id=uuid.uuid4(), name="Laptop", slug="laptop")
    asset = make_asset_public(
        vendor="Apple",
        serial_number="C02XG0JHJGH5",
        purchase_date=date(2023, 6, 15),
        purchase_price=2499.0,
        current_value=1800.0,
        tags=[work_tag, laptop_tag],
        notes="Company issued",
    )
    with patch("app.api.v1.assets.create_asset", new=AsyncMock(return_value=asset)):
        resp = app_client.post(
            "/api/v1/assets/",
            json={
                "name": "MacBook Pro",
                "category": "hardware",
                "vendor": "Apple",
                "serial_number": "C02XG0JHJGH5",
                "purchase_date": "2023-06-15",
                "purchase_price": 2499.0,
                "current_value": 1800.0,
                "tags": ["work", "laptop"],
                "notes": "Company issued",
            },
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["vendor"] == "Apple"
    assert len(body["tags"]) == 2
    assert body["tags"][0]["slug"] == "work"
    assert body["purchase_price"] == 2499.0
