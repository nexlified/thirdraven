import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.vocabulary import TermSlim


class NoteCreate(BaseModel):
    title: str
    body: str | None = None
    pinned: bool = False
    person_id: uuid.UUID | None = None
    asset_id: uuid.UUID | None = None
    subscription_id: uuid.UUID | None = None
    event_id: uuid.UUID | None = None
    tags: list[str] = []  # slugs from "note-tags" vocabulary


class NoteUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    pinned: bool | None = None
    person_id: uuid.UUID | None = None
    asset_id: uuid.UUID | None = None
    subscription_id: uuid.UUID | None = None
    event_id: uuid.UUID | None = None
    tags: list[str] | None = None


class NotePublicRead(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    body: str | None
    pinned: bool
    person_id: uuid.UUID | None
    asset_id: uuid.UUID | None
    subscription_id: uuid.UUID | None
    event_id: uuid.UUID | None
    tags: list[TermSlim]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteStatistics(BaseModel):
    total: int
    pinned: int
    by_attachment: dict[str, int]
