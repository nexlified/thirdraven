import uuid
from datetime import date, datetime

from pydantic import BaseModel, computed_field

from app.schemas.product import ProductSlim


class InventoryProfileCreate(BaseModel):
    is_consumable: bool = True
    restock_unit: str
    reorder_threshold: float
    typical_monthly_usage: float
    current_stock: float
    last_restocked_on: date | None = None
    preferred_source: str | None = None
    notes: str | None = None


class InventoryProfileUpdate(BaseModel):
    reorder_threshold: float | None = None
    typical_monthly_usage: float | None = None
    current_stock: float | None = None
    last_restocked_on: date | None = None
    preferred_source: str | None = None
    notes: str | None = None


class InventoryProfilePublic(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    product: ProductSlim
    is_consumable: bool
    restock_unit: str
    reorder_threshold: float
    typical_monthly_usage: float
    current_stock: float
    last_restocked_on: date | None
    estimated_depletion_date: date | None
    preferred_source: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[misc]  # Pydantic v2 computed_field on property
    @property
    def is_low_stock(self) -> bool:
        return self.current_stock <= self.reorder_threshold

    @computed_field  # type: ignore[misc]  # Pydantic v2 computed_field on property
    @property
    def days_until_depletion(self) -> int | None:
        if self.estimated_depletion_date is None:
            return None
        delta = self.estimated_depletion_date - date.today()
        return delta.days
