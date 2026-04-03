import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.followups import router as followups_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.followup import FollowUpPublic

OWNER_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()
FOLLOWUP_ID = uuid.uuid4()
INTERACTION_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)


def make_followup(**kwargs) -> FollowUpPublic:
    defaults = dict(
        id=FOLLOWUP_ID,
        person_id=PERSON_ID,
        owner_id=OWNER_ID,
        body="Send project proposal",
        due_on=None,
        interaction_id=None,
        cleared_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return FollowUpPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(followups_router, prefix="/api/v1")

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


# ── POST /persons/{person_id}/follow-ups/ ─────────────────────────────────────


def test_create_followup_success(app_client):
    fu = make_followup()
    with (
        patch("app.api.v1.followups.get_person", new=AsyncMock(return_value=object())),
        patch("app.api.v1.followups.create_followup", new=AsyncMock(return_value=fu)),
    ):
        resp = app_client.post(
            f"/api/v1/persons/{PERSON_ID}/follow-ups/",
            json={"body": "Send project proposal"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["body"] == "Send project proposal"
    assert body["cleared_at"] is None


def test_create_followup_person_not_found(app_client):
    with patch("app.api.v1.followups.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.post(
            f"/api/v1/persons/{uuid.uuid4()}/follow-ups/",
            json={"body": "Test"},
        )
    assert resp.status_code == 404


def test_create_followup_missing_body(app_client):
    with patch("app.api.v1.followups.get_person", new=AsyncMock(return_value=object())):
        resp = app_client.post(
            f"/api/v1/persons/{PERSON_ID}/follow-ups/",
            json={"due_on": "2025-06-01"},
        )
    assert resp.status_code == 422


def test_create_followup_with_due_date_and_interaction(app_client):
    fu = make_followup(due_on=date(2025, 6, 1), interaction_id=INTERACTION_ID)
    with (
        patch("app.api.v1.followups.get_person", new=AsyncMock(return_value=object())),
        patch("app.api.v1.followups.create_followup", new=AsyncMock(return_value=fu)),
    ):
        resp = app_client.post(
            f"/api/v1/persons/{PERSON_ID}/follow-ups/",
            json={
                "body": "Send proposal",
                "due_on": "2025-06-01",
                "interaction_id": str(INTERACTION_ID),
            },
        )
    assert resp.status_code == 201
    assert resp.json()["due_on"] == "2025-06-01"
    assert resp.json()["interaction_id"] == str(INTERACTION_ID)


# ── GET /persons/{person_id}/follow-ups/ ──────────────────────────────────────


def test_list_followups_returns_list(app_client):
    fus = [make_followup(), make_followup(id=uuid.uuid4(), body="Schedule call")]
    with (
        patch("app.api.v1.followups.get_person", new=AsyncMock(return_value=object())),
        patch("app.api.v1.followups.list_followups", new=AsyncMock(return_value=(fus, 2))),
    ):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}/follow-ups/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_followups_person_not_found(app_client):
    with patch("app.api.v1.followups.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"/api/v1/persons/{uuid.uuid4()}/follow-ups/")
    assert resp.status_code == 404


def test_list_followups_pending_only_filter(app_client):
    with (
        patch("app.api.v1.followups.get_person", new=AsyncMock(return_value=object())),
        patch(
            "app.api.v1.followups.list_followups", new=AsyncMock(return_value=([], 0))
        ) as mock_list,
    ):
        app_client.get(f"/api/v1/persons/{PERSON_ID}/follow-ups/?pending_only=true")
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["pending_only"] is True


# ── GET /persons/{person_id}/follow-ups/{followup_id} ─────────────────────────


def test_get_followup_found(app_client):
    fu = make_followup()
    with patch("app.api.v1.followups.get_followup", new=AsyncMock(return_value=fu)):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}/follow-ups/{FOLLOWUP_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(FOLLOWUP_ID)


def test_get_followup_not_found(app_client):
    with patch("app.api.v1.followups.get_followup", new=AsyncMock(return_value=None)):
        resp = app_client.get(
            f"/api/v1/persons/{PERSON_ID}/follow-ups/{uuid.uuid4()}"
        )
    assert resp.status_code == 404


def test_get_followup_wrong_person(app_client):
    fu = make_followup(person_id=uuid.uuid4())
    with patch("app.api.v1.followups.get_followup", new=AsyncMock(return_value=fu)):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}/follow-ups/{FOLLOWUP_ID}")
    assert resp.status_code == 404


# ── PATCH /persons/{person_id}/follow-ups/{followup_id} ───────────────────────


def test_patch_followup_success(app_client):
    updated = make_followup(body="Send updated proposal")
    with patch("app.api.v1.followups.update_followup", new=AsyncMock(return_value=updated)):
        resp = app_client.patch(
            f"/api/v1/persons/{PERSON_ID}/follow-ups/{FOLLOWUP_ID}",
            json={"body": "Send updated proposal"},
        )
    assert resp.status_code == 200
    assert resp.json()["body"] == "Send updated proposal"


def test_patch_followup_mark_cleared(app_client):
    cleared = make_followup(cleared_at=datetime.now(UTC))
    with patch(
        "app.api.v1.followups.update_followup", new=AsyncMock(return_value=cleared)
    ):
        resp = app_client.patch(
            f"/api/v1/persons/{PERSON_ID}/follow-ups/{FOLLOWUP_ID}",
            json={"cleared": True},
        )
    assert resp.status_code == 200
    assert resp.json()["cleared_at"] is not None


def test_patch_followup_not_found(app_client):
    with patch("app.api.v1.followups.update_followup", new=AsyncMock(return_value=None)):
        resp = app_client.patch(
            f"/api/v1/persons/{PERSON_ID}/follow-ups/{uuid.uuid4()}",
            json={"body": "Ghost"},
        )
    assert resp.status_code == 404


# ── DELETE /persons/{person_id}/follow-ups/{followup_id} ──────────────────────


def test_delete_followup_success(app_client):
    with (
        patch("app.api.v1.followups.get_person", new=AsyncMock(return_value=object())),
        patch(
            "app.api.v1.followups.delete_followup", new=AsyncMock(return_value=object())
        ),
    ):
        resp = app_client.delete(
            f"/api/v1/persons/{PERSON_ID}/follow-ups/{FOLLOWUP_ID}"
        )
    assert resp.status_code == 204


def test_delete_followup_person_not_found(app_client):
    with patch("app.api.v1.followups.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.delete(
            f"/api/v1/persons/{uuid.uuid4()}/follow-ups/{FOLLOWUP_ID}"
        )
    assert resp.status_code == 404


def test_delete_followup_not_found(app_client):
    with (
        patch("app.api.v1.followups.get_person", new=AsyncMock(return_value=object())),
        patch("app.api.v1.followups.delete_followup", new=AsyncMock(return_value=None)),
    ):
        resp = app_client.delete(
            f"/api/v1/persons/{PERSON_ID}/follow-ups/{uuid.uuid4()}"
        )
    assert resp.status_code == 404
