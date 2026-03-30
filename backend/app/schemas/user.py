import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str | None = None


class UserPublic(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    created_at: datetime
    person_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
