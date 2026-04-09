"""
Integration test conftest — shared fixtures for API-level integration tests.

The `api_engine` fixture creates a fresh SQLite in-memory database per test,
seeds it with reference/vocabulary data, and tears it down after the test.
All CRUD code commits directly to this DB (no rollback tricks needed because
the DB is ephemeral per test).

The `api_client` fixture builds a full FastAPI app (no mocks) with the test
engine injected via `dependency_overrides[get_session]`.
"""

# ruff: noqa: F401

import pytest
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# ── PostgreSQL smoke-test fixture (kept from original) ────────────────────────
from sqlalchemy.ext.asyncio import AsyncSession as SAAsyncSession
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()


@pytest.fixture
async def db():
    """
    Function-scoped async session with NullPool.

    NullPool prevents asyncpg connection reuse between tests, which avoids
    'another operation is in progress' errors when rolling back between tests.
    The session rolls back after every test so no data is committed.
    """
    engine = create_async_engine(settings.database_url, echo=False, poolclass=NullPool)
    try:
        async with SAAsyncSession(engine, expire_on_commit=False) as session:
            yield session
            await session.rollback()
    finally:
        await engine.dispose()


# ── API integration test fixtures ─────────────────────────────────────────────

# Import every model so SQLModel.metadata is fully populated before create_all.
import app.models.asset  # noqa: E402
import app.models.asset_event  # noqa: E402
import app.models.asset_extensions  # noqa: E402
import app.models.budget  # noqa: E402
import app.models.communication  # noqa: E402
# app.models.contact is intentionally excluded — uses PostgreSQL ARRAY which
# is not supported by SQLite. The contact table is not part of api_router.
import app.models.document  # noqa: E402
import app.models.event  # noqa: E402
import app.models.followup  # noqa: E402
import app.models.goal  # noqa: E402
import app.models.household  # noqa: E402
import app.models.import_job  # noqa: E402
import app.models.import_row  # noqa: E402
import app.models.interaction  # noqa: E402
import app.models.inventory  # noqa: E402
import app.models.iso_reference  # noqa: E402
import app.models.life_event  # noqa: E402
import app.models.loan  # noqa: E402
import app.models.note  # noqa: E402
import app.models.observation  # noqa: E402
import app.models.organization  # noqa: E402
import app.models.person  # noqa: E402
import app.models.person_extensions  # noqa: E402
import app.models.person_life_event  # noqa: E402
import app.models.person_relationship  # noqa: E402
import app.models.product  # noqa: E402
import app.models.raven_log  # noqa: E402
import app.models.raven_question  # noqa: E402
import app.models.reference  # noqa: E402
# app.models.relationship (ContactRelationship) excluded — it has FK to the
# contact table which uses ARRAY and cannot be created in SQLite.
import app.models.reminder  # noqa: E402
import app.models.shopping_list  # noqa: E402
import app.models.subscription  # noqa: E402
import app.models.task  # noqa: E402
import app.models.tracked_record  # noqa: E402
import app.models.transaction  # noqa: E402
import app.models.transaction_item  # noqa: E402
import app.models.user  # noqa: E402
import app.models.vocabulary  # noqa: E402

from app.api.v1 import api_router
from app.core.database import get_session
from app.core.security import create_access_token

# ── Known vocabulary slugs confirmed from seeds/seed_data.py ─────────────────
KNOWN_SLUGS = {
    "asset_category": "electronics",   # asset-categories vocab
    "asset_status": "active",          # asset-statuses vocab
    "expense_category": "groceries",   # expense-categories vocab
}


@pytest.fixture
async def api_engine():
    """
    Function-scoped SQLite in-memory engine.

    StaticPool ensures a single underlying connection is reused, which is
    required for in-memory SQLite (each new connection gets a fresh DB).
    A fresh DB is created per test function, so tests are fully isolated.
    """
    from seeds.seed_data import seed_all

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Seed ISO reference data and all vocabularies once for this test's DB.
    async with AsyncSession(engine, expire_on_commit=False) as seed_session:
        await seed_all(seed_session)

    yield engine
    await engine.dispose()


@pytest.fixture
async def test_user(api_engine):
    """Creates a real user (and their self-Person record) via CRUD."""
    from app.crud.user import create_user
    from app.schemas.user import UserCreate

    async with AsyncSession(api_engine, expire_on_commit=False) as session:
        return await create_user(
            session,
            UserCreate(
                username="integration_user",
                email="integration@example.com",
                password="TestPass123!",
                first_name="Integration",
                last_name="Tester",
            ),
        )


@pytest.fixture
def auth_headers(test_user) -> dict[str, str]:
    """Bearer token headers for the test user."""
    token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def api_client(api_engine) -> AsyncGenerator[AsyncClient, None]:
    """
    Full FastAPI app wired to the test DB.

    Each API request gets a fresh AsyncSession from the test engine.
    No lifespan is attached — avoids spinning up the real database engine.
    """
    test_app = FastAPI()
    test_app.include_router(api_router, prefix="/api/v1")

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSession(api_engine, expire_on_commit=False) as session:
            yield session

    test_app.dependency_overrides[get_session] = override_session

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        yield client

    test_app.dependency_overrides.clear()
