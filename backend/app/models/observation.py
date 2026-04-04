import uuid
from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel


class PersonObservation(SQLModel, table=True):
    __tablename__ = "person_observation"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", index=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)

    body: str
    observed_on: date | None = None
    source: str | None = None  # "conversation" | "social-media" | "email" | etc.
    context: str | None = None  # "personal" | "professional" | "mixed"
    is_sensitive: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )


class PersonObservationTag(SQLModel, table=True):
    __tablename__ = "person_observation_tag"

    observation_id: uuid.UUID = Field(
        foreign_key="person_observation.id", primary_key=True
    )
    term_id: uuid.UUID = Field(foreign_key="term.id", primary_key=True)
