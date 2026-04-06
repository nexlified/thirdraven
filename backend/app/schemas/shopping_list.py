import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.product import ProductSlim


class ShoppingListCreate(BaseModel):
    name: str
    store_name: str | None = None
    planned_date: date | None = None


class ShoppingListUpdate(BaseModel):
    name: str | None = None
    store_name: str | None = None
    planned_date: date | None = None


class ShoppingListItemCreate(BaseModel):
    product_id: uuid.UUID | None = None
    raw_name: str
    quantity: float = 1.0
    unit: str | None = None
    estimated_price: float | None = None


class ShoppingListItemUpdate(BaseModel):
    quantity: float | None = None
    actual_price: float | None = None
    is_checked: bool | None = None


class ShoppingListItemPublic(BaseModel):
    id: uuid.UUID
    shopping_list_id: uuid.UUID
    product_id: uuid.UUID | None
    product: ProductSlim | None
    raw_name: str
    quantity: float
    unit: str | None
    estimated_price: float | None
    actual_price: float | None
    is_checked: bool
    source: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShoppingListPublic(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    store_name: str | None
    planned_date: date | None
    is_completed: bool
    completed_on: date | None
    is_active: bool
    notes: str | None
    items: list[ShoppingListItemPublic]
    item_count: int
    checked_count: int
    estimated_total: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
