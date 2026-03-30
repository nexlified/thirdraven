import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.relationships import router as relationships_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.person import RelatedPersonRef, RelationshipPublic
from app.schemas.vocabulary import TermSlim

OWNER_ID = uuid.uuid4()
REL_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()
OTHER_ID = uuid.uuid4()
TERM_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.utcnow(),
)


def make_relationship(**kwargs) -> RelationshipPublic:
    defaults = dict(
        id=REL_ID,
        person=RelatedPersonRef(
            id=PERSON_ID,
            first_name="Alice",
            last_name="Smith",
            nickname=None,
        ),
        related_person=RelatedPersonRef(
            id=OTHER_ID,
            first_name="Bob",
            last_name="Jones",
            nickname=None,
        ),
        label=TermSlim(id=TERM_ID, name="Friend", slug="friend"),
        inverse_id=None,
        created_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return RelationshipPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(relationships_router, prefix="/api/v1")
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


# ── GET /relationships/{rel_id} ─────────────────────────────────────────────────


def test_get_relationship_found(app_client):
    rel = make_relationship()
    with patch(
        "app.api.v1.relationships.get_relationship",
        new=AsyncMock(return_value=rel),
    ):
        resp = app_client.get(f"/api/v1/relationships/{REL_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(REL_ID)
    assert body["person"]["first_name"] == "Alice"
    assert body["related_person"]["first_name"] == "Bob"
    assert body["label"]["slug"] == "friend"


def test_get_relationship_not_found(app_client):
    with patch(
        "app.api.v1.relationships.get_relationship",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.get(f"/api/v1/relationships/{REL_ID}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Relationship not found"


# ── PATCH /relationships/{rel_id} ──────────────────────────────────────────────


def test_patch_relationship_success(app_client):
    updated_term = TermSlim(id=uuid.uuid4(), name="Colleague", slug="colleague")
    rel = make_relationship(label=updated_term)
    with patch(
        "app.api.v1.relationships.update_relationship",
        new=AsyncMock(return_value=rel),
    ):
        resp = app_client.patch(
            f"/api/v1/relationships/{REL_ID}",
            json={"label": "colleague"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(REL_ID)
    assert body["label"]["slug"] == "colleague"


def test_patch_relationship_not_found(app_client):
    with patch(
        "app.api.v1.relationships.update_relationship",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.patch(
            f"/api/v1/relationships/{REL_ID}",
            json={"label": "colleague"},
        )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Relationship not found"


# ── DELETE /relationships/{rel_id} ─────────────────────────────────────────────


def test_delete_relationship_success(app_client):
    with patch(
        "app.api.v1.relationships.delete_relationship",
        new=AsyncMock(return_value=True),
    ):
        resp = app_client.delete(f"/api/v1/relationships/{REL_ID}")
    assert resp.status_code == 204
    assert resp.content == b""


def test_delete_relationship_not_found(app_client):
    with patch(
        "app.api.v1.relationships.delete_relationship",
        new=AsyncMock(return_value=False),
    ):
        resp = app_client.delete(f"/api/v1/relationships/{REL_ID}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Relationship not found"
