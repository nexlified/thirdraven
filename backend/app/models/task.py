import uuid
from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel


class Task(SQLModel, table=True):
    __tablename__ = "task"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    title: str
    description: str | None = None
    status: str = "todo"  # todo | in_progress | done | cancelled | blocked
    priority: str = "normal"  # low | normal | high | urgent
    due_date: date | None = None
    completed_at: datetime | None = None
    person_id: uuid.UUID | None = Field(default=None, foreign_key="person.id")
    asset_id: uuid.UUID | None = Field(default=None, foreign_key="asset.id")
    subscription_id: uuid.UUID | None = Field(
        default=None, foreign_key="subscription.id"
    )
    event_id: uuid.UUID | None = Field(default=None, foreign_key="event.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    deleted_at: datetime | None = None


class TaskTag(SQLModel, table=True):
    __tablename__ = "task_tag"

    task_id: uuid.UUID = Field(foreign_key="task.id", primary_key=True)
    term_id: uuid.UUID = Field(foreign_key="term.id", primary_key=True)
