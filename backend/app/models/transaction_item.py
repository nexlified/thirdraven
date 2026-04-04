import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _naive_utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class TransactionItem(SQLModel, table=True):
    __tablename__ = "transaction_item"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True, nullable=False)
    transaction_id: uuid.UUID = Field(
        foreign_key="transaction.id", index=True, nullable=False
    )
    product_id: uuid.UUID | None = Field(default=None, foreign_key="product.id")
    raw_name: str
    quantity: float
    unit: str | None = None
    unit_price: float
    total_price: float
    currency: str = Field(default="INR", max_length=3)
    discount: float = 0
    store_name: str | None = None
    import_batch_id: str | None = None
    created_at: datetime = Field(default_factory=_naive_utc_now)
    updated_at: datetime = Field(default_factory=_naive_utc_now)

