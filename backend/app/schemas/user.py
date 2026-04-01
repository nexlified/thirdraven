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


class UserPreferencesPublic(BaseModel):
    default_country: str
    default_timezone: str
    default_relationship_nature: str
    default_visibility: str
    default_closeness_level: int | None
    default_languages: list[str]


class UserPreferencesUpdate(BaseModel):
    default_country: str | None = None
    default_timezone: str | None = None
    default_relationship_nature: str | None = None
    default_visibility: str | None = None
    default_closeness_level: int | None = None
    default_languages: list[str] | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str


class MessageResponse(BaseModel):
    message: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
