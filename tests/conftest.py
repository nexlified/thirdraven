from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import router as auth_router
from app.core.database import get_session


@pytest.fixture
def fake_db() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def app(fake_db: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")

    async def override_get_session() -> AsyncGenerator[AsyncSession]:
        yield fake_db

    app.dependency_overrides[get_session] = override_get_session
    return app


@pytest.fixture
def client(app: FastAPI):
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
