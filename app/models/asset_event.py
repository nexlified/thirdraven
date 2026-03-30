import uuid
from datetime import date, datetime

from sqlmodel import Field, SQLModel


class AssetEvent(SQLModel, table=True):
    __tablename__ = "asset_event"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    asset_id: uuid.UUID = Field(foreign_key="asset.id", index=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)

    # acquired|repaired|upgraded|valued|insured|lent|returned|sold|lost|disposed|other
    event_type: str
    occurred_on: date | None = None
    description: str | None = None
    cost: float | None = None
    currency: str | None = None  # ISO 4217
    vendor: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
