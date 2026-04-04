import uuid
from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel

GOAL_TYPES = {"aspiration", "fear", "current-focus", "learning"}


class PersonGoal(SQLModel, table=True):
    __tablename__ = "person_goal"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", index=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)

    goal_type: str  # aspiration | fear | current-focus | learning
    body: str
    target_date: date | None = None
    achieved_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
