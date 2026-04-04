import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Note(SQLModel, table=True):
    __tablename__ = "note"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    title: str
    body: str | None = None
    pinned: bool = Field(default=False)
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


class NoteTag(SQLModel, table=True):
    __tablename__ = "note_tag"

    note_id: uuid.UUID = Field(foreign_key="note.id", primary_key=True)
    term_id: uuid.UUID = Field(foreign_key="term.id", primary_key=True)
