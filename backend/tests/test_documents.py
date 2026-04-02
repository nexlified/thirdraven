import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.documents import router as documents_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.document import DocumentPublic
from app.schemas.vocabulary import TermSlim

OWNER_ID = uuid.uuid4()
DOC_ID = uuid.uuid4()
ENTITY_ID = uuid.uuid4()
TERM_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.utcnow(),
)

PASSPORT_DOC_TERM = TermSlim(id=TERM_ID, name="Passport Scan", slug="passport-scan")


def make_document(**kwargs) -> DocumentPublic:
    defaults = dict(
        id=DOC_ID,
        owner_id=OWNER_ID,
        entity_type="person",
        entity_id=ENTITY_ID,
        doc_type=PASSPORT_DOC_TERM,
        title="Passport Copy",
        file_path=None,
        file_name=None,
        file_size=None,
        mime_type=None,
        issued_on=None,
        expires_on=None,
        notes=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return DocumentPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(documents_router, prefix="/api/v1")

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
    app.include_router(documents_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


# ── POST /documents/ ───────────────────────────────────────────────────────────


def test_create_document_success(app_client):
    doc = make_document()
    with patch("app.api.v1.documents.create_document", new=AsyncMock(return_value=doc)):
        resp = app_client.post(
            "/api/v1/documents/",
            json={
                "entity_type": "person",
                "doc_type": "passport-scan",
                "title": "Passport Copy",
            },
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Passport Copy"
    assert body["owner_id"] == str(OWNER_ID)
    assert body["doc_type"]["slug"] == "passport-scan"


def test_create_document_missing_entity_type_returns_422(app_client):
    resp = app_client.post(
        "/api/v1/documents/",
        json={"doc_type": "passport-scan", "title": "Passport Copy"},
    )
    assert resp.status_code == 422


def test_create_document_missing_doc_type_returns_422(app_client):
    resp = app_client.post(
        "/api/v1/documents/",
        json={"entity_type": "person", "title": "Passport Copy"},
    )
    assert resp.status_code == 422


def test_create_document_missing_title_returns_422(app_client):
    resp = app_client.post(
        "/api/v1/documents/",
        json={"entity_type": "person", "doc_type": "passport-scan"},
    )
    assert resp.status_code == 422


def test_create_document_unauthenticated(unauthed_client):
    resp = unauthed_client.post(
        "/api/v1/documents/",
        json={
            "entity_type": "person",
            "doc_type": "passport-scan",
            "title": "Passport Copy",
        },
    )
    assert resp.status_code in (401, 422, 500)


# ── GET /documents/ ────────────────────────────────────────────────────────────


def test_list_documents_returns_list(app_client):
    docs = [make_document(), make_document(id=uuid.uuid4(), title="Insurance Card")]
    with patch(
        "app.api.v1.documents.list_documents", new=AsyncMock(return_value=(docs, 2))
    ):
        resp = app_client.get("/api/v1/documents/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_documents_empty(app_client):
    with patch(
        "app.api.v1.documents.list_documents", new=AsyncMock(return_value=([], 0))
    ):
        resp = app_client.get("/api/v1/documents/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_documents_passes_entity_type_filter(app_client):
    mock_fn = AsyncMock(return_value=([], 0))
    with patch("app.api.v1.documents.list_documents", new=mock_fn):
        app_client.get("/api/v1/documents/?entity_type=asset")
    kwargs = mock_fn.call_args.kwargs
    assert kwargs["entity_type"] == "asset"


def test_list_documents_passes_entity_id_filter(app_client):
    mock_fn = AsyncMock(return_value=([], 0))
    with patch("app.api.v1.documents.list_documents", new=mock_fn):
        app_client.get(f"/api/v1/documents/?entity_id={ENTITY_ID}")
    kwargs = mock_fn.call_args.kwargs
    assert kwargs["entity_id"] == ENTITY_ID


# ── GET /documents/{doc_id} ────────────────────────────────────────────────────


def test_get_document_found(app_client):
    doc = make_document()
    with patch("app.api.v1.documents.get_document", new=AsyncMock(return_value=doc)):
        resp = app_client.get(f"/api/v1/documents/{DOC_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(DOC_ID)


def test_get_document_not_found(app_client):
    with patch("app.api.v1.documents.get_document", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"/api/v1/documents/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /documents/{doc_id} ──────────────────────────────────────────────────


def test_patch_document_success(app_client):
    updated = make_document(title="Updated Passport", notes="Renewed 2026")
    with patch(
        "app.api.v1.documents.update_document", new=AsyncMock(return_value=updated)
    ):
        resp = app_client.patch(
            f"/api/v1/documents/{DOC_ID}",
            json={"title": "Updated Passport", "notes": "Renewed 2026"},
        )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Passport"
    assert resp.json()["notes"] == "Renewed 2026"


def test_patch_document_not_found(app_client):
    with patch(
        "app.api.v1.documents.update_document", new=AsyncMock(return_value=None)
    ):
        resp = app_client.patch(
            f"/api/v1/documents/{uuid.uuid4()}", json={"title": "Ghost"}
        )
    assert resp.status_code == 404


# ── DELETE /documents/{doc_id} ─────────────────────────────────────────────────


def test_delete_document_success(app_client):
    with patch(
        "app.api.v1.documents.delete_document", new=AsyncMock(return_value=object())
    ):
        resp = app_client.delete(f"/api/v1/documents/{DOC_ID}")
    assert resp.status_code == 204


def test_delete_document_not_found(app_client):
    with patch(
        "app.api.v1.documents.delete_document", new=AsyncMock(return_value=None)
    ):
        resp = app_client.delete(f"/api/v1/documents/{uuid.uuid4()}")
    assert resp.status_code == 404
