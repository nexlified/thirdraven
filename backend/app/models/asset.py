import uuid
from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel


class Asset(SQLModel, table=True):
    __tablename__ = "asset"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    name: str
    category_term_id: uuid.UUID = Field(foreign_key="term.id")
    status_term_id: uuid.UUID = Field(foreign_key="term.id")
    description: str | None = None
    vendor: str | None = None
    purchase_date: date | None = None
    purchase_price: float | None = None
    purchase_price_currency: str | None = None  # ISO 4217
    current_value: float | None = None
    location_note: str | None = None
    image_url: str | None = None
    purchase_url: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None
