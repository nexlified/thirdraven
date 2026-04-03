import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.organizations import orgs_router, person_orgs_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.organization import OrgPublic, OrgSlim, PersonOrgPublic

OWNER_ID = uuid.uuid4()
ORG_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()
LINK_ID = uuid.uuid4()
HOUSEHOLD_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)

ORG_SLIM = OrgSlim(
    id=ORG_ID,
    name="Acme Corp",
    type=None,
    headquarters_city=None,
    country=None,
)


def make_org(**kwargs) -> OrgPublic:
    defaults = dict(
        id=ORG_ID,
        owner_id=OWNER_ID,
        name="Acme Corp",
        type=None,
        description=None,
        website=None,
        email=None,
        phone=None,
        industry=None,
        founded_year=None,
        headquarters_city=None,
        country=None,
        linkedin_url=None,
        notes=None,
        visibility="private",
        household_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return OrgPublic(**defaults)


def make_person_org(**kwargs) -> PersonOrgPublic:
    defaults = dict(
        id=LINK_ID,
        person_id=PERSON_ID,
        org=ORG_SLIM,
        role="Engineer",
        is_current=True,
        started_on=None,
        ended_on=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return PersonOrgPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(orgs_router, prefix="/api/v1")
    app.include_router(person_orgs_router, prefix="/api/v1")

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
    app.include_router(orgs_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


# ── POST /organizations/ ───────────────────────────────────────────────────────


def test_create_org_success(app_client):
    org = make_org()
    with (
        patch(
            "app.api.v1.organizations.get_user_household_id",
            new=AsyncMock(return_value=None),
        ),
        patch("app.api.v1.organizations.create_org", new=AsyncMock(return_value=org)),
    ):
        resp = app_client.post("/api/v1/organizations/", json={"name": "Acme Corp"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Acme Corp"


def test_create_org_missing_name(app_client):
    resp = app_client.post("/api/v1/organizations/", json={"description": "No name"})
    assert resp.status_code == 422


def test_create_org_with_all_fields(app_client):
    org = make_org(founded_year=2010, website="https://acme.com")
    with (
        patch(
            "app.api.v1.organizations.get_user_household_id",
            new=AsyncMock(return_value=HOUSEHOLD_ID),
        ),
        patch("app.api.v1.organizations.create_org", new=AsyncMock(return_value=org)),
    ):
        resp = app_client.post(
            "/api/v1/organizations/",
            json={
                "name": "Acme Corp",
                "founded_year": 2010,
                "website": "https://acme.com",
                "visibility": "household",
            },
        )
    assert resp.status_code == 201


def test_create_org_unauthenticated(unauthed_client):
    resp = unauthed_client.post("/api/v1/organizations/", json={"name": "Acme"})
    assert resp.status_code in (401, 422, 500)


# ── GET /organizations/ ────────────────────────────────────────────────────────


def test_list_orgs_returns_list(app_client):
    orgs = [make_org(), make_org(id=uuid.uuid4(), name="Beta Inc")]
    with (
        patch(
            "app.api.v1.organizations.get_user_household_id",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.api.v1.organizations.list_orgs", new=AsyncMock(return_value=(orgs, 2))
        ),
    ):
        resp = app_client.get("/api/v1/organizations/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_orgs_empty(app_client):
    with (
        patch(
            "app.api.v1.organizations.get_user_household_id",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.api.v1.organizations.list_orgs", new=AsyncMock(return_value=([], 0))
        ),
    ):
        resp = app_client.get("/api/v1/organizations/")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


# ── GET /organizations/{org_id} ────────────────────────────────────────────────


def test_get_org_found(app_client):
    org = make_org()
    with (
        patch(
            "app.api.v1.organizations.get_user_household_id",
            new=AsyncMock(return_value=None),
        ),
        patch("app.api.v1.organizations.get_org", new=AsyncMock(return_value=org)),
    ):
        resp = app_client.get(f"/api/v1/organizations/{ORG_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(ORG_ID)


def test_get_org_not_found(app_client):
    with (
        patch(
            "app.api.v1.organizations.get_user_household_id",
            new=AsyncMock(return_value=None),
        ),
        patch("app.api.v1.organizations.get_org", new=AsyncMock(return_value=None)),
    ):
        resp = app_client.get(f"/api/v1/organizations/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /organizations/{org_id} ──────────────────────────────────────────────


def test_patch_org_success(app_client):
    updated = make_org(name="Acme International")
    with (
        patch(
            "app.api.v1.organizations.get_user_household_id",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.api.v1.organizations.update_org", new=AsyncMock(return_value=updated)
        ),
    ):
        resp = app_client.patch(
            f"/api/v1/organizations/{ORG_ID}", json={"name": "Acme International"}
        )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Acme International"


def test_patch_org_not_found(app_client):
    with (
        patch(
            "app.api.v1.organizations.get_user_household_id",
            new=AsyncMock(return_value=None),
        ),
        patch("app.api.v1.organizations.update_org", new=AsyncMock(return_value=None)),
    ):
        resp = app_client.patch(
            f"/api/v1/organizations/{uuid.uuid4()}", json={"name": "Ghost"}
        )
    assert resp.status_code == 404


# ── DELETE /organizations/{org_id} ─────────────────────────────────────────────


def test_delete_org_success(app_client):
    with patch(
        "app.api.v1.organizations.soft_delete_org", new=AsyncMock(return_value=object())
    ):
        resp = app_client.delete(f"/api/v1/organizations/{ORG_ID}")
    assert resp.status_code == 204


def test_delete_org_not_found(app_client):
    with patch(
        "app.api.v1.organizations.soft_delete_org", new=AsyncMock(return_value=None)
    ):
        resp = app_client.delete(f"/api/v1/organizations/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── POST /persons/{person_id}/organizations/ ───────────────────────────────────


def test_link_person_org_success(app_client):
    link = make_person_org()
    with (
        patch(
            "app.api.v1.organizations.get_user_household_id",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.api.v1.organizations.get_person", new=AsyncMock(return_value=object())
        ),
        patch(
            "app.api.v1.organizations.link_person_org", new=AsyncMock(return_value=link)
        ),
    ):
        resp = app_client.post(
            f"/api/v1/persons/{PERSON_ID}/organizations/",
            json={"org_id": str(ORG_ID), "role": "Engineer"},
        )
    assert resp.status_code == 201
    assert resp.json()["role"] == "Engineer"


def test_link_person_org_person_not_found(app_client):
    with (
        patch(
            "app.api.v1.organizations.get_user_household_id",
            new=AsyncMock(return_value=None),
        ),
        patch("app.api.v1.organizations.get_person", new=AsyncMock(return_value=None)),
    ):
        resp = app_client.post(
            f"/api/v1/persons/{uuid.uuid4()}/organizations/",
            json={"org_id": str(ORG_ID)},
        )
    assert resp.status_code == 404


# ── GET /persons/{person_id}/organizations/ ────────────────────────────────────


def test_list_person_orgs(app_client):
    links = [make_person_org()]
    with (
        patch(
            "app.api.v1.organizations.get_user_household_id",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.api.v1.organizations.get_person", new=AsyncMock(return_value=object())
        ),
        patch(
            "app.api.v1.organizations.list_person_orgs",
            new=AsyncMock(return_value=links),
        ),
    ):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}/organizations/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_person_orgs_person_not_found(app_client):
    with (
        patch(
            "app.api.v1.organizations.get_user_household_id",
            new=AsyncMock(return_value=None),
        ),
        patch("app.api.v1.organizations.get_person", new=AsyncMock(return_value=None)),
    ):
        resp = app_client.get(f"/api/v1/persons/{uuid.uuid4()}/organizations/")
    assert resp.status_code == 404


# ── PATCH /persons/{person_id}/organizations/{link_id} ────────────────────────


def test_patch_person_org_link(app_client):
    updated = make_person_org(role="Senior Engineer", is_current=True)
    with patch(
        "app.api.v1.organizations.update_person_org",
        new=AsyncMock(return_value=updated),
    ):
        resp = app_client.patch(
            f"/api/v1/persons/{PERSON_ID}/organizations/{LINK_ID}",
            json={"role": "Senior Engineer"},
        )
    assert resp.status_code == 200
    assert resp.json()["role"] == "Senior Engineer"


def test_patch_person_org_link_not_found(app_client):
    with patch(
        "app.api.v1.organizations.update_person_org", new=AsyncMock(return_value=None)
    ):
        resp = app_client.patch(
            f"/api/v1/persons/{PERSON_ID}/organizations/{uuid.uuid4()}",
            json={"role": "X"},
        )
    assert resp.status_code == 404


# ── DELETE /persons/{person_id}/organizations/{link_id} ───────────────────────


def test_unlink_person_org_success(app_client):
    with patch(
        "app.api.v1.organizations.unlink_person_org",
        new=AsyncMock(return_value=object()),
    ):
        resp = app_client.delete(f"/api/v1/persons/{PERSON_ID}/organizations/{LINK_ID}")
    assert resp.status_code == 204


def test_unlink_person_org_not_found(app_client):
    with patch(
        "app.api.v1.organizations.unlink_person_org", new=AsyncMock(return_value=None)
    ):
        resp = app_client.delete(
            f"/api/v1/persons/{PERSON_ID}/organizations/{uuid.uuid4()}"
        )
    assert resp.status_code == 404
