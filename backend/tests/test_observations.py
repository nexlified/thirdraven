import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.observations import router as observations_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.observation import ObservationPublic
from app.schemas.vocabulary import TermSlim

OWNER_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()
OBS_ID = uuid.uuid4()
TAG_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)

INSIGHTFUL_TAG = TermSlim(id=TAG_ID, name="Insightful", slug="insightful")


def make_observation(**kwargs) -> ObservationPublic:
    defaults = dict(
        id=OBS_ID,
        person_id=PERSON_ID,
        owner_id=OWNER_ID,
        body="Prefers direct communication",
        observed_on=None,
        source=None,
        context=None,
        is_sensitive=False,
        tags=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return ObservationPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(observations_router, prefix="/api/v1")

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


# ── POST /persons/{person_id}/observations/ ────────────────────────────────────


def test_create_observation_success(app_client):
    obs = make_observation()
    with (
        patch(
            "app.api.v1.observations.get_person", new=AsyncMock(return_value=object())
        ),
        patch(
            "app.api.v1.observations.create_observation",
            new=AsyncMock(return_value=obs),
        ),
    ):
        resp = app_client.post(
            f"/api/v1/persons/{PERSON_ID}/observations/",
            json={"body": "Prefers direct communication"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["body"] == "Prefers direct communication"
    assert body["is_sensitive"] is False


def test_create_observation_person_not_found(app_client):
    with patch("app.api.v1.observations.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.post(
            f"/api/v1/persons/{uuid.uuid4()}/observations/",
            json={"body": "Test observation"},
        )
    assert resp.status_code == 404


def test_create_observation_missing_body(app_client):
    with patch(
        "app.api.v1.observations.get_person", new=AsyncMock(return_value=object())
    ):
        resp = app_client.post(
            f"/api/v1/persons/{PERSON_ID}/observations/",
            json={"context": "personal"},
        )
    assert resp.status_code == 422


def test_create_observation_sensitive_with_tags(app_client):
    obs = make_observation(is_sensitive=True, tags=[INSIGHTFUL_TAG])
    with (
        patch(
            "app.api.v1.observations.get_person", new=AsyncMock(return_value=object())
        ),
        patch(
            "app.api.v1.observations.create_observation",
            new=AsyncMock(return_value=obs),
        ),
    ):
        resp = app_client.post(
            f"/api/v1/persons/{PERSON_ID}/observations/",
            json={
                "body": "Struggles with conflict",
                "is_sensitive": True,
                "tags": ["insightful"],
                "context": "personal",
            },
        )
    assert resp.status_code == 201
    assert resp.json()["is_sensitive"] is True
    assert len(resp.json()["tags"]) == 1


# ── GET /persons/{person_id}/observations/ ─────────────────────────────────────


def test_list_observations_returns_list(app_client):
    obs_list = [
        make_observation(),
        make_observation(id=uuid.uuid4(), body="Very curious"),
    ]
    with (
        patch(
            "app.api.v1.observations.get_person", new=AsyncMock(return_value=object())
        ),
        patch(
            "app.api.v1.observations.list_observations",
            new=AsyncMock(return_value=(obs_list, 2)),
        ),
    ):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}/observations/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_observations_person_not_found(app_client):
    with patch("app.api.v1.observations.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"/api/v1/persons/{uuid.uuid4()}/observations/")
    assert resp.status_code == 404


def test_list_observations_exclude_sensitive(app_client):
    with (
        patch(
            "app.api.v1.observations.get_person", new=AsyncMock(return_value=object())
        ),
        patch(
            "app.api.v1.observations.list_observations",
            new=AsyncMock(return_value=([], 0)),
        ) as mock_list,
    ):
        app_client.get(
            f"/api/v1/persons/{PERSON_ID}/observations/?include_sensitive=false"
        )
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["include_sensitive"] is False


def test_list_observations_context_filter(app_client):
    with (
        patch(
            "app.api.v1.observations.get_person", new=AsyncMock(return_value=object())
        ),
        patch(
            "app.api.v1.observations.list_observations",
            new=AsyncMock(return_value=([], 0)),
        ) as mock_list,
    ):
        app_client.get(
            f"/api/v1/persons/{PERSON_ID}/observations/?context=professional"
        )
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["context"] == "professional"


# ── GET /persons/{person_id}/observations/{obs_id} ────────────────────────────


def test_get_observation_found(app_client):
    obs = make_observation()
    with patch(
        "app.api.v1.observations.get_observation", new=AsyncMock(return_value=obs)
    ):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}/observations/{OBS_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(OBS_ID)


def test_get_observation_not_found(app_client):
    with patch(
        "app.api.v1.observations.get_observation", new=AsyncMock(return_value=None)
    ):
        resp = app_client.get(
            f"/api/v1/persons/{PERSON_ID}/observations/{uuid.uuid4()}"
        )
    assert resp.status_code == 404


def test_get_observation_wrong_person(app_client):
    obs = make_observation(person_id=uuid.uuid4())
    with patch(
        "app.api.v1.observations.get_observation", new=AsyncMock(return_value=obs)
    ):
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}/observations/{OBS_ID}")
    assert resp.status_code == 404


# ── PATCH /persons/{person_id}/observations/{obs_id} ──────────────────────────


def test_patch_observation_success(app_client):
    updated = make_observation(body="Updated observation", context="professional")
    with patch(
        "app.api.v1.observations.update_observation",
        new=AsyncMock(return_value=updated),
    ):
        resp = app_client.patch(
            f"/api/v1/persons/{PERSON_ID}/observations/{OBS_ID}",
            json={"body": "Updated observation", "context": "professional"},
        )
    assert resp.status_code == 200
    assert resp.json()["body"] == "Updated observation"


def test_patch_observation_not_found(app_client):
    with patch(
        "app.api.v1.observations.update_observation", new=AsyncMock(return_value=None)
    ):
        resp = app_client.patch(
            f"/api/v1/persons/{PERSON_ID}/observations/{uuid.uuid4()}",
            json={"body": "Ghost"},
        )
    assert resp.status_code == 404


# ── DELETE /persons/{person_id}/observations/{obs_id} ─────────────────────────


def test_delete_observation_success(app_client):
    with (
        patch(
            "app.api.v1.observations.get_person", new=AsyncMock(return_value=object())
        ),
        patch(
            "app.api.v1.observations.delete_observation",
            new=AsyncMock(return_value=object()),
        ),
    ):
        resp = app_client.delete(f"/api/v1/persons/{PERSON_ID}/observations/{OBS_ID}")
    assert resp.status_code == 204


def test_delete_observation_person_not_found(app_client):
    with patch("app.api.v1.observations.get_person", new=AsyncMock(return_value=None)):
        resp = app_client.delete(
            f"/api/v1/persons/{uuid.uuid4()}/observations/{OBS_ID}"
        )
    assert resp.status_code == 404


def test_delete_observation_not_found(app_client):
    with (
        patch(
            "app.api.v1.observations.get_person", new=AsyncMock(return_value=object())
        ),
        patch(
            "app.api.v1.observations.delete_observation",
            new=AsyncMock(return_value=None),
        ),
    ):
        resp = app_client.delete(
            f"/api/v1/persons/{PERSON_ID}/observations/{uuid.uuid4()}"
        )
    assert resp.status_code == 404
