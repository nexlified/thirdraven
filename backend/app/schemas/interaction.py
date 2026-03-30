import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class InteractionCreate(BaseModel):
    title: str
    interaction_type_id: uuid.UUID | None = None
    term_id: uuid.UUID | None = None
    occurred_on: date | None = None
    context: str | None = None  # "personal" | "professional" | "mixed"
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


class InteractionUpdate(BaseModel):
    title: str | None = None
    interaction_type_id: uuid.UUID | None = None
    term_id: uuid.UUID | None = None
    occurred_on: date | None = None
    context: str | None = None  # "personal" | "professional" | "mixed"
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


class InteractionPublicRead(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    owner_id: uuid.UUID
    interaction_type_id: uuid.UUID | None
    term_id: uuid.UUID | None
    title: str
    occurred_on: date | None
    context: str | None
    notes: str | None
    metadata_: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
