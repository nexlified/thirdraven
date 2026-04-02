import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


class LifeEvent(SQLModel, table=True):
    __tablename__ = "life_event"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    event_type_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")

    title: str
    description: str | None = None
    occurred_on: date | None = None
    occurred_year: int | None = None
    emotion_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    cost: float | None = None
    currency: str | None = None  # ISO 4217
    duration_minutes: int | None = None
    place: str | None = None
    metadata_: dict[str, Any] | None = Field(
        default=None, sa_column=Column("metadata", JSON, nullable=True)
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LifeEventPerson(SQLModel, table=True):
    __tablename__ = "life_event_person"
    __table_args__ = (UniqueConstraint("life_event_id", "person_id"),)

    life_event_id: uuid.UUID = Field(
        foreign_key="life_event.id", primary_key=True, index=True
    )
    person_id: uuid.UUID = Field(foreign_key="person.id", primary_key=True, index=True)
    role: str | None = None  # "primary" | "participant" | custom
