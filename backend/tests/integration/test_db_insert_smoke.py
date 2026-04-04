"""
Smoke tests that INSERT one row per domain model into a real PostgreSQL database.

These tests catch column-type mismatches (e.g. tz-aware datetime vs
TIMESTAMP WITHOUT TIME ZONE) that unit tests with mocked sessions cannot detect.

Run with:
    cd backend && .venv/bin/uv run pytest -m integration --run-integration
"""

import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loan import Loan
from app.models.observation import PersonObservation
from app.models.person import Person
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.models.user import User


def _make_user() -> User:
    uid = str(uuid.uuid4())[:8]
    return User(
        username=f"smoke_{uid}",
        email=f"smoke_{uid}@test.invalid",
        hashed_password="hashed",
    )


def _make_person(owner_id: uuid.UUID) -> Person:
    return Person(owner_id=owner_id, first_name="Smoke", last_name="Test")


# ── Tests ──────────────────────────────────────────────────────────────────────


@pytest.mark.integration
async def test_user_insert(db: AsyncSession):
    user = _make_user()
    db.add(user)
    await db.flush()
    assert isinstance(user.id, uuid.UUID)


@pytest.mark.integration
async def test_person_insert(db: AsyncSession):
    user = _make_user()
    db.add(user)
    await db.flush()

    person = _make_person(user.id)
    db.add(person)
    await db.flush()
    assert isinstance(person.id, uuid.UUID)


@pytest.mark.integration
async def test_subscription_insert(db: AsyncSession):
    user = _make_user()
    db.add(user)
    await db.flush()

    sub = Subscription(
        owner_id=user.id,
        name="Smoke Sub",
        cost=99.0,
    )
    db.add(sub)
    await db.flush()
    assert isinstance(sub.id, uuid.UUID)


@pytest.mark.integration
async def test_loan_insert(db: AsyncSession):
    user = _make_user()
    db.add(user)
    await db.flush()

    person = _make_person(user.id)
    db.add(person)
    await db.flush()

    loan = Loan(
        owner_id=user.id,
        person_id=person.id,
        direction="lent",
        loan_type="money",
        description="Smoke loan",
        amount=500.0,
        currency="INR",
    )
    db.add(loan)
    await db.flush()
    assert isinstance(loan.id, uuid.UUID)


@pytest.mark.integration
async def test_transaction_insert(db: AsyncSession):
    user = _make_user()
    db.add(user)
    await db.flush()

    tx = Transaction(
        owner_id=user.id,
        transaction_type="expense",
        amount=250.0,
        currency="INR",
        transacted_on=date.today(),
        description="Smoke expense",
    )
    db.add(tx)
    await db.flush()
    assert isinstance(tx.id, uuid.UUID)


@pytest.mark.integration
async def test_observation_insert(db: AsyncSession):
    user = _make_user()
    db.add(user)
    await db.flush()

    person = _make_person(user.id)
    db.add(person)
    await db.flush()

    obs = PersonObservation(
        owner_id=user.id,
        person_id=person.id,
        body="Smoke observation body",
    )
    db.add(obs)
    await db.flush()
    assert isinstance(obs.id, uuid.UUID)
