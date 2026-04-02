import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.vocabularies import router as vocabularies_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.vocabulary import TermPublic, VocabularyPublic

OWNER_ID = uuid.uuid4()
VOCAB_ID = uuid.uuid4()
TERM_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.utcnow(),
)


def make_vocabulary(**kwargs) -> VocabularyPublic:
    defaults = dict(
        id=VOCAB_ID,
        name="Asset Categories",
        machine_name="asset-categories",
        description=None,
        is_hierarchical=False,
        allows_new_terms=True,
        is_locked=False,
        source_type="internal",
        external_provider=None,
        is_active=True,
        created_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return VocabularyPublic(**defaults)


def make_term(**kwargs) -> TermPublic:
    defaults = dict(
        id=TERM_ID,
        vocabulary_id=VOCAB_ID,
        name="Hardware",
        slug="hardware",
        description=None,
        parent_id=None,
        weight=0,
        external_id=None,
        is_active=True,
        created_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return TermPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(vocabularies_router, prefix="/api/v1")

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


# ── GET /vocabularies/ ────────────────────────────────────────────────────────


def test_list_vocabularies_returns_list(app_client):
    vocabs = [
        make_vocabulary(),
        make_vocabulary(
            id=uuid.uuid4(),
            name="Subscription Categories",
            machine_name="subscription-categories",
        ),
    ]
    with patch(
        "app.api.v1.vocabularies.list_vocabularies",
        new=AsyncMock(return_value=vocabs),
    ):
        resp = app_client.get("/api/v1/vocabularies/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_vocabularies_empty(app_client):
    with patch(
        "app.api.v1.vocabularies.list_vocabularies",
        new=AsyncMock(return_value=[]),
    ):
        resp = app_client.get("/api/v1/vocabularies/")
    assert resp.status_code == 200
    assert resp.json() == []


# ── POST /vocabularies/ ───────────────────────────────────────────────────────


def test_create_vocabulary_success(app_client):
    vocab = make_vocabulary()
    with patch(
        "app.api.v1.vocabularies.create_vocabulary",
        new=AsyncMock(return_value=vocab),
    ):
        resp = app_client.post(
            "/api/v1/vocabularies/",
            json={"name": "Asset Categories", "machine_name": "asset-categories"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Asset Categories"
    assert body["machine_name"] == "asset-categories"


def test_create_vocabulary_missing_required(app_client):
    # Missing machine_name
    resp = app_client.post("/api/v1/vocabularies/", json={"name": "Asset Categories"})
    assert resp.status_code == 422


def test_create_vocabulary_with_all_fields(app_client):
    vocab = make_vocabulary(
        description="Hardware and peripherals",
        is_hierarchical=True,
        source_type="internal",
    )
    with patch(
        "app.api.v1.vocabularies.create_vocabulary",
        new=AsyncMock(return_value=vocab),
    ):
        resp = app_client.post(
            "/api/v1/vocabularies/",
            json={
                "name": "Asset Categories",
                "machine_name": "asset-categories",
                "description": "Hardware and peripherals",
                "is_hierarchical": True,
            },
        )
    assert resp.status_code == 201
    assert resp.json()["is_hierarchical"] is True


# ── GET /vocabularies/{machine_name} ──────────────────────────────────────────


def test_get_vocabulary_found(app_client):
    vocab = make_vocabulary()
    with patch(
        "app.api.v1.vocabularies.get_vocabulary_by_machine_name",
        new=AsyncMock(return_value=vocab),
    ):
        resp = app_client.get("/api/v1/vocabularies/asset-categories")
    assert resp.status_code == 200
    assert resp.json()["machine_name"] == "asset-categories"


def test_get_vocabulary_not_found(app_client):
    with patch(
        "app.api.v1.vocabularies.get_vocabulary_by_machine_name",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.get("/api/v1/vocabularies/nonexistent")
    assert resp.status_code == 404


# ── PATCH /vocabularies/{machine_name} ────────────────────────────────────────


def test_patch_vocabulary_success(app_client):
    updated = make_vocabulary(name="Updated Name", description="New description")
    with patch(
        "app.api.v1.vocabularies.update_vocabulary",
        new=AsyncMock(return_value=updated),
    ):
        resp = app_client.patch(
            "/api/v1/vocabularies/asset-categories",
            json={"name": "Updated Name", "description": "New description"},
        )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


def test_patch_vocabulary_not_found(app_client):
    with patch(
        "app.api.v1.vocabularies.update_vocabulary",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.patch(
            "/api/v1/vocabularies/nonexistent",
            json={"name": "Ghost"},
        )
    assert resp.status_code == 404


# ── DELETE /vocabularies/{machine_name} ───────────────────────────────────────


def test_delete_vocabulary_success(app_client):
    with patch(
        "app.api.v1.vocabularies.delete_vocabulary",
        new=AsyncMock(return_value=True),
    ):
        resp = app_client.delete("/api/v1/vocabularies/asset-categories")
    assert resp.status_code == 204


def test_delete_vocabulary_not_found(app_client):
    with patch(
        "app.api.v1.vocabularies.delete_vocabulary",
        new=AsyncMock(return_value=False),
    ):
        resp = app_client.delete("/api/v1/vocabularies/nonexistent")
    assert resp.status_code == 404


# ── GET /vocabularies/{machine_name}/terms ────────────────────────────────────


def test_list_vocabulary_terms_returns_list(app_client):
    terms = [
        make_term(),
        make_term(id=uuid.uuid4(), name="Software", slug="software"),
    ]
    with patch("app.api.v1.vocabularies.list_terms", new=AsyncMock(return_value=terms)):
        resp = app_client.get("/api/v1/vocabularies/asset-categories/terms")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_vocabulary_terms_empty(app_client):
    with patch("app.api.v1.vocabularies.list_terms", new=AsyncMock(return_value=[])):
        resp = app_client.get("/api/v1/vocabularies/asset-categories/terms")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_vocabulary_terms_search_filter(app_client):
    with patch(
        "app.api.v1.vocabularies.list_terms", new=AsyncMock(return_value=[])
    ) as mock_list:
        resp = app_client.get("/api/v1/vocabularies/asset-categories/terms?search=hard")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["search"] == "hard"


# ── POST /vocabularies/{machine_name}/terms ───────────────────────────────────


def test_create_vocabulary_term_success(app_client):
    term = make_term()
    with patch("app.api.v1.vocabularies.create_term", new=AsyncMock(return_value=term)):
        resp = app_client.post(
            "/api/v1/vocabularies/asset-categories/terms",
            json={"name": "Hardware", "slug": "hardware"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Hardware"
    assert body["slug"] == "hardware"


def test_create_vocabulary_term_missing_required(app_client):
    # Missing slug
    resp = app_client.post(
        "/api/v1/vocabularies/asset-categories/terms",
        json={"name": "Hardware"},
    )
    assert resp.status_code == 422


# ── GET /vocabularies/{machine_name}/terms/{slug} ─────────────────────────────


def test_get_vocabulary_term_found(app_client):
    term = make_term()
    with patch(
        "app.api.v1.vocabularies.get_term_by_slug", new=AsyncMock(return_value=term)
    ):
        resp = app_client.get("/api/v1/vocabularies/asset-categories/terms/hardware")
    assert resp.status_code == 200
    assert resp.json()["slug"] == "hardware"


def test_get_vocabulary_term_not_found(app_client):
    with patch(
        "app.api.v1.vocabularies.get_term_by_slug",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.get("/api/v1/vocabularies/asset-categories/terms/nonexistent")
    assert resp.status_code == 404


# ── PATCH /vocabularies/{machine_name}/terms/{slug} ───────────────────────────


def test_patch_vocabulary_term_success(app_client):
    updated = make_term(name="Updated Hardware", description="Updated desc")
    with patch(
        "app.api.v1.vocabularies.update_term", new=AsyncMock(return_value=updated)
    ):
        resp = app_client.patch(
            "/api/v1/vocabularies/asset-categories/terms/hardware",
            json={"name": "Updated Hardware"},
        )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Hardware"


def test_patch_vocabulary_term_not_found(app_client):
    with patch("app.api.v1.vocabularies.update_term", new=AsyncMock(return_value=None)):
        resp = app_client.patch(
            "/api/v1/vocabularies/asset-categories/terms/nonexistent",
            json={"name": "Ghost"},
        )
    assert resp.status_code == 404


# ── DELETE /vocabularies/{machine_name}/terms/{slug} ──────────────────────────


def test_delete_vocabulary_term_success(app_client):
    with patch("app.api.v1.vocabularies.delete_term", new=AsyncMock(return_value=True)):
        resp = app_client.delete("/api/v1/vocabularies/asset-categories/terms/hardware")
    assert resp.status_code == 204


def test_delete_vocabulary_term_not_found(app_client):
    with patch(
        "app.api.v1.vocabularies.delete_term", new=AsyncMock(return_value=False)
    ):
        resp = app_client.delete(
            "/api/v1/vocabularies/asset-categories/terms/nonexistent"
        )
    assert resp.status_code == 404
