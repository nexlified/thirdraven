import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class PersonSignificantDate(SQLModel, table=True):
    __tablename__ = "person_significant_date"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", index=True)

    date_type_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    label: str | None = (
        None  # free-text override; at least one of date_type or label must be set
    )
    month: int
    day: int
    year: int | None = None
    recurs_annually: bool = Field(default=True)
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
