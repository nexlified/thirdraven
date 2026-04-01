import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.notes import router as notes_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.note import NotePublicRead, NoteStatistics
from app.schemas.vocabulary import TermSlim

OWNER_ID = uuid.uuid4()
NOTE_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()
ASSET_ID = uuid.uuid4()
EVENT_ID = uuid.uuid4()
TAG_TERM_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.utcnow(),
)

IMPORTANT_TERM = TermSlim(id=TAG_TERM_ID, name="Important", slug="important")


def make_note(**kwargs) -> NotePublicRead:
    defaults = dict(
        id=NOTE_ID,
        owner_id=OWNER_ID,
        title="Meeting notes",
        body=None,
        pinned=False,
        person_id=None,
        asset_id=None,
        subscription_id=None,
        event_id=None,
        tags=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return NotePublicRead(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(notes_router, prefix="/api/v1")

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
    app.include_router(notes_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


# ── POST /notes/ ──────────────────────────────────────────────────────────────


def test_create_note_success(app_client):
    note = make_note()
    with patch("app.api.v1.notes.create_note", new=AsyncMock(return_value=note)):
        resp = app_client.post(
            "/api/v1/notes/", json={"title": "Meeting notes"}
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Meeting notes"
    assert body["owner_id"] == str(OWNER_ID)


def test_create_note_missing_title(app_client):
    resp = app_client.post("/api/v1/notes/", json={"body": "Some text"})
    assert resp.status_code == 422


def test_create_note_unauthenticated(unauthed_client):
    resp = unauthed_client.post("/api/v1/notes/", json={"title": "Secret"})
    assert resp.status_code in (401, 422, 500)


def test_create_note_with_all_fields(app_client):
    note = make_note(
        body="Detailed notes",
        pinned=True,
        person_id=PERSON_ID,
        tags=[IMPORTANT_TERM],
    )
    with patch("app.api.v1.notes.create_note", new=AsyncMock(return_value=note)):
        resp = app_client.post(
            "/api/v1/notes/",
            json={
                "title": "Meeting notes",
                "body": "Detailed notes",
                "pinned": True,
                "person_id": str(PERSON_ID),
                "tags": ["important"],
            },
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["body"] == "Detailed notes"
    assert body["pinned"] is True
    assert body["person_id"] == str(PERSON_ID)
    assert len(body["tags"]) == 1
    assert body["tags"][0]["slug"] == "important"


def test_create_note_with_event_id(app_client):
    note = make_note(event_id=EVENT_ID)
    with patch("app.api.v1.notes.create_note", new=AsyncMock(return_value=note)):
        resp = app_client.post(
            "/api/v1/notes/",
            json={"title": "Event note", "event_id": str(EVENT_ID)},
        )
    assert resp.status_code == 201
    assert resp.json()["event_id"] == str(EVENT_ID)


# ── GET /notes/ ───────────────────────────────────────────────────────────────


def test_list_notes_returns_list(app_client):
    notes = [make_note(), make_note(id=uuid.uuid4(), title="Other note")]
    with patch("app.api.v1.notes.list_notes", new=AsyncMock(return_value=(notes, 2))):
        resp = app_client.get("/api/v1/notes/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_notes_empty(app_client):
    with patch("app.api.v1.notes.list_notes", new=AsyncMock(return_value=([], 0))):
        resp = app_client.get("/api/v1/notes/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_notes_pinned_filter(app_client):
    with patch(
        "app.api.v1.notes.list_notes", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        resp = app_client.get("/api/v1/notes/?pinned=true")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["pinned"] is True


def test_list_notes_person_filter(app_client):
    with patch(
        "app.api.v1.notes.list_notes", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        resp = app_client.get(f"/api/v1/notes/?person_id={PERSON_ID}")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["person_id"] == PERSON_ID


def test_list_notes_asset_filter(app_client):
    with patch(
        "app.api.v1.notes.list_notes", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        resp = app_client.get(f"/api/v1/notes/?asset_id={ASSET_ID}")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["asset_id"] == ASSET_ID


def test_list_notes_search_filter(app_client):
    with patch(
        "app.api.v1.notes.list_notes", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        resp = app_client.get("/api/v1/notes/?q=meeting")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["q"] == "meeting"


def test_list_notes_no_search_filter(app_client):
    with patch(
        "app.api.v1.notes.list_notes", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        resp = app_client.get("/api/v1/notes/")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["q"] is None


def test_list_notes_event_filter(app_client):
    with patch(
        "app.api.v1.notes.list_notes", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        resp = app_client.get(f"/api/v1/notes/?event_id={EVENT_ID}")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["event_id"] == EVENT_ID


# ── GET /notes/statistics ─────────────────────────────────────────────────────


def test_get_note_statistics(app_client):
    stats = NoteStatistics(
        total=5,
        pinned=2,
        by_attachment={
            "person": 1,
            "asset": 1,
            "subscription": 0,
            "event": 0,
            "unlinked": 3,
        },
    )
    with patch(
        "app.api.v1.notes.get_note_statistics", new=AsyncMock(return_value=stats)
    ):
        resp = app_client.get("/api/v1/notes/statistics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert body["pinned"] == 2
    assert body["by_attachment"]["unlinked"] == 3
    assert body["by_attachment"]["person"] == 1


def test_get_note_statistics_empty(app_client):
    stats = NoteStatistics(
        total=0,
        pinned=0,
        by_attachment={
            "person": 0,
            "asset": 0,
            "subscription": 0,
            "event": 0,
            "unlinked": 0,
        },
    )
    with patch(
        "app.api.v1.notes.get_note_statistics", new=AsyncMock(return_value=stats)
    ):
        resp = app_client.get("/api/v1/notes/statistics")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


# ── GET /notes/{note_id} ──────────────────────────────────────────────────────


def test_get_note_found(app_client):
    note = make_note()
    with patch(
        "app.api.v1.notes.get_note_public", new=AsyncMock(return_value=note)
    ):
        resp = app_client.get(f"/api/v1/notes/{NOTE_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(NOTE_ID)


def test_get_note_not_found(app_client):
    with patch(
        "app.api.v1.notes.get_note_public", new=AsyncMock(return_value=None)
    ):
        resp = app_client.get(f"/api/v1/notes/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /notes/{note_id} ────────────────────────────────────────────────────


def test_patch_note_success(app_client):
    updated = make_note(title="Updated title", pinned=True)
    with patch(
        "app.api.v1.notes.update_note", new=AsyncMock(return_value=updated)
    ):
        resp = app_client.patch(
            f"/api/v1/notes/{NOTE_ID}",
            json={"title": "Updated title", "pinned": True},
        )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated title"
    assert resp.json()["pinned"] is True


def test_patch_note_not_found(app_client):
    with patch(
        "app.api.v1.notes.update_note", new=AsyncMock(return_value=None)
    ):
        resp = app_client.patch(
            f"/api/v1/notes/{uuid.uuid4()}", json={"title": "Ghost"}
        )
    assert resp.status_code == 404


# ── DELETE /notes/{note_id} ───────────────────────────────────────────────────


def test_delete_note_success(app_client):
    with patch(
        "app.api.v1.notes.soft_delete_note", new=AsyncMock(return_value=object())
    ):
        resp = app_client.delete(f"/api/v1/notes/{NOTE_ID}")
    assert resp.status_code == 204


def test_delete_note_not_found(app_client):
    with patch(
        "app.api.v1.notes.soft_delete_note", new=AsyncMock(return_value=None)
    ):
        resp = app_client.delete(f"/api/v1/notes/{uuid.uuid4()}")
    assert resp.status_code == 404
