import uuid
from datetime import date

from pydantic import BaseModel


class RenewalEntry(BaseModel):
    entity_type: str  # "tracked_record" | "subscription"
    entity_id: uuid.UUID
    title: str
    record_type: str | None  # vocabulary slug for tracked_record; None for subscription
    expires_on: date
    days_remaining: int
    auto_renews: bool | None
    cost: float | None
    currency: str | None
    asset_id: uuid.UUID | None
    person_id: uuid.UUID | None
