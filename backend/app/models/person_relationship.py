import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class PersonRelationship(SQLModel, table=True):
    __tablename__ = "person_relationship"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    from_person_id: uuid.UUID = Field(foreign_key="person.id", index=True)
    to_person_id: uuid.UUID = Field(foreign_key="person.id", index=True)
    label_term_id: uuid.UUID = Field(foreign_key="term.id")
    inverse_id: uuid.UUID | None = Field(
        default=None, foreign_key="person_relationship.id", nullable=True
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
