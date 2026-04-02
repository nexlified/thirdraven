import uuid
from datetime import date, datetime

from pydantic import BaseModel


class AssetEventCreate(BaseModel):
    event_type: str  # acquired|repaired|upgraded|valued|insured|lent
    # returned|sold|lost|disposed|other
    occurred_on: date | None = None
    description: str | None = None
    cost: float | None = None
    currency: str | None = None  # ISO 4217
    vendor: str | None = None


class AssetEventPublic(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    owner_id: uuid.UUID
    event_type: str
    occurred_on: date | None
    description: str | None
    cost: float | None
    currency: str | None
    vendor: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
