import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.tasks import router as tasks_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.task import TaskPublicRead, TaskSummary
from app.schemas.vocabulary import TermSlim

OWNER_ID = uuid.uuid4()
TASK_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()
ASSET_ID = uuid.uuid4()
EVENT_ID = uuid.uuid4()
TAG_TERM_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)

WORK_TERM = TermSlim(id=TAG_TERM_ID, name="Work", slug="work")


def make_task(**kwargs) -> TaskPublicRead:
    defaults = dict(
        id=TASK_ID,
        owner_id=OWNER_ID,
        title="Buy groceries",
        description=None,
        status="todo",
        priority="normal",
        due_date=None,
        completed_at=None,
        person_id=None,
        asset_id=None,
        subscription_id=None,
        event_id=None,
        tags=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return TaskPublicRead(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(tasks_router, prefix="/api/v1")

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
    app.include_router(tasks_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


# ── POST /tasks/ ──────────────────────────────────────────────────────────────


def test_create_task_success(app_client):
    task = make_task()
    with patch("app.api.v1.tasks.create_task", new=AsyncMock(return_value=task)):
        resp = app_client.post("/api/v1/tasks/", json={"title": "Buy groceries"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Buy groceries"
    assert body["owner_id"] == str(OWNER_ID)
    assert body["status"] == "todo"


def test_create_task_missing_title(app_client):
    resp = app_client.post("/api/v1/tasks/", json={"description": "No title here"})
    assert resp.status_code == 422


def test_create_task_unauthenticated(unauthed_client):
    resp = unauthed_client.post("/api/v1/tasks/", json={"title": "Secret"})
    assert resp.status_code in (401, 422, 500)


def test_create_task_with_all_fields(app_client):
    task = make_task(
        description="Pick up from store",
        status="in_progress",
        priority="high",
        due_date=date(2026, 3, 25),
        person_id=PERSON_ID,
        tags=[WORK_TERM],
    )
    with patch("app.api.v1.tasks.create_task", new=AsyncMock(return_value=task)):
        resp = app_client.post(
            "/api/v1/tasks/",
            json={
                "title": "Buy groceries",
                "description": "Pick up from store",
                "status": "in_progress",
                "priority": "high",
                "due_date": "2026-03-25",
                "person_id": str(PERSON_ID),
                "tags": ["work"],
            },
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["description"] == "Pick up from store"
    assert body["priority"] == "high"
    assert body["due_date"] == "2026-03-25"
    assert len(body["tags"]) == 1


def test_create_task_with_event_id(app_client):
    task = make_task(event_id=EVENT_ID)
    with patch("app.api.v1.tasks.create_task", new=AsyncMock(return_value=task)):
        resp = app_client.post(
            "/api/v1/tasks/",
            json={"title": "Event task", "event_id": str(EVENT_ID)},
        )
    assert resp.status_code == 201
    assert resp.json()["event_id"] == str(EVENT_ID)


# ── GET /tasks/summary ────────────────────────────────────────────────────────


def test_get_task_summary(app_client):
    summary = TaskSummary(
        total=10,
        by_status={"todo": 5, "in_progress": 3, "done": 2},
        overdue=2,
        due_today=1,
    )
    with patch(
        "app.api.v1.tasks.get_task_summary", new=AsyncMock(return_value=summary)
    ):
        resp = app_client.get("/api/v1/tasks/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 10
    assert body["by_status"]["todo"] == 5
    assert body["overdue"] == 2
    assert body["due_today"] == 1


def test_get_task_summary_includes_by_priority(app_client):
    summary = TaskSummary(
        total=6,
        by_status={"todo": 3, "in_progress": 2, "done": 1},
        overdue=1,
        due_today=0,
        by_priority={"low": 1, "normal": 3, "high": 2},
    )
    with patch(
        "app.api.v1.tasks.get_task_summary", new=AsyncMock(return_value=summary)
    ):
        resp = app_client.get("/api/v1/tasks/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["by_priority"]["normal"] == 3
    assert body["by_priority"]["high"] == 2
    assert "low" in body["by_priority"]


# ── GET /tasks/ ───────────────────────────────────────────────────────────────


def test_list_tasks_returns_list(app_client):
    tasks = [make_task(), make_task(id=uuid.uuid4(), title="Another task")]
    with patch("app.api.v1.tasks.list_tasks", new=AsyncMock(return_value=(tasks, 2))):
        resp = app_client.get("/api/v1/tasks/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_tasks_empty(app_client):
    with patch("app.api.v1.tasks.list_tasks", new=AsyncMock(return_value=([], 0))):
        resp = app_client.get("/api/v1/tasks/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_tasks_status_filter(app_client):
    with patch(
        "app.api.v1.tasks.list_tasks", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        resp = app_client.get("/api/v1/tasks/?status=in_progress")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["status"] == "in_progress"


def test_list_tasks_priority_filter(app_client):
    with patch(
        "app.api.v1.tasks.list_tasks", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        resp = app_client.get("/api/v1/tasks/?priority=high")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["priority"] == "high"


def test_list_tasks_person_filter(app_client):
    with patch(
        "app.api.v1.tasks.list_tasks", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        resp = app_client.get(f"/api/v1/tasks/?person_id={PERSON_ID}")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["person_id"] == PERSON_ID


def test_list_tasks_event_filter(app_client):
    with patch(
        "app.api.v1.tasks.list_tasks", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        resp = app_client.get(f"/api/v1/tasks/?event_id={EVENT_ID}")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["event_id"] == EVENT_ID


def test_list_tasks_due_before_filter(app_client):
    with patch(
        "app.api.v1.tasks.list_tasks", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        resp = app_client.get("/api/v1/tasks/?due_before=2026-04-30")
    assert resp.status_code == 200
    assert mock_list.call_args.kwargs["due_before"] == date(2026, 4, 30)


def test_list_tasks_due_after_filter(app_client):
    with patch(
        "app.api.v1.tasks.list_tasks", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        resp = app_client.get("/api/v1/tasks/?due_after=2026-01-01")
    assert resp.status_code == 200
    assert mock_list.call_args.kwargs["due_after"] == date(2026, 1, 1)


def test_list_tasks_overdue_filter_true(app_client):
    with patch(
        "app.api.v1.tasks.list_tasks", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        resp = app_client.get("/api/v1/tasks/?overdue=true")
    assert resp.status_code == 200
    assert mock_list.call_args.kwargs["overdue"] is True


def test_list_tasks_overdue_filter_false(app_client):
    with patch(
        "app.api.v1.tasks.list_tasks", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        resp = app_client.get("/api/v1/tasks/?overdue=false")
    assert resp.status_code == 200
    assert mock_list.call_args.kwargs["overdue"] is False


# ── GET /tasks/{task_id} ──────────────────────────────────────────────────────


def test_get_task_found(app_client):
    task = make_task()
    with patch("app.api.v1.tasks.get_task_public", new=AsyncMock(return_value=task)):
        resp = app_client.get(f"/api/v1/tasks/{TASK_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(TASK_ID)


def test_get_task_not_found(app_client):
    with patch("app.api.v1.tasks.get_task_public", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"/api/v1/tasks/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /tasks/{task_id} ────────────────────────────────────────────────────


def test_patch_task_success(app_client):
    updated = make_task(title="Updated task", status="done")
    with patch("app.api.v1.tasks.update_task", new=AsyncMock(return_value=updated)):
        resp = app_client.patch(
            f"/api/v1/tasks/{TASK_ID}",
            json={"title": "Updated task", "status": "done"},
        )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated task"
    assert resp.json()["status"] == "done"


def test_patch_task_not_found(app_client):
    with patch("app.api.v1.tasks.update_task", new=AsyncMock(return_value=None)):
        resp = app_client.patch(
            f"/api/v1/tasks/{uuid.uuid4()}", json={"title": "Ghost"}
        )
    assert resp.status_code == 404


# ── DELETE /tasks/{task_id} ───────────────────────────────────────────────────


def test_delete_task_success(app_client):
    with patch(
        "app.api.v1.tasks.soft_delete_task", new=AsyncMock(return_value=object())
    ):
        resp = app_client.delete(f"/api/v1/tasks/{TASK_ID}")
    assert resp.status_code == 204


def test_delete_task_not_found(app_client):
    with patch("app.api.v1.tasks.soft_delete_task", new=AsyncMock(return_value=None)):
        resp = app_client.delete(f"/api/v1/tasks/{uuid.uuid4()}")
    assert resp.status_code == 404
