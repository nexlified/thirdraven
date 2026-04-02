import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.addresses import router as addresses_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.person import AddressPublic

OWNER_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()
ADDRESS_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)


def make_address(**kwargs) -> AddressPublic:
    defaults = dict(
        id=ADDRESS_ID,
        type="home",
        street="Kastanienallee 22",
        city="Berlin",
        postal_code="10435",
        country=None,
        lat=None,
        lng=None,
        is_primary=True,
    )
    defaults.update(kwargs)
    return AddressPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(addresses_router, prefix="/api/v1")

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


BASE = f"/api/v1/persons/{PERSON_ID}/addresses"


# ── POST /persons/{id}/addresses/ ─────────────────────────────────────────────


def test_add_address_success(app_client):
    addr = make_address()
    with (
        patch(
            "app.api.v1.addresses.get_person",
            new=AsyncMock(return_value=object()),
        ),
        patch(
            "app.api.v1.addresses.create_address",
            new=AsyncMock(return_value=addr),
        ),
    ):
        resp = app_client.post(
            f"{BASE}/",
            json={"type": "home", "street": "Kastanienallee 22", "city": "Berlin"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "home"
    assert body["city"] == "Berlin"


def test_add_address_work_type(app_client):
    addr = make_address(type="work", city="Munich")
    with (
        patch(
            "app.api.v1.addresses.get_person",
            new=AsyncMock(return_value=object()),
        ),
        patch(
            "app.api.v1.addresses.create_address",
            new=AsyncMock(return_value=addr),
        ),
    ):
        resp = app_client.post(
            f"{BASE}/",
            json={"type": "work", "city": "Munich"},
        )
    assert resp.status_code == 201
    assert resp.json()["type"] == "work"


def test_add_address_person_not_found(app_client):
    with patch(
        "app.api.v1.addresses.get_person",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.post(
            f"{BASE}/",
            json={"type": "home", "city": "Berlin"},
        )
    assert resp.status_code == 404


# ── PATCH /persons/{id}/addresses/{address_id} ────────────────────────────────


def test_patch_address_success(app_client):
    updated = make_address(city="Hamburg")
    with patch(
        "app.api.v1.addresses.update_address",
        new=AsyncMock(return_value=updated),
    ):
        resp = app_client.patch(
            f"{BASE}/{ADDRESS_ID}",
            json={"city": "Hamburg"},
        )
    assert resp.status_code == 200
    assert resp.json()["city"] == "Hamburg"


def test_patch_address_not_found(app_client):
    with patch(
        "app.api.v1.addresses.update_address",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.patch(
            f"{BASE}/{uuid.uuid4()}",
            json={"city": "Dresden"},
        )
    assert resp.status_code == 404


# ── DELETE /persons/{id}/addresses/{address_id} ───────────────────────────────


def test_delete_address_success(app_client):
    with patch(
        "app.api.v1.addresses.delete_address",
        new=AsyncMock(return_value=True),
    ):
        resp = app_client.delete(f"{BASE}/{ADDRESS_ID}")
    assert resp.status_code == 204


def test_delete_address_not_found(app_client):
    with patch(
        "app.api.v1.addresses.delete_address",
        new=AsyncMock(return_value=False),
    ):
        resp = app_client.delete(f"{BASE}/{uuid.uuid4()}")
    assert resp.status_code == 404
