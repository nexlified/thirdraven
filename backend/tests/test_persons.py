import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.persons import router as persons_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.person import Person
from app.models.user import User
from app.schemas.person import (
    PersonExtended,
    PersonProfessionalSection,
    PersonSlim,
    RelatedPersonRef,
    RelationshipPublic,
)
from app.schemas.vocabulary import TermSlim

OWNER_ID = uuid.uuid4()
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


def make_person(**kwargs) -> PersonSlim:
    """Return a PersonSlim Pydantic object with sensible defaults."""
    defaults = dict(
        id=PERSON_ID,
        owner_id=OWNER_ID,
        first_name="Alice",
        last_name="Smith",
        nickname=None,
        email="alice@example.com",
        phone=None,
        closeness_level=None,
        notes=None,
        tags=[],
        visibility="private",
        household_id=None,
        is_placeholder=False,
        is_bot=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return PersonSlim(**defaults)


def make_person_extended(**kwargs) -> PersonExtended:
    """Return a PersonExtended with optional sections."""
    section_keys = {
        "profile",
        "professional",
        "location",
        "context",
        "physical",
        "personality",
        "channels",
    }
    slim_kwargs = {k: v for k, v in kwargs.items() if k not in section_keys}
    section_kwargs = {k: v for k, v in kwargs.items() if k in section_keys}
    slim = make_person(**slim_kwargs)
    return PersonExtended(**slim.model_dump(), **section_kwargs)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(persons_router, prefix="/api/v1")

    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    async def override_get_current_user():
        return FAKE_USER

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    with (
        patch(
            "app.api.v1.persons.get_user_household_id",
            new=AsyncMock(return_value=None),
        ),
        TestClient(app) as client,
    ):
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client():
    app = FastAPI()
    app.include_router(persons_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


# ── POST /persons/ ─────────────────────────────────────────────────────────────


def test_create_person_success(app_client):
    person = make_person()
    with patch("app.api.v1.persons.create_person", new=AsyncMock(return_value=person)):
        resp = app_client.post("/api/v1/persons/", json={"first_name": "Alice"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["first_name"] == "Alice"
    assert body["owner_id"] == str(OWNER_ID)


def test_create_person_missing_first_name(app_client):
    resp = app_client.post("/api/v1/persons/", json={"last_name": "Smith"})
    assert resp.status_code == 422


def test_create_person_unauthenticated(unauthed_client):
    resp = unauthed_client.post("/api/v1/persons/", json={"first_name": "Alice"})
    assert resp.status_code in (401, 422, 500)


def test_create_person_with_extension_fields(app_client):
    """POST accepts extension fields in the flat body; response is slim (core only)."""
    person = make_person(closeness_level=4)
    with patch("app.api.v1.persons.create_person", new=AsyncMock(return_value=person)):
        resp = app_client.post(
            "/api/v1/persons/",
            json={
                "first_name": "Alice",
                "company": "Acme Corp",
                "job_title": "Engineer",
                "city": "Berlin",
                "country": "DE",
                "closeness_level": 4,
                "languages": ["en", "de"],
            },
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["first_name"] == "Alice"
    assert body["closeness_level"] == 4
    # Extension fields are not in the slim response
    assert "company" not in body
    assert "city" not in body


# ── GET /persons/ ──────────────────────────────────────────────────────────────


def test_list_persons_returns_list(app_client):
    persons = [make_person(), make_person(id=uuid.uuid4(), first_name="Bob")]
    with patch(
        "app.api.v1.persons.list_persons",
        new=AsyncMock(return_value=(persons, 2)),
    ):
        resp = app_client.get("/api/v1/persons/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_persons_empty(app_client):
    with patch("app.api.v1.persons.list_persons", new=AsyncMock(return_value=([], 0))):
        resp = app_client.get("/api/v1/persons/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


# ── GET /persons/{person_id} ───────────────────────────────────────────────────


def test_get_person_found(app_client):
    person = make_person_extended()
    with (
        patch("app.api.v1.persons.get_person", new=AsyncMock(return_value=person)),
        patch(
            "app.api.v1.persons.list_relationships_for_person",
            new=AsyncMock(return_value=([], 0)),
        ),
    ):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(PERSON_ID)
    assert body["relationships"] == []
    # Slim response — no extension sections when not included
    assert body["professional"] is None
    assert body["profile"] is None


def test_get_person_with_relationships(app_client):
    person = make_person_extended()
    REL_ID = uuid.uuid4()
    rel = RelationshipPublic(
        id=REL_ID,
        person=RelatedPersonRef(
            id=PERSON_ID, first_name="Alice", last_name="Smith", nickname=None
        ),
        related_person=RelatedPersonRef(
            id=OTHER_ID, first_name="Bob", last_name=None, nickname=None
        ),
        label=TermSlim(id=TERM_ID, name="Colleague", slug="colleague"),
        inverse_id=None,
        created_at=datetime.utcnow(),
    )
    with (
        patch("app.api.v1.persons.get_person", new=AsyncMock(return_value=person)),
        patch(
            "app.api.v1.persons.list_relationships_for_person",
            new=AsyncMock(return_value=([rel], 1)),
        ),
    ):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["relationships"]) == 1
    assert body["relationships"][0]["label"]["slug"] == "colleague"


def test_get_person_not_found(app_client):
    with patch("app.api.v1.persons.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"/api/v1/persons/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_get_person_with_include_professional(app_client):
    """?include=professional populates the professional nested object."""
    person = make_person_extended(
        professional=PersonProfessionalSection(
            company="Acme Corp", job_title="Engineer"
        )
    )
    with (
        patch("app.api.v1.persons.get_person", new=AsyncMock(return_value=person)),
        patch(
            "app.api.v1.persons.list_relationships_for_person",
            new=AsyncMock(return_value=([], 0)),
        ),
    ):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}?include=professional")
    assert resp.status_code == 200
    body = resp.json()
    assert body["professional"]["company"] == "Acme Corp"
    assert body["professional"]["job_title"] == "Engineer"
    assert body["profile"] is None


# ── PATCH /persons/{person_id} ─────────────────────────────────────────────────


def test_patch_person_success(app_client):
    updated = make_person(nickname="Ali", closeness_level=5)
    with patch("app.api.v1.persons.update_person", new=AsyncMock(return_value=updated)):
        resp = app_client.patch(
            f"/api/v1/persons/{PERSON_ID}",
            json={"nickname": "Ali", "closeness_level": 5},
        )
    assert resp.status_code == 200
    assert resp.json()["nickname"] == "Ali"
    assert resp.json()["closeness_level"] == 5


def test_patch_person_not_found(app_client):
    with patch("app.api.v1.persons.update_person", new=AsyncMock(return_value=None)):
        resp = app_client.patch(
            f"/api/v1/persons/{uuid.uuid4()}", json={"first_name": "Ghost"}
        )
    assert resp.status_code == 404


# ── DELETE /persons/{person_id} ────────────────────────────────────────────────


def test_delete_person_success(app_client):
    person = Person(
        id=PERSON_ID,
        owner_id=OWNER_ID,
        first_name="Alice",
        deleted_at=datetime.utcnow(),
    )
    with patch(
        "app.api.v1.persons.soft_delete_person", new=AsyncMock(return_value=person)
    ):
        resp = app_client.delete(f"/api/v1/persons/{PERSON_ID}")
    assert resp.status_code == 204


def test_delete_person_not_found(app_client):
    with patch(
        "app.api.v1.persons.soft_delete_person", new=AsyncMock(return_value=None)
    ):
        resp = app_client.delete(f"/api/v1/persons/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── POST /persons/{person_id}/relationships ────────────────────────────────────


def test_create_relationship_success(app_client):
    person = make_person_extended()
    target = make_person_extended(id=OTHER_ID, first_name="Bob")
    rel = RelationshipPublic(
        id=uuid.uuid4(),
        person=RelatedPersonRef(
            id=PERSON_ID, first_name="Alice", last_name="Smith", nickname=None
        ),
        related_person=RelatedPersonRef(
            id=OTHER_ID, first_name="Bob", last_name=None, nickname=None
        ),
        label=TermSlim(id=TERM_ID, name="Colleague", slug="colleague"),
        inverse_id=None,
        created_at=datetime.utcnow(),
    )
    with (
        patch(
            "app.api.v1.persons.get_person",
            new=AsyncMock(side_effect=[person, target]),
        ),
        patch("app.api.v1.persons.add_relationship", new=AsyncMock(return_value=rel)),
    ):
        resp = app_client.post(
            f"/api/v1/persons/{PERSON_ID}/relationships",
            json={"to_person_id": str(OTHER_ID), "label": "colleague"},
        )
    assert resp.status_code == 201
    assert resp.json()["label"]["slug"] == "colleague"


def test_create_relationship_source_not_found(app_client):
    with patch("app.api.v1.persons.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.post(
            f"/api/v1/persons/{PERSON_ID}/relationships",
            json={"to_person_id": str(OTHER_ID), "label": "friend"},
        )
    assert resp.status_code == 404


# ── GET /persons/schema ───────────────────────────────────────────────────────


def test_get_person_schema(app_client):
    with patch(
        "app.api.v1.persons.list_vocab_terms",
        new=AsyncMock(return_value=[]),
    ):
        resp = app_client.get("/api/v1/persons/schema")
    assert resp.status_code == 200
    data = resp.json()
    for key in (
        "prefixes",
        "genders",
        "occupations",
        "tags",
        "relationship_types",
        "preferred_contact",
        "address_types",
        "channel_types",
    ):
        assert key in data
        assert isinstance(data[key], list)
    assert "home" in data["address_types"]
    assert "email" in data["channel_types"]
    assert "discord" in data["channel_types"]
