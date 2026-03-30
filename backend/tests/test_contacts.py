import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.contacts import router as contacts_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.relationship import ContactRelationship
from app.models.user import User
from app.schemas.contact import ContactPublicRead

OWNER_ID = uuid.uuid4()
CONTACT_ID = uuid.uuid4()
OTHER_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.utcnow(),
)


def make_contact(**kwargs) -> ContactPublicRead:
    defaults = dict(
        id=CONTACT_ID,
        owner_id=OWNER_ID,
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
        phone=None,
        notes=None,
        tags=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return ContactPublicRead(**defaults)


def make_relationship(**kwargs) -> ContactRelationship:
    defaults = dict(
        id=uuid.uuid4(),
        from_contact_id=CONTACT_ID,
        to_contact_id=OTHER_ID,
        label="friend",
        created_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return ContactRelationship(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(contacts_router, prefix="/api/v1")

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
    app.include_router(contacts_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


# ── POST /contacts/ ────────────────────────────────────────────────────────────


def test_create_contact_success(app_client):
    contact = make_contact()
    with patch(
        "app.api.v1.contacts.create_contact", new=AsyncMock(return_value=contact)
    ):
        resp = app_client.post(
            "/api/v1/contacts/", json={"first_name": "Alice"}
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["first_name"] == "Alice"
    assert body["owner_id"] == str(OWNER_ID)


def test_create_contact_missing_first_name(app_client):
    resp = app_client.post("/api/v1/contacts/", json={"last_name": "Smith"})
    assert resp.status_code == 422


def test_create_contact_unauthenticated(unauthed_client):
    resp = unauthed_client.post(
        "/api/v1/contacts/", json={"first_name": "Alice"}
    )
    assert resp.status_code in (401, 422, 500)


def test_create_contact_with_optional_fields(app_client):
    contact = make_contact(
        last_name="Smith",
        email="alice@example.com",
        phone="+1234567890",
        notes="Met at conference",
    )
    with patch(
        "app.api.v1.contacts.create_contact", new=AsyncMock(return_value=contact)
    ):
        resp = app_client.post(
            "/api/v1/contacts/",
            json={
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "alice@example.com",
                "phone": "+1234567890",
                "notes": "Met at conference",
            },
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["last_name"] == "Smith"
    assert body["email"] == "alice@example.com"


# ── GET /contacts/ ─────────────────────────────────────────────────────────────


def test_list_contacts_returns_list(app_client):
    contacts = [make_contact(), make_contact(id=uuid.uuid4(), first_name="Bob")]
    with patch(
        "app.api.v1.contacts.list_contacts", new=AsyncMock(return_value=(contacts, 2))
    ):
        resp = app_client.get("/api/v1/contacts/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_contacts_empty(app_client):
    with patch(
        "app.api.v1.contacts.list_contacts", new=AsyncMock(return_value=([], 0))
    ):
        resp = app_client.get("/api/v1/contacts/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_contacts_pagination_params(app_client):
    with patch(
        "app.api.v1.contacts.list_contacts", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        resp = app_client.get("/api/v1/contacts/?skip=10&limit=5")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["skip"] == 10
    assert call_kwargs["limit"] == 5


# ── GET /contacts/{contact_id} ─────────────────────────────────────────────────


def test_get_contact_found(app_client):
    contact = make_contact()
    with (
        patch(
            "app.api.v1.contacts.get_contact", new=AsyncMock(return_value=contact)
        ),
        patch(
            "app.api.v1.contacts.get_relationships_for_contact",
            new=AsyncMock(return_value=[]),
        ),
    ):
        resp = app_client.get(f"/api/v1/contacts/{CONTACT_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(CONTACT_ID)
    assert body["relationships"] == []


def test_get_contact_with_relationships(app_client):
    contact = make_contact()
    rel = make_relationship()
    with (
        patch(
            "app.api.v1.contacts.get_contact", new=AsyncMock(return_value=contact)
        ),
        patch(
            "app.api.v1.contacts.get_relationships_for_contact",
            new=AsyncMock(return_value=[rel]),
        ),
    ):
        resp = app_client.get(f"/api/v1/contacts/{CONTACT_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["relationships"]) == 1
    assert body["relationships"][0]["label"] == "friend"


def test_get_contact_not_found(app_client):
    with patch("app.api.v1.contacts.get_contact", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"/api/v1/contacts/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /contacts/{contact_id} ───────────────────────────────────────────────


def test_patch_contact_success(app_client):
    updated = make_contact(first_name="Alicia", phone="+9876543210")
    with patch(
        "app.api.v1.contacts.update_contact", new=AsyncMock(return_value=updated)
    ):
        resp = app_client.patch(
            f"/api/v1/contacts/{CONTACT_ID}",
            json={"first_name": "Alicia", "phone": "+9876543210"},
        )
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Alicia"
    assert resp.json()["phone"] == "+9876543210"


def test_patch_contact_not_found(app_client):
    with patch(
        "app.api.v1.contacts.update_contact", new=AsyncMock(return_value=None)
    ):
        resp = app_client.patch(
            f"/api/v1/contacts/{uuid.uuid4()}", json={"first_name": "Ghost"}
        )
    assert resp.status_code == 404


# ── DELETE /contacts/{contact_id} ──────────────────────────────────────────────


def test_delete_contact_success(app_client):
    contact = make_contact()
    with patch(
        "app.api.v1.contacts.soft_delete_contact",
        new=AsyncMock(return_value=contact),
    ):
        resp = app_client.delete(f"/api/v1/contacts/{CONTACT_ID}")
    assert resp.status_code == 204


def test_delete_contact_not_found(app_client):
    with patch(
        "app.api.v1.contacts.soft_delete_contact",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.delete(f"/api/v1/contacts/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── POST /contacts/{contact_id}/relationships ──────────────────────────────────


def test_create_contact_relationship_success(app_client):
    contact = make_contact()
    target = make_contact(id=OTHER_ID, first_name="Bob")
    rel = make_relationship()
    with (
        patch(
            "app.api.v1.contacts.get_contact",
            new=AsyncMock(side_effect=[contact, target]),
        ),
        patch(
            "app.api.v1.contacts.add_relationship",
            new=AsyncMock(return_value=rel),
        ),
    ):
        resp = app_client.post(
            f"/api/v1/contacts/{CONTACT_ID}/relationships",
            json={"to_contact_id": str(OTHER_ID), "label": "friend"},
        )
    assert resp.status_code == 201
    assert resp.json()["label"] == "friend"
    assert resp.json()["from_contact_id"] == str(CONTACT_ID)


def test_create_contact_relationship_source_not_found(app_client):
    with patch("app.api.v1.contacts.get_contact", new=AsyncMock(return_value=None)):
        resp = app_client.post(
            f"/api/v1/contacts/{CONTACT_ID}/relationships",
            json={"to_contact_id": str(OTHER_ID), "label": "friend"},
        )
    assert resp.status_code == 404


def test_create_contact_relationship_target_not_found(app_client):
    contact = make_contact()
    with patch(
        "app.api.v1.contacts.get_contact",
        new=AsyncMock(side_effect=[contact, None]),
    ):
        resp = app_client.post(
            f"/api/v1/contacts/{CONTACT_ID}/relationships",
            json={"to_contact_id": str(uuid.uuid4()), "label": "colleague"},
        )
    assert resp.status_code == 404


def test_create_contact_relationship_missing_label(app_client):
    resp = app_client.post(
        f"/api/v1/contacts/{CONTACT_ID}/relationships",
        json={"to_contact_id": str(OTHER_ID)},
    )
    assert resp.status_code == 422
