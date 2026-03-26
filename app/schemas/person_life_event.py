import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.vocabulary import TermSlim  # noqa: F401 (re-used by LifeEventPublic)

# ── Life Event schemas ─────────────────────────────────────────────────────────


class LifeEventCreate(BaseModel):
    title: str
    event_type: str | None = None  # slug from "life-event-types" vocabulary
    description: str | None = None
    occurred_on: date | None = None
    occurred_year: int | None = None
    metadata_: dict[str, Any] | None = None


class LifeEventUpdate(BaseModel):
    title: str | None = None
    event_type: str | None = None
    description: str | None = None
    occurred_on: date | None = None
    occurred_year: int | None = None
    metadata_: dict[str, Any] | None = None


class LifeEventPublic(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    owner_id: uuid.UUID
    event_type: TermSlim | None
    title: str
    description: str | None
    occurred_on: date | None
    occurred_year: int | None
    metadata_: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Significant Date schemas ───────────────────────────────────────────────────


class SignificantDateCreate(BaseModel):
    label: str
    month: int
    day: int
    year: int | None = None
    recurs_annually: bool = True
    notes: str | None = None


class SignificantDateUpdate(BaseModel):
    label: str | None = None
    month: int | None = None
    day: int | None = None
    year: int | None = None
    recurs_annually: bool | None = None
    notes: str | None = None


class SignificantDatePublic(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    label: str
    month: int
    day: int
    year: int | None
    recurs_annually: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
