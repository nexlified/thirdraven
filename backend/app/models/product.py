import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _naive_utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Product(SQLModel, table=True):
    __tablename__ = "product"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True, nullable=False)
    name: str
    brand: str | None = None
    category_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    unit: str | None = None
    barcode: str | None = None
    priceraven_product_id: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=_naive_utc_now)
    updated_at: datetime = Field(default_factory=_naive_utc_now)
    deleted_at: datetime | None = None
