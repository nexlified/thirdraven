import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.events import event_persons_router, events_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.event import EventPersonPublic, EventPublic
from app.schemas.person import PersonSlim
from app.schemas.vocabulary import TermSlim

OWNER_ID = uuid.uuid4()
EVENT_ID = uuid.uuid4()
EVENT_PERSON_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()
TYPE_TERM_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)

MEETING_TERM = TermSlim(id=TYPE_TERM_ID, name="Meeting", slug="meeting")

FAKE_PERSON_SLIM = PersonSlim(
    id=PERSON_ID,
    owner_id=OWNER_ID,
    first_name="Alice",
    last_name="Smith",
    nickname=None,
    email=None,
    phone=None,
    notes=None,
    tags=[],
    closeness_level=None,
    visibility="private",
    household_id=None,
    is_placeholder=False,
    is_bot=False,
    created_at=datetime.now(UTC),
    updated_at=datetime.now(UTC),
)


def make_event(**kwargs) -> EventPublic:
    defaults = dict(
        id=EVENT_ID,
        owner_id=OWNER_ID,
        title="Team sync",
        event_type=MEETING_TERM,
        description=None,
        occurred_on=date(2025, 1, 15),
        location=None,
        notes=None,
        persons=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return EventPublic(**defaults)


def make_event_person(**kwargs) -> EventPersonPublic:
    defaults = dict(
        id=EVENT_PERSON_ID,
        event_id=EVENT_ID,
        person=FAKE_PERSON_SLIM,
        role=None,
        created_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return EventPersonPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(events_router, prefix="/api/v1")
    app.include_router(event_persons_router, prefix="/api/v1")

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
    app.include_router(events_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


# ── POST /events/ ──────────────────────────────────────────────────────────────


def test_create_event_success(app_client):
    event = make_event()
    with patch("app.api.v1.events.create_event", new=AsyncMock(return_value=event)):
        resp = app_client.post(
            "/api/v1/events/",
            json={"title": "Team sync", "event_type": "meeting"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Team sync"
    assert body["event_type"]["slug"] == "meeting"


def test_create_event_missing_title(app_client):
    resp = app_client.post("/api/v1/events/", json={"event_type": "meeting"})
    assert resp.status_code == 422


def test_create_event_with_all_fields(app_client):
    event = make_event(description="Quarterly review", location="Office")
    with patch("app.api.v1.events.create_event", new=AsyncMock(return_value=event)):
        resp = app_client.post(
            "/api/v1/events/",
            json={
                "title": "Team sync",
                "event_type": "meeting",
                "description": "Quarterly review",
                "occurred_on": "2025-01-15",
                "location": "Office",
            },
        )
    assert resp.status_code == 201


def test_create_event_unauthenticated(unauthed_client):
    resp = unauthed_client.post(
        "/api/v1/events/",
        json={"title": "Team sync"},
    )
    assert resp.status_code in (401, 422, 500)


# ── GET /events/ ───────────────────────────────────────────────────────────────


def test_list_events_returns_list(app_client):
    events = [make_event(), make_event(id=uuid.uuid4(), title="Offsite")]
    with patch(
        "app.api.v1.events.list_events", new=AsyncMock(return_value=(events, 2))
    ):
        resp = app_client.get("/api/v1/events/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_events_empty(app_client):
    with patch("app.api.v1.events.list_events", new=AsyncMock(return_value=([], 0))):
        resp = app_client.get("/api/v1/events/")
    assert resp.status_code == 200
    assert resp.json()["items"] == []
    assert resp.json()["total"] == 0


# ── GET /events/{event_id} ─────────────────────────────────────────────────────


def test_get_event_found(app_client):
    event = make_event()
    with patch("app.api.v1.events.get_event", new=AsyncMock(return_value=event)):
        resp = app_client.get(f"/api/v1/events/{EVENT_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(EVENT_ID)


def test_get_event_not_found(app_client):
    with patch("app.api.v1.events.get_event", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"/api/v1/events/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /events/{event_id} ───────────────────────────────────────────────────


def test_patch_event_success(app_client):
    updated = make_event(title="Updated sync", location="Remote")
    with patch("app.api.v1.events.update_event", new=AsyncMock(return_value=updated)):
        resp = app_client.patch(
            f"/api/v1/events/{EVENT_ID}",
            json={"title": "Updated sync", "location": "Remote"},
        )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated sync"


def test_patch_event_not_found(app_client):
    with patch("app.api.v1.events.update_event", new=AsyncMock(return_value=None)):
        resp = app_client.patch(
            f"/api/v1/events/{uuid.uuid4()}",
            json={"title": "Ghost"},
        )
    assert resp.status_code == 404


def test_patch_event_partial_update(app_client):
    updated = make_event(location="New York")
    with patch(
        "app.api.v1.events.update_event", new=AsyncMock(return_value=updated)
    ) as mock_update:
        resp = app_client.patch(
            f"/api/v1/events/{EVENT_ID}", json={"location": "New York"}
        )
    assert resp.status_code == 200
    update_data = mock_update.call_args.args[3]
    assert update_data.location == "New York"
    assert update_data.title is None


# ── DELETE /events/{event_id} ──────────────────────────────────────────────────


def test_delete_event_success(app_client):
    with patch("app.api.v1.events.delete_event", new=AsyncMock(return_value=object())):
        resp = app_client.delete(f"/api/v1/events/{EVENT_ID}")
    assert resp.status_code == 204


def test_delete_event_not_found(app_client):
    with patch("app.api.v1.events.delete_event", new=AsyncMock(return_value=None)):
        resp = app_client.delete(f"/api/v1/events/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── POST /events/{event_id}/persons/ ──────────────────────────────────────────


def test_add_event_person_success(app_client):
    ep = make_event_person(role="speaker")
    with patch("app.api.v1.events.add_event_person", new=AsyncMock(return_value=ep)):
        resp = app_client.post(
            f"/api/v1/events/{EVENT_ID}/persons/",
            json={"person_id": str(PERSON_ID), "role": "speaker"},
        )
    assert resp.status_code == 201
    assert resp.json()["role"] == "speaker"
    assert resp.json()["person"]["id"] == str(PERSON_ID)


def test_add_event_person_event_not_found(app_client):
    with patch("app.api.v1.events.add_event_person", new=AsyncMock(return_value=None)):
        resp = app_client.post(
            f"/api/v1/events/{uuid.uuid4()}/persons/",
            json={"person_id": str(PERSON_ID)},
        )
    assert resp.status_code == 404


# ── GET /events/{event_id}/persons/ ───────────────────────────────────────────


def test_list_event_persons(app_client):
    eps = [make_event_person(), make_event_person(id=uuid.uuid4())]
    with patch("app.api.v1.events.list_event_persons", new=AsyncMock(return_value=eps)):
        resp = app_client.get(f"/api/v1/events/{EVENT_ID}/persons/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# ── DELETE /events/{event_id}/persons/{event_person_id} ───────────────────────


def test_remove_event_person_success(app_client):
    with patch(
        "app.api.v1.events.remove_event_person", new=AsyncMock(return_value=object())
    ):
        resp = app_client.delete(f"/api/v1/events/{EVENT_ID}/persons/{EVENT_PERSON_ID}")
    assert resp.status_code == 204


def test_remove_event_person_not_found(app_client):
    with patch(
        "app.api.v1.events.remove_event_person", new=AsyncMock(return_value=None)
    ):
        resp = app_client.delete(f"/api/v1/events/{EVENT_ID}/persons/{uuid.uuid4()}")
    assert resp.status_code == 404
