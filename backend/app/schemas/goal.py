import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

GoalType = Literal["aspiration", "fear", "current-focus", "learning"]


class GoalCreate(BaseModel):
    goal_type: GoalType
    body: str
    target_date: date | None = None


class GoalUpdate(BaseModel):
    goal_type: GoalType | None = None
    body: str | None = None
    target_date: date | None = None
    achieved: bool | None = None  # True = mark achieved, False = unmark


class GoalPublic(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    owner_id: uuid.UUID
    goal_type: str
    body: str
    target_date: date | None
    achieved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
