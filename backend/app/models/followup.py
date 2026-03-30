import uuid
from datetime import date, datetime

from sqlmodel import Field, SQLModel


class PersonFollowUp(SQLModel, table=True):
    __tablename__ = "person_followup"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", index=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)

    body: str
    due_on: date | None = None
    interaction_id: uuid.UUID | None = Field(
        default=None, foreign_key="interaction.id"
    )
    cleared_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
