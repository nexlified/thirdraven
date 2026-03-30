import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.vocabulary import TermSlim

# ── Life Event schemas ────────────────────────────────────────────────────────


class LifeEventParticipantCreate(BaseModel):
    person_id: uuid.UUID
    role: str | None = "primary"  # "primary" | "participant" | custom


class LifeEventCreate(BaseModel):
    title: str
    event_type: str | None = None  # slug from "life-event-types" vocabulary
    description: str | None = None
    occurred_on: date | None = None
    occurred_year: int | None = None
    emotion: str | None = None  # slug from "life-event-emotions" vocabulary
    cost: float | None = None
    currency: str | None = None  # ISO 4217
    duration_minutes: int | None = None
    place: str | None = None
    metadata_: dict[str, Any] | None = None
    participants: list[LifeEventParticipantCreate] = []


class LifeEventUpdate(BaseModel):
    title: str | None = None
    event_type: str | None = None
    description: str | None = None
    occurred_on: date | None = None
    occurred_year: int | None = None
    emotion: str | None = None
    cost: float | None = None
    currency: str | None = None
    duration_minutes: int | None = None
    place: str | None = None
    metadata_: dict[str, Any] | None = None


class LifeEventParticipantPublic(BaseModel):
    person_id: uuid.UUID
    first_name: str
    last_name: str | None
    role: str | None

    model_config = {"from_attributes": True}


class LifeEventPublic(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    event_type: TermSlim | None
    title: str
    description: str | None
    occurred_on: date | None
    occurred_year: int | None
    emotion: TermSlim | None
    cost: float | None
    currency: str | None
    duration_minutes: int | None
    place: str | None
    metadata_: dict[str, Any] | None
    participants: list[LifeEventParticipantPublic]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Significant Date schemas ─────────────────────────────────────────────────


class SignificantDateCreate(BaseModel):
    date_type: str | None = None  # slug from "significant-date-types" vocabulary
    label: str | None = None  # free-text override; at least one must be set
    month: int
    day: int
    year: int | None = None
    recurs_annually: bool = True
    notes: str | None = None


class SignificantDateUpdate(BaseModel):
    date_type: str | None = None
    label: str | None = None
    month: int | None = None
    day: int | None = None
    year: int | None = None
    recurs_annually: bool | None = None
    notes: str | None = None


class SignificantDatePublic(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    date_type: TermSlim | None = None
    label: str | None
    month: int
    day: int
    year: int | None
    recurs_annually: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
