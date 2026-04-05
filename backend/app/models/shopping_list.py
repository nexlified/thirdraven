import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _naive_utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class ShoppingList(SQLModel, table=True):
    __tablename__ = "shopping_list"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    name: str
    is_active: bool = Field(default=True)
    notes: str | None = None
    created_at: datetime = Field(default_factory=_naive_utc_now)
    updated_at: datetime = Field(default_factory=_naive_utc_now)
    deleted_at: datetime | None = None


class ShoppingListItem(SQLModel, table=True):
    __tablename__ = "shopping_list_item"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    list_id: uuid.UUID = Field(foreign_key="shopping_list.id", index=True)
    product_id: uuid.UUID | None = Field(
        default=None, foreign_key="product.id", index=True
    )
    name: str
    quantity: float = Field(default=1.0)
    unit: str | None = None
    estimated_price: float | None = None
    source: str | None = None  # "auto" | "manual"
    is_checked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_naive_utc_now)
    updated_at: datetime = Field(default_factory=_naive_utc_now)
