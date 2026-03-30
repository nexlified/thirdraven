import uuid
from datetime import datetime

from pydantic import BaseModel


class ReminderCreate(BaseModel):
    title: str
    body: str | None = None
    due_at: datetime
    remind_at: datetime | None = None
    recurrence: str | None = None  # "daily"|"weekly"|"monthly"|"annual"
    person_id: uuid.UUID | None = None
    asset_id: uuid.UUID | None = None
    subscription_id: uuid.UUID | None = None


class ReminderUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    due_at: datetime | None = None
    remind_at: datetime | None = None
    recurrence: str | None = None
    is_done: bool | None = None


class ReminderPublic(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    body: str | None
    due_at: datetime
    remind_at: datetime | None
    recurrence: str | None
    is_done: bool
    done_at: datetime | None
    person_id: uuid.UUID | None
    asset_id: uuid.UUID | None
    subscription_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
