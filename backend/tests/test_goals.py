import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.goals import router as goals_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.goal import GoalPublic

OWNER_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()
GOAL_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)


def make_goal(**kwargs) -> GoalPublic:
    defaults = dict(
        id=GOAL_ID,
        person_id=PERSON_ID,
        owner_id=OWNER_ID,
        goal_type="aspiration",
        body="Run a marathon",
        target_date=None,
        achieved_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return GoalPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(goals_router, prefix="/api/v1")

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


# ── POST /persons/{person_id}/goals/ ──────────────────────────────────────────


def test_create_goal_success(app_client):
    goal = make_goal()
    with (
        patch("app.api.v1.goals.get_person", new=AsyncMock(return_value=object())),
        patch("app.api.v1.goals.create_goal", new=AsyncMock(return_value=goal)),
    ):
        resp = app_client.post(
            f"/api/v1/persons/{PERSON_ID}/goals/",
            json={"goal_type": "aspiration", "body": "Run a marathon"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["goal_type"] == "aspiration"
    assert body["body"] == "Run a marathon"
    assert body["achieved_at"] is None


def test_create_goal_person_not_found(app_client):
    with patch("app.api.v1.goals.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.post(
            f"/api/v1/persons/{uuid.uuid4()}/goals/",
            json={"goal_type": "aspiration", "body": "Test"},
        )
    assert resp.status_code == 404


def test_create_goal_missing_required_fields(app_client):
    with patch("app.api.v1.goals.get_person", new=AsyncMock(return_value=object())):
        # Missing goal_type and body
        resp = app_client.post(
            f"/api/v1/persons/{PERSON_ID}/goals/", json={"target_date": "2026-01-01"}
        )
    assert resp.status_code == 422


def test_create_goal_with_target_date(app_client):
    goal = make_goal(target_date=date(2026, 12, 31))
    with (
        patch("app.api.v1.goals.get_person", new=AsyncMock(return_value=object())),
        patch("app.api.v1.goals.create_goal", new=AsyncMock(return_value=goal)),
    ):
        resp = app_client.post(
            f"/api/v1/persons/{PERSON_ID}/goals/",
            json={
                "goal_type": "current-focus",
                "body": "Ship new feature",
                "target_date": "2026-12-31",
            },
        )
    assert resp.status_code == 201
    assert resp.json()["target_date"] == "2026-12-31"


# ── GET /persons/{person_id}/goals/ ────────────────────────────────────────────


def test_list_goals_returns_list(app_client):
    goals = [make_goal(), make_goal(id=uuid.uuid4(), body="Learn piano")]
    with (
        patch("app.api.v1.goals.get_person", new=AsyncMock(return_value=object())),
        patch("app.api.v1.goals.list_goals", new=AsyncMock(return_value=(goals, 2))),
    ):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}/goals/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_goals_person_not_found(app_client):
    with patch("app.api.v1.goals.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"/api/v1/persons/{uuid.uuid4()}/goals/")
    assert resp.status_code == 404


def test_list_goals_active_only_filter(app_client):
    with (
        patch("app.api.v1.goals.get_person", new=AsyncMock(return_value=object())),
        patch("app.api.v1.goals.list_goals", new=AsyncMock(return_value=([], 0))) as mock_list,
    ):
        app_client.get(f"/api/v1/persons/{PERSON_ID}/goals/?active_only=true")
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["active_only"] is True


# ── GET /persons/{person_id}/goals/{goal_id} ──────────────────────────────────


def test_get_goal_found(app_client):
    goal = make_goal()
    with patch("app.api.v1.goals.get_goal", new=AsyncMock(return_value=goal)):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}/goals/{GOAL_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(GOAL_ID)


def test_get_goal_not_found(app_client):
    with patch("app.api.v1.goals.get_goal", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}/goals/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_get_goal_wrong_person(app_client):
    # Goal belongs to different person — router checks goal.person_id != person_id
    wrong_person_goal = make_goal(person_id=uuid.uuid4())
    with patch("app.api.v1.goals.get_goal", new=AsyncMock(return_value=wrong_person_goal)):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}/goals/{GOAL_ID}")
    assert resp.status_code == 404


# ── PATCH /persons/{person_id}/goals/{goal_id} ────────────────────────────────


def test_patch_goal_success(app_client):
    updated = make_goal(body="Run an ultra marathon")
    with patch("app.api.v1.goals.update_goal", new=AsyncMock(return_value=updated)):
        resp = app_client.patch(
            f"/api/v1/persons/{PERSON_ID}/goals/{GOAL_ID}",
            json={"body": "Run an ultra marathon"},
        )
    assert resp.status_code == 200
    assert resp.json()["body"] == "Run an ultra marathon"


def test_patch_goal_mark_achieved(app_client):
    achieved_goal = make_goal(achieved_at=datetime.now(UTC))
    with patch("app.api.v1.goals.update_goal", new=AsyncMock(return_value=achieved_goal)):
        resp = app_client.patch(
            f"/api/v1/persons/{PERSON_ID}/goals/{GOAL_ID}", json={"achieved": True}
        )
    assert resp.status_code == 200
    assert resp.json()["achieved_at"] is not None


def test_patch_goal_not_found(app_client):
    with patch("app.api.v1.goals.update_goal", new=AsyncMock(return_value=None)):
        resp = app_client.patch(
            f"/api/v1/persons/{PERSON_ID}/goals/{uuid.uuid4()}",
            json={"body": "Ghost"},
        )
    assert resp.status_code == 404


# ── DELETE /persons/{person_id}/goals/{goal_id} ───────────────────────────────


def test_delete_goal_success(app_client):
    with (
        patch("app.api.v1.goals.get_person", new=AsyncMock(return_value=object())),
        patch("app.api.v1.goals.delete_goal", new=AsyncMock(return_value=object())),
    ):
        resp = app_client.delete(f"/api/v1/persons/{PERSON_ID}/goals/{GOAL_ID}")
    assert resp.status_code == 204


def test_delete_goal_person_not_found(app_client):
    with patch("app.api.v1.goals.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.delete(f"/api/v1/persons/{uuid.uuid4()}/goals/{GOAL_ID}")
    assert resp.status_code == 404


def test_delete_goal_not_found(app_client):
    with (
        patch("app.api.v1.goals.get_person", new=AsyncMock(return_value=object())),
        patch("app.api.v1.goals.delete_goal", new=AsyncMock(return_value=None)),
    ):
        resp = app_client.delete(f"/api/v1/persons/{PERSON_ID}/goals/{uuid.uuid4()}")
    assert resp.status_code == 404
