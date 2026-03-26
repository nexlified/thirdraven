import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, model_validator

from app.schemas.vocabulary import TermSlim


class RecordCreate(BaseModel):
    record_type: str  # vocab slug e.g. "insurance-vehicle", "license-driving"
    title: str
    reference_number: str | None = None
    issuer: str | None = None
    issued_on: date | None = None
    expires_on: date | None = None
    reminder_days: int = 30
    cost: float | None = None
    currency: str | None = None
    billing_frequency: str | None = None
    auto_renews: bool = False
    coverage_notes: str | None = None
    metadata_: dict[str, Any] | None = None
    asset_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None
    notes: str | None = None


class RecordUpdate(BaseModel):
    record_type: str | None = None
    title: str | None = None
    reference_number: str | None = None
    issuer: str | None = None
    issued_on: date | None = None
    expires_on: date | None = None
    reminder_days: int | None = None
    cost: float | None = None
    currency: str | None = None
    billing_frequency: str | None = None
    auto_renews: bool | None = None
    coverage_notes: str | None = None
    metadata_: dict[str, Any] | None = None
    asset_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None
    notes: str | None = None


class RecordPublic(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    record_type: TermSlim
    title: str
    reference_number: str | None
    issuer: str | None
    issued_on: date | None
    expires_on: date | None
    reminder_days: int
    cost: float | None
    currency: str | None
    billing_frequency: str | None
    auto_renews: bool
    coverage_notes: str | None
    metadata_: dict[str, Any] | None
    asset_id: uuid.UUID | None
    person_id: uuid.UUID | None
    notes: str | None
    is_expired: bool
    days_until_expiry: int | None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _compute_expiry_fields(cls, values: Any) -> Any:
        # Computed fields are set by the CRUD layer, not here
        return values

    model_config = {"from_attributes": True}
