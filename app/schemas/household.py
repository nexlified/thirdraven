import uuid
from datetime import datetime

from pydantic import BaseModel


class HouseholdCreate(BaseModel):
    name: str


class HouseholdInvite(BaseModel):
    username: str


class HouseholdMemberPublic(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    username: str
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class HouseholdPublic(BaseModel):
    id: uuid.UUID
    name: str
    created_by: uuid.UUID
    members: list[HouseholdMemberPublic]
    created_at: datetime

    model_config = {"from_attributes": True}
