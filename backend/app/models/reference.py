import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class PersonTerm(SQLModel, table=True):
    __tablename__ = "person_term"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", index=True)
    term_id: uuid.UUID = Field(foreign_key="term.id", index=True)
    context: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
