import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.renewals import router as renewals_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.renewal import RenewalEntry

OWNER_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.utcnow(),
)


def make_renewal_entry(**kwargs) -> RenewalEntry:
    defaults = dict(
        entity_type="tracked_record",
        entity_id=uuid.uuid4(),
        title="Car Insurance",
        record_type="insurance-vehicle",
        expires_on=date(2026, 6, 1),
        days_remaining=10,
        auto_renews=False,
        cost=500.0,
        currency="GBP",
        asset_id=None,
        person_id=None,
    )
    defaults.update(kwargs)
    return RenewalEntry(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(renewals_router, prefix="/api/v1")

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
    app.include_router(renewals_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


# ── GET /renewals/upcoming ─────────────────────────────────────────────────────


def test_get_upcoming_renewals_returns_list(app_client):
    entries = [
        make_renewal_entry(),
        make_renewal_entry(
            entity_type="subscription",
            title="Netflix",
            record_type=None,
            expires_on=date(2026, 4, 15),
            days_remaining=5,
        ),
    ]
    with patch(
        "app.api.v1.renewals.get_upcoming_renewals",
        new=AsyncMock(return_value=entries),
    ):
        resp = app_client.get("/api/v1/renewals/upcoming")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert body[0]["title"] == "Car Insurance"
    assert body[1]["record_type"] is None


def test_get_upcoming_renewals_empty(app_client):
    with patch(
        "app.api.v1.renewals.get_upcoming_renewals", new=AsyncMock(return_value=[])
    ):
        resp = app_client.get("/api/v1/renewals/upcoming")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_upcoming_renewals_passes_days_param(app_client):
    mock_fn = AsyncMock(return_value=[])
    with patch("app.api.v1.renewals.get_upcoming_renewals", new=mock_fn):
        app_client.get("/api/v1/renewals/upcoming?days=14")
    kwargs = mock_fn.call_args.kwargs
    assert kwargs["days"] == 14


def test_get_upcoming_renewals_unauthenticated(unauthed_client):
    resp = unauthed_client.get("/api/v1/renewals/upcoming")
    assert resp.status_code in (401, 422, 500)
