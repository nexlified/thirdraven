"""Abstract base class for all import handlers."""

import uuid
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession


class BaseImportHandler(ABC):
    @abstractmethod
    async def parse(self, raw_data: str, source_format: str) -> list[dict]:
        """Parse raw file content into a list of normalised row dicts."""

    @abstractmethod
    async def find_candidates(
        self, db: AsyncSession, owner_id: uuid.UUID, row: dict
    ) -> list[dict]:
        """Return existing DB records that might match this row."""

    @abstractmethod
    async def execute_create(
        self, db: AsyncSession, owner_id: uuid.UUID, row: dict
    ) -> uuid.UUID:
        """Create a new entity from the row and return its UUID."""

    @abstractmethod
    async def execute_merge(
        self, db: AsyncSession, owner_id: uuid.UUID, target_id: uuid.UUID, row: dict
    ) -> uuid.UUID:
        """Merge row data into the existing entity and return its UUID."""
