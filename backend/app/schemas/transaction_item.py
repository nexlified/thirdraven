import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.product import ProductSlim


class TransactionItemCreate(BaseModel):
    product_id: uuid.UUID | None = None
    raw_name: str
    quantity: float
    unit: str | None = None
    unit_price: float
    total_price: float
    currency: str = "INR"
    discount: float = 0.0
    store_name: str | None = None
    import_batch_id: str | None = None


class TransactionItemUpdate(BaseModel):
    product_id: uuid.UUID | None = None
    raw_name: str | None = None
    quantity: float | None = None
    unit: str | None = None
    unit_price: float | None = None
    total_price: float | None = None
    currency: str | None = None
    discount: float | None = None
    store_name: str | None = None


class TransactionItemPublic(BaseModel):
    id: uuid.UUID
    transaction_id: uuid.UUID
    product_id: uuid.UUID | None
    product: ProductSlim | None
    raw_name: str
    quantity: float
    unit: str | None
    unit_price: float
    total_price: float
    currency: str
    discount: float
    store_name: str | None
    import_batch_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
