import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.persons import router as persons_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.reference import PersonTerm
from app.models.user import User

# Sentinel returned by get_person to signal "person exists"
FAKE_PERSON = MagicMock()

OWNER_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()
TERM_ID = uuid.uuid4()
PT_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.utcnow(),
)


def make_person_term(**kwargs) -> PersonTerm:
    defaults = dict(
        id=PT_ID,
        person_id=PERSON_ID,
        term_id=TERM_ID,
        context=None,
        created_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return PersonTerm(**defaults)


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

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ── POST /persons/{person_id}/terms ───────────────────────────────────────────


def test_add_person_term_success(app_client):
    pt = make_person_term()
    with (
        patch("app.api.v1.persons.get_person", new=AsyncMock(return_value=FAKE_PERSON)),
        patch("app.api.v1.persons.add_person_term", new=AsyncMock(return_value=pt)),
    ):
        resp = app_client.post(
            f"/api/v1/persons/{PERSON_ID}/terms",
            json={"term_id": str(TERM_ID)},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["term_id"] == str(TERM_ID)
    assert body["person_id"] == str(PERSON_ID)
    assert body["context"] is None


def test_add_person_term_with_context(app_client):
    pt = make_person_term(context="met at conference")
    with (
        patch("app.api.v1.persons.get_person", new=AsyncMock(return_value=FAKE_PERSON)),
        patch("app.api.v1.persons.add_person_term", new=AsyncMock(return_value=pt)),
    ):
        resp = app_client.post(
            f"/api/v1/persons/{PERSON_ID}/terms",
            json={"term_id": str(TERM_ID), "context": "met at conference"},
        )
    assert resp.status_code == 201
    assert resp.json()["context"] == "met at conference"


def test_add_person_term_missing_term_id(app_client):
    resp = app_client.post(
        f"/api/v1/persons/{PERSON_ID}/terms",
        json={},
    )
    assert resp.status_code == 422


def test_add_person_term_person_not_found(app_client):
    with patch("app.api.v1.persons.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.post(
            f"/api/v1/persons/{uuid.uuid4()}/terms",
            json={"term_id": str(TERM_ID)},
        )
    assert resp.status_code == 404


# ── GET /persons/{person_id}/terms ────────────────────────────────────────────


def test_list_person_terms(app_client):
    pts = [make_person_term(), make_person_term(id=uuid.uuid4(), term_id=uuid.uuid4())]
    with (
        patch("app.api.v1.persons.get_person", new=AsyncMock(return_value=FAKE_PERSON)),
        patch("app.api.v1.persons.list_person_terms", new=AsyncMock(return_value=pts)),
    ):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}/terms")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_person_terms_empty(app_client):
    with (
        patch("app.api.v1.persons.get_person", new=AsyncMock(return_value=FAKE_PERSON)),
        patch("app.api.v1.persons.list_person_terms", new=AsyncMock(return_value=[])),
    ):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}/terms")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_person_terms_person_not_found(app_client):
    with patch("app.api.v1.persons.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"/api/v1/persons/{uuid.uuid4()}/terms")
    assert resp.status_code == 404


# ── DELETE /persons/{person_id}/terms/{term_id} ───────────────────────────────


def test_remove_person_term_success(app_client):
    with (
        patch("app.api.v1.persons.get_person", new=AsyncMock(return_value=FAKE_PERSON)),
        patch(
            "app.api.v1.persons.remove_person_term", new=AsyncMock(return_value=True)
        ),
    ):
        resp = app_client.delete(f"/api/v1/persons/{PERSON_ID}/terms/{TERM_ID}")
    assert resp.status_code == 204


def test_remove_person_term_not_found(app_client):
    with (
        patch("app.api.v1.persons.get_person", new=AsyncMock(return_value=FAKE_PERSON)),
        patch(
            "app.api.v1.persons.remove_person_term", new=AsyncMock(return_value=False)
        ),
    ):
        resp = app_client.delete(f"/api/v1/persons/{PERSON_ID}/terms/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_remove_person_term_person_not_found(app_client):
    with patch("app.api.v1.persons.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.delete(f"/api/v1/persons/{uuid.uuid4()}/terms/{TERM_ID}")
    assert resp.status_code == 404
