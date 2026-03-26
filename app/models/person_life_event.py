import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class PersonLifeEvent(SQLModel, table=True):
    __tablename__ = "person_life_event"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", index=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    event_type_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")

    title: str
    description: str | None = None
    occurred_on: date | None = None
    occurred_year: int | None = None
    metadata_: dict[str, Any] | None = Field(
        default=None, sa_column=Column("metadata", JSON, nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PersonSignificantDate(SQLModel, table=True):
    __tablename__ = "person_significant_date"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", index=True)

    label: str
    month: int
    day: int
    year: int | None = None
    recurs_annually: bool = Field(default=True)
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
