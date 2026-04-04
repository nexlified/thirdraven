import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.budgets import router as budgets_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.budget import BudgetPublic, BudgetWithSpend
from app.schemas.vocabulary import TermSlim

OWNER_ID = uuid.uuid4()
BUDGET_ID = uuid.uuid4()
CAT_TERM_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)

FOOD_TERM = TermSlim(id=CAT_TERM_ID, name="Food & Dining", slug="food")


def make_budget_public(**kwargs) -> BudgetPublic:
    defaults = dict(
        id=BUDGET_ID,
        owner_id=OWNER_ID,
        category=FOOD_TERM,
        year=2026,
        month=4,
        amount=5000.0,
        currency="INR",
        notes=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return BudgetPublic(**defaults)


def make_budget_with_spend(**kwargs) -> BudgetWithSpend:
    defaults = dict(
        id=BUDGET_ID,
        owner_id=OWNER_ID,
        category=FOOD_TERM,
        year=2026,
        month=4,
        amount=5000.0,
        currency="INR",
        notes=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        spent=2500.0,
        remaining=2500.0,
        utilization=0.5,
    )
    defaults.update(kwargs)
    return BudgetWithSpend(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(budgets_router, prefix="/api/v1")

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


# ── POST /budgets/ ─────────────────────────────────────────────────────────────


def test_create_budget_success(app_client):
    budget = make_budget_public()
    with patch(
        "app.api.v1.budgets.create_budget",
        new=AsyncMock(return_value=budget),
    ):
        resp = app_client.post(
            "/api/v1/budgets/",
            json={
                "category": "food",
                "year": 2026,
                "month": 4,
                "amount": 5000.0,
                "currency": "INR",
            },
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["year"] == 2026
    assert body["month"] == 4
    assert body["amount"] == 5000.0
    assert body["owner_id"] == str(OWNER_ID)


def test_create_budget_invalid_month(app_client):
    resp = app_client.post(
        "/api/v1/budgets/",
        json={
            "category": "food",
            "year": 2026,
            "month": 13,
            "amount": 5000.0,
        },
    )
    assert resp.status_code == 422


def test_create_budget_invalid_month_zero(app_client):
    resp = app_client.post(
        "/api/v1/budgets/",
        json={
            "category": "food",
            "year": 2026,
            "month": 0,
            "amount": 5000.0,
        },
    )
    assert resp.status_code == 422


def test_create_budget_duplicate_returns_409(app_client):
    from fastapi import HTTPException

    with patch(
        "app.api.v1.budgets.create_budget",
        new=AsyncMock(
            side_effect=HTTPException(
                status_code=409,
                detail="Budget already exists for this category and month",
            )
        ),
    ):
        resp = app_client.post(
            "/api/v1/budgets/",
            json={
                "category": "food",
                "year": 2026,
                "month": 4,
                "amount": 5000.0,
            },
        )
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]


def test_create_budget_missing_required(app_client):
    resp = app_client.post(
        "/api/v1/budgets/",
        json={"category": "food", "year": 2026},
    )
    assert resp.status_code == 422


# ── GET /budgets/ ──────────────────────────────────────────────────────────────


def test_list_budgets_success(app_client):
    b = make_budget_with_spend()
    with patch(
        "app.api.v1.budgets.list_budgets",
        new=AsyncMock(return_value=[b]),
    ):
        resp = app_client.get("/api/v1/budgets/", params={"year": 2026, "month": 4})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    item = body[0]
    assert item["spent"] == 2500.0
    assert item["remaining"] == 2500.0
    assert item["utilization"] == 0.5


def test_list_budgets_empty(app_client):
    with patch(
        "app.api.v1.budgets.list_budgets",
        new=AsyncMock(return_value=[]),
    ):
        resp = app_client.get("/api/v1/budgets/", params={"year": 2026, "month": 4})
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_budgets_over_budget(app_client):
    b = make_budget_with_spend(spent=6000.0, remaining=-1000.0, utilization=1.2)
    with patch(
        "app.api.v1.budgets.list_budgets",
        new=AsyncMock(return_value=[b]),
    ):
        resp = app_client.get("/api/v1/budgets/", params={"year": 2026, "month": 4})
    assert resp.status_code == 200
    item = resp.json()[0]
    assert item["utilization"] == 1.2
    assert item["remaining"] == -1000.0


def test_list_budgets_missing_year(app_client):
    resp = app_client.get("/api/v1/budgets/", params={"month": 4})
    assert resp.status_code == 422


def test_list_budgets_missing_month(app_client):
    resp = app_client.get("/api/v1/budgets/", params={"year": 2026})
    assert resp.status_code == 422


# ── PATCH /budgets/{id} ────────────────────────────────────────────────────────


def test_patch_budget_success(app_client):
    updated = make_budget_public(amount=8000.0, notes="Revised budget")
    with patch(
        "app.api.v1.budgets.update_budget",
        new=AsyncMock(return_value=updated),
    ):
        resp = app_client.patch(
            f"/api/v1/budgets/{BUDGET_ID}",
            json={"amount": 8000.0, "notes": "Revised budget"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["amount"] == 8000.0
    assert body["notes"] == "Revised budget"


def test_patch_budget_not_found(app_client):
    with patch(
        "app.api.v1.budgets.update_budget",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.patch(
            f"/api/v1/budgets/{uuid.uuid4()}",
            json={"amount": 8000.0},
        )
    assert resp.status_code == 404


# ── DELETE /budgets/{id} ───────────────────────────────────────────────────────


def test_delete_budget_success(app_client):
    with patch(
        "app.api.v1.budgets.delete_budget",
        new=AsyncMock(return_value=True),
    ):
        resp = app_client.delete(f"/api/v1/budgets/{BUDGET_ID}")
    assert resp.status_code == 204


def test_delete_budget_not_found(app_client):
    with patch(
        "app.api.v1.budgets.delete_budget",
        new=AsyncMock(return_value=False),
    ):
        resp = app_client.delete(f"/api/v1/budgets/{uuid.uuid4()}")
    assert resp.status_code == 404
