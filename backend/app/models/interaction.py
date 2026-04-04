import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def _naive_utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Interaction(SQLModel, table=True):
    __tablename__ = "interaction"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", index=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    interaction_type_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    title: str
    occurred_on: date | None = None
    context: str | None = None  # "personal" | "professional" | "mixed"
    notes: str | None = None
    metadata_: dict[str, Any] | None = Field(
        default=None, sa_column=Column("metadata", JSON, nullable=True)
    )
    created_at: datetime = Field(default_factory=_naive_utc_now)
    updated_at: datetime = Field(default_factory=_naive_utc_now)
