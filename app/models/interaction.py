import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Interaction(SQLModel, table=True):
    __tablename__ = "interaction"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", index=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    interaction_type_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    title: str
    occurred_on: date | None = None
    notes: str | None = None
    metadata_: dict[str, Any] | None = Field(
        default=None, sa_column=Column("metadata", JSON, nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
