import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.channels import router as channels_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.person import ChannelPublic

OWNER_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()
CHANNEL_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.utcnow(),
)


def make_channel(**kwargs) -> ChannelPublic:
    defaults = dict(
        id=CHANNEL_ID,
        value="alice@example.com",
        type="email",
        label=None,
        is_primary=True,
    )
    defaults.update(kwargs)
    return ChannelPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(channels_router, prefix="/api/v1")

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


BASE = f"/api/v1/persons/{PERSON_ID}/channels"


# ── POST /persons/{id}/channels/ ──────────────────────────────────────────────


def test_add_channel_success(app_client):
    ch = make_channel()
    with (
        patch(
            "app.api.v1.channels.get_person",
            new=AsyncMock(return_value=object()),
        ),
        patch(
            "app.api.v1.channels.create_channel",
            new=AsyncMock(return_value=ch),
        ),
    ):
        resp = app_client.post(
            f"{BASE}/",
            json={"value": "alice@example.com", "type": "email", "is_primary": True},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["value"] == "alice@example.com"
    assert body["type"] == "email"
    assert body["is_primary"] is True


def test_add_channel_person_not_found(app_client):
    with patch(
        "app.api.v1.channels.get_person",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.post(
            f"{BASE}/",
            json={"value": "alice@example.com", "type": "email"},
        )
    assert resp.status_code == 404


def test_add_channel_missing_value_returns_422(app_client):
    resp = app_client.post(f"{BASE}/", json={"type": "email"})
    assert resp.status_code == 422


def test_add_channel_missing_type_returns_422(app_client):
    resp = app_client.post(f"{BASE}/", json={"value": "alice@example.com"})
    assert resp.status_code == 422


def test_add_channel_discord(app_client):
    ch = make_channel(value="alice#1234", type="discord", is_primary=False)
    with (
        patch(
            "app.api.v1.channels.get_person",
            new=AsyncMock(return_value=object()),
        ),
        patch(
            "app.api.v1.channels.create_channel",
            new=AsyncMock(return_value=ch),
        ),
    ):
        resp = app_client.post(
            f"{BASE}/",
            json={"value": "alice#1234", "type": "discord"},
        )
    assert resp.status_code == 201
    assert resp.json()["type"] == "discord"


def test_add_channel_with_label(app_client):
    ch = make_channel(label="work")
    with (
        patch(
            "app.api.v1.channels.get_person",
            new=AsyncMock(return_value=object()),
        ),
        patch(
            "app.api.v1.channels.create_channel",
            new=AsyncMock(return_value=ch),
        ),
    ):
        resp = app_client.post(
            f"{BASE}/",
            json={"value": "alice@work.com", "type": "email", "label": "work"},
        )
    assert resp.status_code == 201
    assert resp.json()["label"] == "work"


# ── PATCH /persons/{id}/channels/{channel_id} ─────────────────────────────────


def test_patch_channel_success(app_client):
    updated = make_channel(value="+491234567890", type="mobile", is_primary=False)
    with patch(
        "app.api.v1.channels.update_channel",
        new=AsyncMock(return_value=updated),
    ):
        resp = app_client.patch(
            f"{BASE}/{CHANNEL_ID}",
            json={"value": "+491234567890", "type": "mobile"},
        )
    assert resp.status_code == 200
    assert resp.json()["value"] == "+491234567890"
    assert resp.json()["type"] == "mobile"


def test_patch_channel_not_found(app_client):
    with patch(
        "app.api.v1.channels.update_channel",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.patch(
            f"{BASE}/{uuid.uuid4()}",
            json={"value": "new@example.com"},
        )
    assert resp.status_code == 404


# ── DELETE /persons/{id}/channels/{channel_id} ────────────────────────────────


def test_delete_channel_success(app_client):
    with patch(
        "app.api.v1.channels.delete_channel",
        new=AsyncMock(return_value=True),
    ):
        resp = app_client.delete(f"{BASE}/{CHANNEL_ID}")
    assert resp.status_code == 204


def test_delete_channel_not_found(app_client):
    with patch(
        "app.api.v1.channels.delete_channel",
        new=AsyncMock(return_value=False),
    ):
        resp = app_client.delete(f"{BASE}/{uuid.uuid4()}")
    assert resp.status_code == 404
