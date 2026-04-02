import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.records import router as records_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.tracked_record import RecordPublic
from app.schemas.vocabulary import TermSlim

OWNER_ID = uuid.uuid4()
RECORD_ID = uuid.uuid4()
ASSET_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()
TERM_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)

LICENSE_TERM = TermSlim(id=TERM_ID, name="Driving Licence", slug="license-driving")


def make_record(**kwargs) -> RecordPublic:
    defaults = dict(
        id=RECORD_ID,
        owner_id=OWNER_ID,
        record_type=LICENSE_TERM,
        title="UK Driving Licence",
        reference_number=None,
        issuer=None,
        issued_on=None,
        expires_on=None,
        reminder_days=30,
        cost=None,
        currency=None,
        billing_frequency=None,
        auto_renews=False,
        coverage_notes=None,
        metadata_=None,
        asset_id=None,
        person_id=None,
        notes=None,
        is_expired=False,
        days_until_expiry=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return RecordPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(records_router, prefix="/api/v1")

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
    app.include_router(records_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


# ── POST /records/ ─────────────────────────────────────────────────────────────


def test_create_record_success(app_client):
    record = make_record()
    with patch("app.api.v1.records.create_record", new=AsyncMock(return_value=record)):
        resp = app_client.post(
            "/api/v1/records/",
            json={"record_type": "license-driving", "title": "UK Driving Licence"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "UK Driving Licence"
    assert body["owner_id"] == str(OWNER_ID)
    assert body["record_type"]["slug"] == "license-driving"


def test_create_record_missing_record_type_returns_422(app_client):
    resp = app_client.post(
        "/api/v1/records/",
        json={"title": "No Type"},
    )
    assert resp.status_code == 422


def test_create_record_missing_title_returns_422(app_client):
    resp = app_client.post(
        "/api/v1/records/",
        json={"record_type": "license-driving"},
    )
    assert resp.status_code == 422


def test_create_record_unauthenticated(unauthed_client):
    resp = unauthed_client.post(
        "/api/v1/records/",
        json={"record_type": "license-driving", "title": "UK Driving Licence"},
    )
    assert resp.status_code in (401, 422, 500)


# ── GET /records/ ──────────────────────────────────────────────────────────────


def test_list_records_returns_list(app_client):
    records = [make_record(), make_record(id=uuid.uuid4(), title="Passport")]
    with patch(
        "app.api.v1.records.list_records", new=AsyncMock(return_value=(records, 2))
    ):
        resp = app_client.get("/api/v1/records/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_records_empty(app_client):
    with patch("app.api.v1.records.list_records", new=AsyncMock(return_value=([], 0))):
        resp = app_client.get("/api/v1/records/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_records_passes_record_type_slug_kwarg(app_client):
    """Query param `record_type` is forwarded to CRUD as `record_type_slug`."""
    mock_fn = AsyncMock(return_value=([], 0))
    with patch("app.api.v1.records.list_records", new=mock_fn):
        app_client.get("/api/v1/records/?record_type=license-driving")
    kwargs = mock_fn.call_args.kwargs
    assert kwargs["record_type_slug"] == "license-driving"


def test_list_records_passes_asset_id_filter(app_client):
    mock_fn = AsyncMock(return_value=([], 0))
    with patch("app.api.v1.records.list_records", new=mock_fn):
        app_client.get(f"/api/v1/records/?asset_id={ASSET_ID}")
    kwargs = mock_fn.call_args.kwargs
    assert kwargs["asset_id"] == ASSET_ID


def test_list_records_passes_person_id_filter(app_client):
    mock_fn = AsyncMock(return_value=([], 0))
    with patch("app.api.v1.records.list_records", new=mock_fn):
        app_client.get(f"/api/v1/records/?person_id={PERSON_ID}")
    kwargs = mock_fn.call_args.kwargs
    assert kwargs["person_id"] == PERSON_ID


def test_list_records_passes_expires_before_filter(app_client):
    mock_fn = AsyncMock(return_value=([], 0))
    with patch("app.api.v1.records.list_records", new=mock_fn):
        app_client.get("/api/v1/records/?expires_before=2026-12-31")
    kwargs = mock_fn.call_args.kwargs
    assert kwargs["expires_before"] == date(2026, 12, 31)


# ── GET /records/{record_id} ───────────────────────────────────────────────────


def test_get_record_found(app_client):
    record = make_record()
    with patch("app.api.v1.records.get_record", new=AsyncMock(return_value=record)):
        resp = app_client.get(f"/api/v1/records/{RECORD_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(RECORD_ID)


def test_get_record_not_found(app_client):
    with patch("app.api.v1.records.get_record", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"/api/v1/records/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /records/{record_id} ─────────────────────────────────────────────────


def test_patch_record_success(app_client):
    updated = make_record(title="Updated Licence", reminder_days=60)
    with patch("app.api.v1.records.update_record", new=AsyncMock(return_value=updated)):
        resp = app_client.patch(
            f"/api/v1/records/{RECORD_ID}",
            json={"title": "Updated Licence", "reminder_days": 60},
        )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Licence"
    assert resp.json()["reminder_days"] == 60


def test_patch_record_not_found(app_client):
    with patch("app.api.v1.records.update_record", new=AsyncMock(return_value=None)):
        resp = app_client.patch(
            f"/api/v1/records/{uuid.uuid4()}", json={"title": "Ghost"}
        )
    assert resp.status_code == 404


# ── DELETE /records/{record_id} ────────────────────────────────────────────────


def test_delete_record_success(app_client):
    with patch(
        "app.api.v1.records.delete_record", new=AsyncMock(return_value=object())
    ):
        resp = app_client.delete(f"/api/v1/records/{RECORD_ID}")
    assert resp.status_code == 204


def test_delete_record_not_found(app_client):
    with patch("app.api.v1.records.delete_record", new=AsyncMock(return_value=None)):
        resp = app_client.delete(f"/api/v1/records/{uuid.uuid4()}")
    assert resp.status_code == 404
