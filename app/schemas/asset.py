import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.vocabulary import TermSlim


class AssetCreate(BaseModel):
    name: str
    category: str  # slug from "asset-categories" vocabulary
    status: str = "active"  # slug from "asset-statuses" vocabulary
    description: str | None = None
    serial_number: str | None = None
    vendor: str | None = None
    purchase_date: date | None = None
    purchase_price: float | None = None
    current_value: float | None = None
    tags: list[str] = []  # slugs from "asset-tags" vocabulary
    notes: str | None = None


class AssetUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    status: str | None = None
    description: str | None = None
    serial_number: str | None = None
    vendor: str | None = None
    purchase_date: date | None = None
    purchase_price: float | None = None
    current_value: float | None = None
    tags: list[str] | None = None
    notes: str | None = None


class AssetPublicRead(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    category: TermSlim
    status: TermSlim
    description: str | None
    serial_number: str | None
    vendor: str | None
    purchase_date: date | None
    purchase_price: float | None
    current_value: float | None
    tags: list[TermSlim]
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
