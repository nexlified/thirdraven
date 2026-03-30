import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.asset_extensions import (
    DigitalAssetPublic,
    DocumentAssetPublic,
    FinancialAssetPublic,
    PhysicalAssetPublic,
)
from app.schemas.vocabulary import TermSlim


class AssetCreate(BaseModel):
    name: str
    category: str  # slug from "asset-categories" vocabulary
    status: str = "active"  # slug from "asset-statuses" vocabulary
    description: str | None = None
    vendor: str | None = None
    purchase_date: date | None = None
    purchase_price: float | None = None
    purchase_price_currency: str | None = None  # ISO 4217
    current_value: float | None = None
    tags: list[str] = []  # slugs from "asset-tags" vocabulary
    location_note: str | None = None
    image_url: str | None = None
    purchase_url: str | None = None
    notes: str | None = None


class AssetUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    status: str | None = None
    description: str | None = None
    vendor: str | None = None
    purchase_date: date | None = None
    purchase_price: float | None = None
    purchase_price_currency: str | None = None
    current_value: float | None = None
    tags: list[str] | None = None
    location_note: str | None = None
    image_url: str | None = None
    purchase_url: str | None = None
    notes: str | None = None


class AssetPublicRead(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    category: TermSlim
    status: TermSlim
    description: str | None
    vendor: str | None
    purchase_date: date | None
    purchase_price: float | None
    purchase_price_currency: str | None
    current_value: float | None
    tags: list[TermSlim]
    location_note: str | None = None
    image_url: str | None = None
    purchase_url: str | None = None
    notes: str | None
    # Optional extension sections (loaded via ?include=)
    physical: PhysicalAssetPublic | None = None
    document: DocumentAssetPublic | None = None
    financial: FinancialAssetPublic | None = None
    digital: DigitalAssetPublic | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
