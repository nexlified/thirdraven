import uuid
from datetime import date, datetime

from sqlmodel import Field, SQLModel


class Asset(SQLModel, table=True):
    __tablename__ = "asset"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    name: str
    category_term_id: uuid.UUID = Field(foreign_key="term.id")
    status_term_id: uuid.UUID = Field(foreign_key="term.id")
    description: str | None = None
    serial_number: str | None = None
    vendor: str | None = None
    purchase_date: date | None = None
    purchase_price: float | None = None
    current_value: float | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None
