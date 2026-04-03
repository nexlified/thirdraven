import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.loans import person_loans_router
from app.api.v1.loans import router as loans_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.loan import LoanPublic

OWNER_ID = uuid.uuid4()
LOAN_ID = uuid.uuid4()
PERSON_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.now(UTC),
)


def make_loan(**kwargs) -> LoanPublic:
    defaults = dict(
        id=LOAN_ID,
        owner_id=OWNER_ID,
        person_id=PERSON_ID,
        direction="lent",
        loan_type="money",
        description="Lent for medical expenses",
        amount=500.0,
        currency="USD",
        item_name=None,
        loaned_on=date(2025, 1, 10),
        due_on=date(2025, 3, 10),
        returned_on=None,
        status="outstanding",
        notes=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return LoanPublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(loans_router, prefix="/api/v1")
    app.include_router(person_loans_router, prefix="/api/v1")

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
    app.include_router(loans_router, prefix="/api/v1")
    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


# ── POST /loans/ ──────────────────────────────────────────────────────────────


def test_create_money_loan_success(app_client):
    loan = make_loan()
    with patch("app.api.v1.loans.create_loan", new=AsyncMock(return_value=loan)):
        resp = app_client.post(
            "/api/v1/loans/",
            json={
                "person_id": str(PERSON_ID),
                "direction": "lent",
                "loan_type": "money",
                "description": "Lent for medical expenses",
                "amount": 500.0,
                "currency": "USD",
            },
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["direction"] == "lent"
    assert body["loan_type"] == "money"
    assert body["amount"] == 500.0
    assert body["status"] == "outstanding"


def test_create_item_loan_success(app_client):
    loan = make_loan(
        loan_type="item", amount=None, currency=None, item_name="Canon EOS R5"
    )
    with patch("app.api.v1.loans.create_loan", new=AsyncMock(return_value=loan)):
        resp = app_client.post(
            "/api/v1/loans/",
            json={
                "person_id": str(PERSON_ID),
                "direction": "lent",
                "loan_type": "item",
                "description": "Lent camera",
                "item_name": "Canon EOS R5",
            },
        )
    assert resp.status_code == 201
    assert resp.json()["item_name"] == "Canon EOS R5"


def test_create_loan_missing_required_fields(app_client):
    # Missing person_id, direction, loan_type, description
    resp = app_client.post("/api/v1/loans/", json={"amount": 100.0})
    assert resp.status_code == 422


def test_create_loan_unauthenticated(unauthed_client):
    resp = unauthed_client.post(
        "/api/v1/loans/",
        json={
            "person_id": str(PERSON_ID),
            "direction": "lent",
            "loan_type": "money",
            "description": "Test",
        },
    )
    assert resp.status_code in (401, 422, 500)


# ── GET /loans/ ────────────────────────────────────────────────────────────────


def test_list_loans_returns_list(app_client):
    loans = [make_loan(), make_loan(id=uuid.uuid4(), direction="borrowed")]
    with patch("app.api.v1.loans.list_loans", new=AsyncMock(return_value=(loans, 2))):
        resp = app_client.get("/api/v1/loans/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_loans_empty(app_client):
    with patch("app.api.v1.loans.list_loans", new=AsyncMock(return_value=([], 0))):
        resp = app_client.get("/api/v1/loans/")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_list_loans_direction_filter(app_client):
    with patch(
        "app.api.v1.loans.list_loans", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        app_client.get("/api/v1/loans/?direction=lent")
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["direction"] == "lent"


def test_list_loans_status_filter(app_client):
    with patch(
        "app.api.v1.loans.list_loans", new=AsyncMock(return_value=([], 0))
    ) as mock_list:
        app_client.get("/api/v1/loans/?status_filter=outstanding")
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["status"] == "outstanding"


# ── GET /loans/{loan_id} ──────────────────────────────────────────────────────


def test_get_loan_found(app_client):
    loan = make_loan()
    with patch("app.api.v1.loans.get_loan", new=AsyncMock(return_value=loan)):
        resp = app_client.get(f"/api/v1/loans/{LOAN_ID}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(LOAN_ID)


def test_get_loan_not_found(app_client):
    with patch("app.api.v1.loans.get_loan", new=AsyncMock(return_value=None)):
        resp = app_client.get(f"/api/v1/loans/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── PATCH /loans/{loan_id} ────────────────────────────────────────────────────


def test_patch_loan_mark_returned(app_client):
    returned = make_loan(status="returned", returned_on=date(2025, 3, 5))
    with patch("app.api.v1.loans.update_loan", new=AsyncMock(return_value=returned)):
        resp = app_client.patch(
            f"/api/v1/loans/{LOAN_ID}",
            json={"status": "returned", "returned_on": "2025-03-05"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "returned"
    assert resp.json()["returned_on"] == "2025-03-05"


def test_patch_loan_not_found(app_client):
    with patch("app.api.v1.loans.update_loan", new=AsyncMock(return_value=None)):
        resp = app_client.patch(
            f"/api/v1/loans/{uuid.uuid4()}", json={"status": "returned"}
        )
    assert resp.status_code == 404


def test_patch_loan_partial_update(app_client):
    updated = make_loan(description="Updated description")
    with patch(
        "app.api.v1.loans.update_loan", new=AsyncMock(return_value=updated)
    ) as mock_update:
        resp = app_client.patch(
            f"/api/v1/loans/{LOAN_ID}", json={"description": "Updated description"}
        )
    assert resp.status_code == 200
    update_data = mock_update.call_args.args[3]
    assert update_data.description == "Updated description"
    assert update_data.status is None


# ── DELETE /loans/{loan_id} ───────────────────────────────────────────────────


def test_delete_loan_success(app_client):
    with patch(
        "app.api.v1.loans.soft_delete_loan", new=AsyncMock(return_value=object())
    ):
        resp = app_client.delete(f"/api/v1/loans/{LOAN_ID}")
    assert resp.status_code == 204


def test_delete_loan_not_found(app_client):
    with patch("app.api.v1.loans.soft_delete_loan", new=AsyncMock(return_value=None)):
        resp = app_client.delete(f"/api/v1/loans/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── GET /persons/{person_id}/loans/ ───────────────────────────────────────────


def test_list_person_loans(app_client):
    loans = [make_loan()]
    with patch(
        "app.api.v1.loans.list_loans", new=AsyncMock(return_value=(loans, 1))
    ) as mock_list:
        resp = app_client.get(f"/api/v1/persons/{PERSON_ID}/loans/")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["person_id"] == PERSON_ID
