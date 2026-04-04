import uuid
from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel


class Event(SQLModel, table=True):
    __tablename__ = "event"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)

    title: str
    event_type_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    description: str | None = None
    occurred_on: date | None = None
    location: str | None = None
    notes: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )


class EventPerson(SQLModel, table=True):
    __tablename__ = "event_person"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    event_id: uuid.UUID = Field(foreign_key="event.id", index=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", index=True)
    role: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
