import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.person import PersonSlim
from app.schemas.vocabulary import TermSlim


class EventCreate(BaseModel):
    title: str
    event_type: str | None = None  # slug from "event-types"
    description: str | None = None
    occurred_on: date | None = None
    location: str | None = None
    notes: str | None = None


class EventUpdate(BaseModel):
    title: str | None = None
    event_type: str | None = None
    description: str | None = None
    occurred_on: date | None = None
    location: str | None = None
    notes: str | None = None


class EventSlim(BaseModel):
    id: uuid.UUID
    title: str
    event_type: TermSlim | None
    occurred_on: date | None
    location: str | None

    model_config = {"from_attributes": True}


class EventPublic(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    event_type: TermSlim | None
    description: str | None
    occurred_on: date | None
    location: str | None
    notes: str | None
    persons: list[PersonSlim]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventPersonCreate(BaseModel):
    person_id: uuid.UUID
    role: str | None = None


class EventPersonPublic(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    person: PersonSlim
    role: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
