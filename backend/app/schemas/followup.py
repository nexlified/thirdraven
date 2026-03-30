import uuid
from datetime import date, datetime

from pydantic import BaseModel


class FollowUpCreate(BaseModel):
    body: str
    due_on: date | None = None
    interaction_id: uuid.UUID | None = None


class FollowUpUpdate(BaseModel):
    body: str | None = None
    due_on: date | None = None
    interaction_id: uuid.UUID | None = None
    cleared: bool | None = None  # True = mark cleared, False = unmark


class FollowUpPublic(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    owner_id: uuid.UUID
    body: str
    due_on: date | None
    interaction_id: uuid.UUID | None
    cleared_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
