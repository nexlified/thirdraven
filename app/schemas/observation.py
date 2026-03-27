import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.vocabulary import TermSlim


class ObservationCreate(BaseModel):
    body: str
    observed_on: date | None = None
    source: str | None = None
    context: str | None = None  # "personal" | "professional" | "mixed"
    is_sensitive: bool = False
    tags: list[str] = []  # slugs from "observation-tags" vocabulary


class ObservationUpdate(BaseModel):
    body: str | None = None
    observed_on: date | None = None
    source: str | None = None
    context: str | None = None  # "personal" | "professional" | "mixed"
    is_sensitive: bool | None = None
    tags: list[str] | None = None


class ObservationPublic(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    owner_id: uuid.UUID
    body: str
    observed_on: date | None
    source: str | None
    context: str | None
    is_sensitive: bool
    tags: list[TermSlim]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
