import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.vocabulary import TermSlim


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: str = "todo"
    priority: str = "normal"
    due_date: date | None = None
    person_id: uuid.UUID | None = None
    asset_id: uuid.UUID | None = None
    subscription_id: uuid.UUID | None = None
    tags: list[str] = []  # slugs from "task-tags" vocabulary


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date: date | None = None
    person_id: uuid.UUID | None = None
    asset_id: uuid.UUID | None = None
    subscription_id: uuid.UUID | None = None
    tags: list[str] | None = None


class TaskPublicRead(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    description: str | None
    status: str
    priority: str
    due_date: date | None
    completed_at: datetime | None
    person_id: uuid.UUID | None
    asset_id: uuid.UUID | None
    subscription_id: uuid.UUID | None
    tags: list[TermSlim]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskSummary(BaseModel):
    total: int
    by_status: dict[str, int]
    overdue: int
    due_today: int
