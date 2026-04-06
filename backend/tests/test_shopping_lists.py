import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.shopping_lists import router as shopping_lists_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.product import ProductSlim
from app.schemas.shopping_list import (
    ShoppingListItemPublic,
    ShoppingListPublic,
)

OWNER_ID = uuid.uuid4()
LIST_ID = uuid.uuid4()
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

PRODUCT_SLIM = ProductSlim(id=PRODUCT_ID, name="Amul Milk 1L", brand="Amul", unit="L")


def make_item(**kwargs) -> ShoppingListItemPublic:
    defaults = dict(
        id=ITEM_ID,
        shopping_list_id=LIST_ID,
        product_id=PRODUCT_ID,
        product=PRODUCT_SLIM,
        raw_name="Amul Milk 1L",
        quantity=2.0,
        unit="L",
        estimated_price=65.0,
        actual_price=None,
        is_checked=False,
        source="manual",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return ShoppingListItemPublic(**defaults)


def make_list(**kwargs) -> ShoppingListPublic:
    defaults = dict(
        id=LIST_ID,
        owner_id=OWNER_ID,
        name="Weekly Groceries",
        store_name="DMart",
        planned_date=date(2026, 4, 10),
        is_completed=False,
        completed_on=None,
        is_active=True,
        notes=None,
        items=[],
        item_count=0,
        checked_count=0,
        estimated_total=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return ShoppingListPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(shopping_lists_router, prefix="/api/v1")

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


# ── POST /shopping-lists/ ─────────────────────────────────────────────────────


def test_create_shopping_list_success(app_client):
    sl = make_list()
    with patch(
        "app.api.v1.shopping_lists.create_shopping_list",
        new=AsyncMock(return_value=sl),
    ):
        resp = app_client.post(
            "/api/v1/shopping-lists/",
            json={"name": "Weekly Groceries", "store_name": "DMart"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Weekly Groceries"
    assert body["store_name"] == "DMart"
    assert body["is_completed"] is False


def test_create_shopping_list_missing_name(app_client):
    resp = app_client.post("/api/v1/shopping-lists/", json={})
    assert resp.status_code == 422


# ── GET /shopping-lists/ ──────────────────────────────────────────────────────


def test_list_shopping_lists_active_only(app_client):
    sl = make_list()
    with patch(
        "app.api.v1.shopping_lists.list_shopping_lists",
        new=AsyncMock(return_value=[sl]),
    ):
        resp = app_client.get("/api/v1/shopping-lists/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_shopping_lists_include_completed(app_client):
    sl_active = make_list()
    sl_done = make_list(
        id=uuid.uuid4(),
        is_completed=True,
        completed_on=date(2026, 4, 1),
        is_active=False,
    )
    with patch(
        "app.api.v1.shopping_lists.list_shopping_lists",
        new=AsyncMock(return_value=[sl_active, sl_done]),
    ):
        resp = app_client.get("/api/v1/shopping-lists/?include_completed=true")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# ── GET /shopping-lists/active ────────────────────────────────────────────────


def test_get_active_lists(app_client):
    sl = make_list()
    with patch(
        "app.api.v1.shopping_lists.list_shopping_lists",
        new=AsyncMock(return_value=[sl]),
    ):
        resp = app_client.get("/api/v1/shopping-lists/active")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["is_completed"] is False


# ── GET /shopping-lists/{id} ──────────────────────────────────────────────────


def test_get_shopping_list_success(app_client):
    sl = make_list()
    with patch(
        "app.api.v1.shopping_lists.get_shopping_list",
        new=AsyncMock(return_value=sl),
    ):
        resp = app_client.get(f"/api/v1/shopping-lists/{LIST_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(LIST_ID)


def test_get_shopping_list_not_found(app_client):
    with patch(
        "app.api.v1.shopping_lists.get_shopping_list",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.get(f"/api/v1/shopping-lists/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /shopping-lists/{id} ────────────────────────────────────────────────


def test_patch_shopping_list_success(app_client):
    updated = make_list(name="Monthly Groceries")
    with patch(
        "app.api.v1.shopping_lists.update_shopping_list",
        new=AsyncMock(return_value=updated),
    ):
        resp = app_client.patch(
            f"/api/v1/shopping-lists/{LIST_ID}",
            json={"name": "Monthly Groceries"},
        )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Monthly Groceries"


def test_patch_shopping_list_not_found(app_client):
    with patch(
        "app.api.v1.shopping_lists.update_shopping_list",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.patch(
            f"/api/v1/shopping-lists/{uuid.uuid4()}",
            json={"name": "X"},
        )
    assert resp.status_code == 404


# ── DELETE /shopping-lists/{id} ───────────────────────────────────────────────


def test_delete_shopping_list_success(app_client):
    with patch(
        "app.api.v1.shopping_lists.delete_shopping_list",
        new=AsyncMock(return_value=True),
    ):
        resp = app_client.delete(f"/api/v1/shopping-lists/{LIST_ID}")
    assert resp.status_code == 204


def test_delete_shopping_list_not_found(app_client):
    with patch(
        "app.api.v1.shopping_lists.delete_shopping_list",
        new=AsyncMock(return_value=False),
    ):
        resp = app_client.delete(f"/api/v1/shopping-lists/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── POST /shopping-lists/{id}/complete ────────────────────────────────────────


def test_complete_list_success(app_client):
    completed = make_list(
        is_completed=True,
        completed_on=date.today(),
        is_active=False,
    )
    with patch(
        "app.api.v1.shopping_lists.complete_list",
        new=AsyncMock(return_value=completed),
    ):
        resp = app_client.post(
            f"/api/v1/shopping-lists/{LIST_ID}/complete",
            json={"create_transaction": False},
        )
    assert resp.status_code == 200
    assert resp.json()["is_completed"] is True
    assert resp.json()["is_active"] is False


def test_complete_list_with_transaction(app_client):
    completed = make_list(
        is_completed=True,
        completed_on=date.today(),
        is_active=False,
    )
    with patch(
        "app.api.v1.shopping_lists.complete_list",
        new=AsyncMock(return_value=completed),
    ) as mock_complete:
        resp = app_client.post(
            f"/api/v1/shopping-lists/{LIST_ID}/complete",
            json={"create_transaction": True},
        )
    assert resp.status_code == 200
    mock_complete.assert_called_once()
    # Verify create_transaction=True was passed as 4th positional arg
    assert mock_complete.call_args.args[3] is True


def test_complete_list_not_found(app_client):
    with patch(
        "app.api.v1.shopping_lists.complete_list",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.post(
            f"/api/v1/shopping-lists/{uuid.uuid4()}/complete",
            json={"create_transaction": False},
        )
    assert resp.status_code == 404


# ── POST /shopping-lists/{id}/items/ ──────────────────────────────────────────


def test_add_item_success(app_client):
    item = make_item()
    with patch(
        "app.api.v1.shopping_lists.add_item",
        new=AsyncMock(return_value=item),
    ):
        resp = app_client.post(
            f"/api/v1/shopping-lists/{LIST_ID}/items/",
            json={"raw_name": "Amul Milk 1L", "quantity": 2.0},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["raw_name"] == "Amul Milk 1L"
    assert body["quantity"] == 2.0
    assert body["is_checked"] is False


def test_add_item_list_not_found(app_client):
    with patch(
        "app.api.v1.shopping_lists.add_item",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.post(
            f"/api/v1/shopping-lists/{uuid.uuid4()}/items/",
            json={"raw_name": "Something", "quantity": 1.0},
        )
    assert resp.status_code == 404


def test_add_item_missing_required(app_client):
    resp = app_client.post(
        f"/api/v1/shopping-lists/{LIST_ID}/items/",
        json={"quantity": 1.0},  # missing raw_name
    )
    assert resp.status_code == 422


# ── PATCH /shopping-lists/{id}/items/{item_id} ────────────────────────────────


def test_patch_item_success(app_client):
    updated = make_item(is_checked=True, actual_price=65.0)
    with patch(
        "app.api.v1.shopping_lists.update_item",
        new=AsyncMock(return_value=updated),
    ):
        resp = app_client.patch(
            f"/api/v1/shopping-lists/{LIST_ID}/items/{ITEM_ID}",
            json={"is_checked": True, "actual_price": 65.0},
        )
    assert resp.status_code == 200
    assert resp.json()["is_checked"] is True
    assert resp.json()["actual_price"] == 65.0


def test_patch_item_not_found(app_client):
    with patch(
        "app.api.v1.shopping_lists.update_item",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.patch(
            f"/api/v1/shopping-lists/{LIST_ID}/items/{uuid.uuid4()}",
            json={"is_checked": True},
        )
    assert resp.status_code == 404


# ── DELETE /shopping-lists/{id}/items/{item_id} ───────────────────────────────


def test_delete_item_success(app_client):
    with patch(
        "app.api.v1.shopping_lists.delete_item",
        new=AsyncMock(return_value=True),
    ):
        resp = app_client.delete(f"/api/v1/shopping-lists/{LIST_ID}/items/{ITEM_ID}")
    assert resp.status_code == 204


def test_delete_item_not_found(app_client):
    with patch(
        "app.api.v1.shopping_lists.delete_item",
        new=AsyncMock(return_value=False),
    ):
        resp = app_client.delete(
            f"/api/v1/shopping-lists/{LIST_ID}/items/{uuid.uuid4()}"
        )
    assert resp.status_code == 404


# ── ShoppingListPublic fields ─────────────────────────────────────────────────


def test_shopping_list_public_with_items():
    item1 = make_item(is_checked=False, estimated_price=65.0, quantity=2.0)
    item2 = make_item(
        id=uuid.uuid4(), is_checked=True, estimated_price=30.0, quantity=1.0
    )
    sl = make_list(
        items=[item1, item2],
        item_count=2,
        checked_count=1,
        estimated_total=130.0,  # only unchecked item1: 65.0 * 2.0
    )
    assert sl.item_count == 2
    assert sl.checked_count == 1
    assert sl.estimated_total == 130.0


def test_shopping_list_public_estimated_total_none_when_no_prices():
    item = make_item(estimated_price=None)
    sl = make_list(items=[item], item_count=1, checked_count=0, estimated_total=None)
    assert sl.estimated_total is None


def test_shopping_list_item_public_source_field():
    item = make_item(source="auto")
    assert item.source == "auto"


def test_shopping_list_item_public_shopping_list_id():
    item = make_item()
    assert item.shopping_list_id == LIST_ID
