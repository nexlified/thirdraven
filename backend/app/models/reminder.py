import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _naive_utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Reminder(SQLModel, table=True):
    __tablename__ = "reminder"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)

    title: str
    body: str | None = None
    due_at: datetime
    remind_at: datetime | None = None
    recurrence: str | None = None  # "daily"|"weekly"|"monthly"|"annual"
    is_done: bool = Field(default=False)
    done_at: datetime | None = None

    # Polymorphic nullable FKs
    person_id: uuid.UUID | None = Field(
        default=None, foreign_key="person.id", index=True
    )
    asset_id: uuid.UUID | None = Field(default=None, foreign_key="asset.id", index=True)
    subscription_id: uuid.UUID | None = Field(
        default=None, foreign_key="subscription.id", index=True
    )

    created_at: datetime = Field(default_factory=_naive_utc_now)
    updated_at: datetime = Field(default_factory=_naive_utc_now)
    deleted_at: datetime | None = None
