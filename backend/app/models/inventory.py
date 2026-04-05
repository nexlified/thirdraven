import uuid
from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel, UniqueConstraint


def _naive_utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class InventoryProfile(SQLModel, table=True):
    __tablename__ = "inventory_profile"
    __table_args__ = (
        UniqueConstraint("owner_id", "product_id", name="uq_inventory_owner_product"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    product_id: uuid.UUID = Field(foreign_key="product.id", index=True)
    is_consumable: bool = Field(default=True)
    restock_unit: str
    reorder_threshold: float
    typical_monthly_usage: float
    current_stock: float
    last_restocked_on: date | None = None
    estimated_depletion_date: date | None = None
    preferred_source: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=_naive_utc_now)
    updated_at: datetime = Field(default_factory=_naive_utc_now)
