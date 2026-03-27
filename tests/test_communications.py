import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.communications import router as communications_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.communication import CommPublic

OWNER_ID = uuid.uuid4()
COMM_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.utcnow(),
)


def make_comm(**kwargs) -> CommPublic:
    defaults = dict(
        id=COMM_ID,
        owner_id=OWNER_ID,
        channel="email",
        direction="inbound",
        status="raw",
        is_bot=False,
        sender_identifier="alice@example.com",
        recipient_identifiers=None,
        source_app=None,
        external_id=None,
        thread_id=None,
        subject="Hello",
        body="Hey there",
        raw_payload=None,
        communicated_at=None,
        processed_at=None,
        context=None,
        person_id=None,
        interaction_id=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return CommPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(communications_router, prefix="/api/v1")

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
    app.include_router(communications_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


# ── POST /communications/ingest ────────────────────────────────────────────────


def test_ingest_communication_success(app_client):
    comm = make_comm()
    with patch(
        "app.api.v1.communications.ingest_communication",
        new=AsyncMock(return_value=comm),
    ):
        resp = app_client.post(
            "/api/v1/communications/ingest",
            json={"channel": "email", "sender": "alice@example.com", "body": "Hey"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["channel"] == "email"
    assert body["owner_id"] == str(OWNER_ID)


def test_ingest_communication_accepts_unknown_fields(app_client):
    """CommIngest has extra='allow' — unknown fields must not cause a 422."""
    comm = make_comm(raw_payload={"custom_tag": "vip"})
    with patch(
        "app.api.v1.communications.ingest_communication",
        new=AsyncMock(return_value=comm),
    ):
        resp = app_client.post(
            "/api/v1/communications/ingest",
            json={"channel": "email", "custom_tag": "vip"},
        )
    assert resp.status_code == 201


def test_ingest_communication_missing_channel_returns_422(app_client):
    resp = app_client.post(
        "/api/v1/communications/ingest",
        json={"sender": "alice@example.com", "body": "Hey"},
    )
    assert resp.status_code == 422


# ── POST /communications/ ──────────────────────────────────────────────────────


def test_create_communication_success(app_client):
    comm = make_comm()
    with patch(
        "app.api.v1.communications.create_communication",
        new=AsyncMock(return_value=comm),
    ):
        resp = app_client.post(
            "/api/v1/communications/",
            json={"channel": "email", "sender_identifier": "alice@example.com"},
        )
    assert resp.status_code == 201
    assert resp.json()["channel"] == "email"


def test_create_communication_missing_channel_returns_422(app_client):
    resp = app_client.post(
        "/api/v1/communications/",
        json={"sender_identifier": "alice@example.com"},
    )
    assert resp.status_code == 422


# ── GET /communications/ ───────────────────────────────────────────────────────


def test_list_communications_returns_list(app_client):
    comms = [make_comm(), make_comm(id=uuid.uuid4(), channel="whatsapp")]
    with patch(
        "app.api.v1.communications.list_communications",
        new=AsyncMock(return_value=(comms, 2)),
    ):
        resp = app_client.get("/api/v1/communications/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_communications_empty(app_client):
    with patch(
        "app.api.v1.communications.list_communications",
        new=AsyncMock(return_value=([], 0)),
    ):
        resp = app_client.get("/api/v1/communications/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_communications_passes_channel_filter(app_client):
    mock_fn = AsyncMock(return_value=([], 0))
    with patch("app.api.v1.communications.list_communications", new=mock_fn):
        app_client.get("/api/v1/communications/?channel=email")
    kwargs = mock_fn.call_args.kwargs
    assert kwargs["channel"] == "email"


def test_list_communications_passes_status_filter(app_client):
    mock_fn = AsyncMock(return_value=([], 0))
    with patch("app.api.v1.communications.list_communications", new=mock_fn):
        app_client.get("/api/v1/communications/?status=matched")
    kwargs = mock_fn.call_args.kwargs
    assert kwargs["status"] == "matched"


def test_list_communications_passes_person_id_filter(app_client):
    mock_fn = AsyncMock(return_value=([], 0))
    with patch("app.api.v1.communications.list_communications", new=mock_fn):
        app_client.get(f"/api/v1/communications/?person_id={PERSON_ID}")
    kwargs = mock_fn.call_args.kwargs
    assert kwargs["person_id"] == PERSON_ID


# ── GET /communications/{comm_id} ──────────────────────────────────────────────


def test_get_communication_found(app_client):
    comm = make_comm()
    with patch(
        "app.api.v1.communications.get_communication",
        new=AsyncMock(return_value=comm),
    ):
        resp = app_client.get(f"/api/v1/communications/{COMM_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(COMM_ID)


def test_get_communication_not_found(app_client):
    with patch(
        "app.api.v1.communications.get_communication",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.get(f"/api/v1/communications/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /communications/{comm_id} ────────────────────────────────────────────


def test_patch_communication_success(app_client):
    updated = make_comm(status="matched", person_id=PERSON_ID)
    with patch(
        "app.api.v1.communications.update_communication",
        new=AsyncMock(return_value=updated),
    ):
        resp = app_client.patch(
            f"/api/v1/communications/{COMM_ID}",
            json={"status": "matched", "person_id": str(PERSON_ID)},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "matched"
    assert resp.json()["person_id"] == str(PERSON_ID)


def test_patch_communication_not_found(app_client):
    with patch(
        "app.api.v1.communications.update_communication",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.patch(
            f"/api/v1/communications/{uuid.uuid4()}", json={"status": "ignored"}
        )
    assert resp.status_code == 404


# ── DELETE /communications/{comm_id} ───────────────────────────────────────────


def test_delete_communication_success(app_client):
    with patch(
        "app.api.v1.communications.delete_communication",
        new=AsyncMock(return_value=object()),
    ):
        resp = app_client.delete(f"/api/v1/communications/{COMM_ID}")
    assert resp.status_code == 204


def test_delete_communication_not_found(app_client):
    with patch(
        "app.api.v1.communications.delete_communication",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.delete(f"/api/v1/communications/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── POST /communications/{comm_id}/match ───────────────────────────────────────


def test_match_communication_success(app_client):
    matched = make_comm(status="matched", person_id=PERSON_ID)
    with patch(
        "app.api.v1.communications.match_communication",
        new=AsyncMock(return_value=matched),
    ):
        resp = app_client.post(f"/api/v1/communications/{COMM_ID}/match")
    assert resp.status_code == 200
    assert resp.json()["status"] == "matched"
    assert resp.json()["person_id"] == str(PERSON_ID)


def test_match_communication_not_found(app_client):
    with patch(
        "app.api.v1.communications.match_communication",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.post(f"/api/v1/communications/{uuid.uuid4()}/match")
    assert resp.status_code == 404


# ── POST /communications/{comm_id}/extract-actions ─────────────────────────────


def test_extract_actions_returns_501(app_client):
    """Phase 2 stub — always returns 501 regardless of input."""
    resp = app_client.post(f"/api/v1/communications/{COMM_ID}/extract-actions")
    assert resp.status_code == 501
    assert "not yet implemented" in resp.json()["detail"].lower()
