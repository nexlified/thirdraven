import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.reminders import (
    asset_reminders_router,
    person_reminders_router,
    router as reminders_router,
    subscription_reminders_router,
)
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.reminder import ReminderPublic

OWNER_ID = uuid.uuid4()
REMINDER_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()
ASSET_ID = uuid.uuid4()
SUB_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)

DUE_AT = datetime(2025, 6, 1, 9, 0, 0)


def make_reminder(**kwargs) -> ReminderPublic:
    defaults = dict(
        id=REMINDER_ID,
        owner_id=OWNER_ID,
        title="Call dentist",
        body=None,
        due_at=DUE_AT,
        remind_at=None,
        recurrence=None,
        is_done=False,
        done_at=None,
        person_id=None,
        asset_id=None,
        subscription_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return ReminderPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(reminders_router, prefix="/api/v1")
    app.include_router(person_reminders_router, prefix="/api/v1")
    app.include_router(asset_reminders_router, prefix="/api/v1")
    app.include_router(subscription_reminders_router, prefix="/api/v1")

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
    app.include_router(reminders_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


# ── POST /reminders/ ──────────────────────────────────────────────────────────


def test_create_reminder_success(app_client):
    reminder = make_reminder()
    with patch("app.api.v1.reminders.create_reminder", new=AsyncMock(return_value=reminder)):
        resp = app_client.post(
            "/api/v1/reminders/",
            json={"title": "Call dentist", "due_at": "2025-06-01T09:00:00"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Call dentist"
    assert body["is_done"] is False


def test_create_reminder_missing_due_at(app_client):
    resp = app_client.post("/api/v1/reminders/", json={"title": "No due date"})
    assert resp.status_code == 422


def test_create_reminder_missing_title(app_client):
    resp = app_client.post(
        "/api/v1/reminders/", json={"due_at": "2025-06-01T09:00:00"}
    )
    assert resp.status_code == 422


def test_create_reminder_with_recurrence(app_client):
    reminder = make_reminder(recurrence="weekly")
    with patch("app.api.v1.reminders.create_reminder", new=AsyncMock(return_value=reminder)):
        resp = app_client.post(
            "/api/v1/reminders/",
            json={
                "title": "Weekly check",
                "due_at": "2025-06-01T09:00:00",
                "recurrence": "weekly",
            },
        )
    assert resp.status_code == 201
    assert resp.json()["recurrence"] == "weekly"


def test_create_reminder_unauthenticated(unauthed_client):
    resp = unauthed_client.post(
        "/api/v1/reminders/",
        json={"title": "Call dentist", "due_at": "2025-06-01T09:00:00"},
    )
    assert resp.status_code in (401, 422, 500)


# ── GET /reminders/ ────────────────────────────────────────────────────────────


def test_list_reminders_returns_list(app_client):
    reminders = [make_reminder(), make_reminder(id=uuid.uuid4(), title="Buy groceries")]
    with patch("app.api.v1.reminders.list_reminders", new=AsyncMock(return_value=(reminders, 2))):
        resp = app_client.get("/api/v1/reminders/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_reminders_empty(app_client):
    with patch("app.api.v1.reminders.list_reminders", new=AsyncMock(return_value=([], 0))):
        resp = app_client.get("/api/v1/reminders/")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_list_reminders_is_done_filter_false(app_client):
    with patch(
        "app.api.v1.reminders.list_reminders", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        app_client.get("/api/v1/reminders/?is_done=false")
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["is_done"] is False


def test_list_reminders_is_done_filter_true(app_client):
    done = make_reminder(is_done=True, done_at=datetime.now(UTC))
    with patch(
        "app.api.v1.reminders.list_reminders", new=AsyncMock(return_value=([done], 1))
    ) as mock_list:
        resp = app_client.get("/api/v1/reminders/?is_done=true")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


# ── GET /reminders/{reminder_id} ──────────────────────────────────────────────


def test_get_reminder_found(app_client):
    reminder = make_reminder()
    with patch("app.api.v1.reminders.get_reminder", new=AsyncMock(return_value=reminder)):
        resp = app_client.get(f"/api/v1/reminders/{REMINDER_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(REMINDER_ID)


def test_get_reminder_not_found(app_client):
    with patch("app.api.v1.reminders.get_reminder", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"/api/v1/reminders/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /reminders/{reminder_id} ────────────────────────────────────────────


def test_patch_reminder_mark_done(app_client):
    done_reminder = make_reminder(is_done=True, done_at=datetime.now(UTC))
    with patch(
        "app.api.v1.reminders.update_reminder", new=AsyncMock(return_value=done_reminder)
    ):
        resp = app_client.patch(
            f"/api/v1/reminders/{REMINDER_ID}", json={"is_done": True}
        )
    assert resp.status_code == 200
    assert resp.json()["is_done"] is True


def test_patch_reminder_not_found(app_client):
    with patch("app.api.v1.reminders.update_reminder", new=AsyncMock(return_value=None)):
        resp = app_client.patch(
            f"/api/v1/reminders/{uuid.uuid4()}", json={"title": "Ghost"}
        )
    assert resp.status_code == 404


# ── DELETE /reminders/{reminder_id} ───────────────────────────────────────────


def test_delete_reminder_success(app_client):
    with patch(
        "app.api.v1.reminders.soft_delete_reminder", new=AsyncMock(return_value=object())
    ):
        resp = app_client.delete(f"/api/v1/reminders/{REMINDER_ID}")
    assert resp.status_code == 204


def test_delete_reminder_not_found(app_client):
    with patch(
        "app.api.v1.reminders.soft_delete_reminder", new=AsyncMock(return_value=None)
    ):
        resp = app_client.delete(f"/api/v1/reminders/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── Entity-scoped list endpoints ───────────────────────────────────────────────


def test_list_person_reminders(app_client):
    reminders = [make_reminder(person_id=PERSON_ID)]
    with patch(
        "app.api.v1.reminders.list_reminders", new=AsyncMock(return_value=(reminders, 1))
    ) as mock_list:
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}/reminders/")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["person_id"] == PERSON_ID


def test_list_asset_reminders(app_client):
    reminders = [make_reminder(asset_id=ASSET_ID)]
    with patch(
        "app.api.v1.reminders.list_reminders", new=AsyncMock(return_value=(reminders, 1))
    ) as mock_list:
        resp = app_client.get(f"/api/v1/assets/{ASSET_ID}/reminders/")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["asset_id"] == ASSET_ID


def test_list_subscription_reminders(app_client):
    reminders = [make_reminder(subscription_id=SUB_ID)]
    with patch(
        "app.api.v1.reminders.list_reminders", new=AsyncMock(return_value=(reminders, 1))
    ) as mock_list:
        resp = app_client.get(f"/api/v1/subscriptions/{SUB_ID}/reminders/")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["subscription_id"] == SUB_ID
