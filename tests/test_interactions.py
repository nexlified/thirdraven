import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.interactions import router as interactions_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.interaction import Interaction
from app.models.person import Person
from app.models.user import User

OWNER_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()
INTERACTION_ID = uuid.uuid4()
TYPE_ITEM_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.utcnow(),
)


def make_person(**kwargs) -> Person:
    defaults = dict(
        id=PERSON_ID,
        owner_id=OWNER_ID,
        first_name="Alice",
        last_name=None,
        middle_name=None,
        nickname=None,
        prefix=None,
        email=None,
        phone=None,
        phone_secondary=None,
        date_of_birth=None,
        gender=None,
        nationality=None,
        languages=[],
        occupation=None,
        company=None,
        job_title=None,
        linkedin_url=None,
        twitter_handle=None,
        instagram_handle=None,
        website_url=None,
        address_home=None,
        address_work=None,
        city=None,
        country=None,
        timezone=None,
        how_we_met=None,
        first_met_on=None,
        closeness_level=None,
        notes=None,
        tags=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        deleted_at=None,
    )
    defaults.update(kwargs)
    return Person(**defaults)


def make_interaction(**kwargs) -> Interaction:
    defaults = dict(
        id=INTERACTION_ID,
        person_id=PERSON_ID,
        owner_id=OWNER_ID,
        interaction_type_id=None,
        reference_item_id=None,
        title="Coffee chat",
        occurred_on=None,
        notes=None,
        metadata_=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return Interaction(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(interactions_router, prefix="/api/v1")

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


BASE = f"/api/v1/persons/{PERSON_ID}/interactions"


# ── POST /persons/{person_id}/interactions/ ───────────────────────────────────


def test_log_interaction_success(app_client):
    person = make_person()
    interaction = make_interaction()
    with (
        patch("app.api.v1.interactions.get_person", new=AsyncMock(return_value=person)),
        patch(
            "app.api.v1.interactions.create_interaction",
            new=AsyncMock(return_value=interaction),
        ),
    ):
        resp = app_client.post(f"{BASE}/", json={"title": "Coffee chat"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Coffee chat"
    assert body["person_id"] == str(PERSON_ID)


def test_log_interaction_person_not_found(app_client):
    with patch("app.api.v1.interactions.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.post(f"{BASE}/", json={"title": "Ghost"})
    assert resp.status_code == 404


def test_log_interaction_missing_title(app_client):
    person = make_person()
    with patch(
        "app.api.v1.interactions.get_person", new=AsyncMock(return_value=person)
    ):
        resp = app_client.post(f"{BASE}/", json={})
    assert resp.status_code == 422


def test_log_interaction_with_full_fields(app_client):
    person = make_person()
    interaction = make_interaction(
        interaction_type_id=TYPE_ITEM_ID,
        occurred_on=date(2026, 3, 15),
        notes="Great chat",
        metadata_={"location": "cafe"},
    )
    with (
        patch("app.api.v1.interactions.get_person", new=AsyncMock(return_value=person)),
        patch(
            "app.api.v1.interactions.create_interaction",
            new=AsyncMock(return_value=interaction),
        ),
    ):
        resp = app_client.post(
            f"{BASE}/",
            json={
                "title": "Coffee chat",
                "interaction_type_id": str(TYPE_ITEM_ID),
                "occurred_on": "2026-03-15",
                "notes": "Great chat",
                "metadata_": {"location": "cafe"},
            },
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["notes"] == "Great chat"
    assert body["occurred_on"] == "2026-03-15"


# ── GET /persons/{person_id}/interactions/ ────────────────────────────────────


def test_list_interactions_success(app_client):
    person = make_person()
    interactions = [
        make_interaction(),
        make_interaction(id=uuid.uuid4(), title="Lunch"),
    ]
    with (
        patch("app.api.v1.interactions.get_person", new=AsyncMock(return_value=person)),
        patch(
            "app.api.v1.interactions.list_interactions",
            new=AsyncMock(return_value=(interactions, 2)),
        ),
    ):
        resp = app_client.get(f"{BASE}/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_interactions_empty(app_client):
    person = make_person()
    with (
        patch("app.api.v1.interactions.get_person", new=AsyncMock(return_value=person)),
        patch(
            "app.api.v1.interactions.list_interactions",
            new=AsyncMock(return_value=([], 0)),
        ),
    ):
        resp = app_client.get(f"{BASE}/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_interactions_person_not_found(app_client):
    with patch("app.api.v1.interactions.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"{BASE}/")
    assert resp.status_code == 404


# ── GET /persons/{person_id}/interactions/{interaction_id} ────────────────────


def test_get_interaction_found(app_client):
    interaction = make_interaction()
    with patch(
        "app.api.v1.interactions.get_interaction",
        new=AsyncMock(return_value=interaction),
    ):
        resp = app_client.get(f"{BASE}/{INTERACTION_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(INTERACTION_ID)


def test_get_interaction_not_found(app_client):
    with patch(
        "app.api.v1.interactions.get_interaction", new=AsyncMock(return_value=None)
    ):
        resp = app_client.get(f"{BASE}/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_get_interaction_wrong_person(app_client):
    # Interaction belongs to a different person — should 404
    other_person_id = uuid.uuid4()
    interaction = make_interaction(person_id=other_person_id)
    with patch(
        "app.api.v1.interactions.get_interaction",
        new=AsyncMock(return_value=interaction),
    ):
        resp = app_client.get(f"{BASE}/{INTERACTION_ID}")
    assert resp.status_code == 404


# ── PATCH /persons/{person_id}/interactions/{interaction_id} ──────────────────


def test_patch_interaction_success(app_client):
    updated = make_interaction(title="Updated chat", notes="New note")
    with patch(
        "app.api.v1.interactions.update_interaction",
        new=AsyncMock(return_value=updated),
    ):
        resp = app_client.patch(
            f"{BASE}/{INTERACTION_ID}",
            json={"title": "Updated chat", "notes": "New note"},
        )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated chat"


def test_patch_interaction_not_found(app_client):
    with patch(
        "app.api.v1.interactions.update_interaction",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.patch(f"{BASE}/{uuid.uuid4()}", json={"title": "Ghost"})
    assert resp.status_code == 404


# ── DELETE /persons/{person_id}/interactions/{interaction_id} ─────────────────


def test_delete_interaction_success(app_client):
    with patch(
        "app.api.v1.interactions.delete_interaction",
        new=AsyncMock(return_value=True),
    ):
        resp = app_client.delete(f"{BASE}/{INTERACTION_ID}")
    assert resp.status_code == 204


def test_delete_interaction_not_found(app_client):
    with patch(
        "app.api.v1.interactions.delete_interaction",
        new=AsyncMock(return_value=False),
    ):
        resp = app_client.delete(f"{BASE}/{uuid.uuid4()}")
    assert resp.status_code == 404
