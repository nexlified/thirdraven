import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.households import router as households_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.household import HouseholdMemberPublic, HouseholdPublic

OWNER_ID = uuid.uuid4()
MEMBER_ID = uuid.uuid4()
HH_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="alice",
    email="alice@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.utcnow(),
)

FAKE_ADMIN_MEMBER = HouseholdMemberPublic(
    id=uuid.uuid4(),
    user_id=OWNER_ID,
    username="alice",
    role="admin",
    joined_at=datetime.utcnow(),
)

FAKE_HH = HouseholdPublic(
    id=HH_ID,
    name="Smith Family",
    created_by=OWNER_ID,
    members=[FAKE_ADMIN_MEMBER],
    created_at=datetime.utcnow(),
)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(households_router, prefix="/api/v1")
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


# ── POST /households/ ─────────────────────────────────────────────────────────


def test_create_household_success(app_client):
    with patch(
        "app.api.v1.households.create_household", new=AsyncMock(return_value=FAKE_HH)
    ):
        resp = app_client.post("/api/v1/households/", json={"name": "Smith Family"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Smith Family"
    assert body["created_by"] == str(OWNER_ID)
    assert len(body["members"]) == 1
    assert body["members"][0]["role"] == "admin"


def test_create_household_missing_name(app_client):
    resp = app_client.post("/api/v1/households/", json={})
    assert resp.status_code == 422


# ── GET /households/me ────────────────────────────────────────────────────────


def test_get_my_household_success(app_client):
    with patch(
        "app.api.v1.households.get_my_household", new=AsyncMock(return_value=FAKE_HH)
    ):
        resp = app_client.get("/api/v1/households/me")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(HH_ID)


def test_get_my_household_not_in_one(app_client):
    with patch(
        "app.api.v1.households.get_my_household", new=AsyncMock(return_value=None)
    ):
        resp = app_client.get("/api/v1/households/me")
    assert resp.status_code == 404


# ── POST /households/{id}/members ─────────────────────────────────────────────


def test_invite_member_success(app_client):
    second_member = HouseholdMemberPublic(
        id=uuid.uuid4(),
        user_id=MEMBER_ID,
        username="bob",
        role="member",
        joined_at=datetime.utcnow(),
    )
    hh_with_two = HouseholdPublic(
        id=HH_ID,
        name="Smith Family",
        created_by=OWNER_ID,
        members=[FAKE_ADMIN_MEMBER, second_member],
        created_at=datetime.utcnow(),
    )
    with patch(
        "app.api.v1.households.invite_member",
        new=AsyncMock(return_value=hh_with_two),
    ):
        resp = app_client.post(
            f"/api/v1/households/{HH_ID}/members",
            json={"username": "bob"},
        )
    assert resp.status_code == 200
    assert len(resp.json()["members"]) == 2


# ── DELETE /households/{id}/members/{user_id} ─────────────────────────────────


def test_remove_member_success(app_client):
    with patch(
        "app.api.v1.households.remove_member", new=AsyncMock(return_value=FAKE_HH)
    ):
        resp = app_client.delete(
            f"/api/v1/households/{HH_ID}/members/{MEMBER_ID}"
        )
    assert resp.status_code == 200
    assert len(resp.json()["members"]) == 1


# ── DELETE /households/me/leave ───────────────────────────────────────────────


def test_leave_household_success(app_client):
    with patch(
        "app.api.v1.households.leave_household", new=AsyncMock(return_value=None)
    ):
        resp = app_client.delete("/api/v1/households/me/leave")
    assert resp.status_code == 204


# ── Schema validation: new fields on PersonSlim ───────────────────────────────


def test_person_slim_household_fields():
    from app.schemas.person import PersonSlim

    shared = PersonSlim(
        id=uuid.uuid4(),
        owner_id=MEMBER_ID,
        first_name="Bob",
        last_name=None,
        nickname=None,
        email=None,
        phone=None,
        notes=None,
        closeness_level=None,
        tags=[],
        visibility="household",
        household_id=HH_ID,
        is_placeholder=False,
        is_bot=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    assert shared.visibility == "household"
    assert shared.household_id == HH_ID


def test_person_slim_private_defaults():
    from app.schemas.person import PersonSlim

    private = PersonSlim(
        id=uuid.uuid4(),
        owner_id=OWNER_ID,
        first_name="Alice",
        last_name=None,
        nickname=None,
        email=None,
        phone=None,
        notes=None,
        closeness_level=None,
        tags=[],
        visibility="private",
        household_id=None,
        is_placeholder=False,
        is_bot=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    assert private.visibility == "private"
    assert private.household_id is None


# ── Schema validation: new fields on OrgPublic ────────────────────────────────


def test_org_public_household_fields():
    from app.schemas.organization import OrgPublic

    org = OrgPublic(
        id=uuid.uuid4(),
        owner_id=MEMBER_ID,
        name="ACME Corp",
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
        visibility="household",
        household_id=HH_ID,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    assert org.visibility == "household"
    assert org.household_id == HH_ID
