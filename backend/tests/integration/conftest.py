import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
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
        async with AsyncSession(engine, expire_on_commit=False) as session:
            yield session
            await session.rollback()
    finally:
        await engine.dispose()
