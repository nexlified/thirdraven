import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.vocabulary import TermSlim


class ProductCreate(BaseModel):
    name: str
    brand: str | None = None
    category: str | None = None  # term slug from product-categories
    unit: str | None = None
    barcode: str | None = None
    priceraven_product_id: str | None = None
    notes: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    brand: str | None = None
    category: str | None = None
    unit: str | None = None
    barcode: str | None = None
    priceraven_product_id: str | None = None
    notes: str | None = None


class ProductPublic(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    brand: str | None
    category: TermSlim | None
    unit: str | None
    barcode: str | None
    priceraven_product_id: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductSlim(BaseModel):
    id: uuid.UUID
    name: str
    brand: str | None
    unit: str | None

    model_config = {"from_attributes": True}
