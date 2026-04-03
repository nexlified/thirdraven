import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


def _naive_utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Transaction(SQLModel, table=True):
    __tablename__ = "transaction"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True, nullable=False)
    transaction_type: str  # "expense" | "income"
    amount: float
    currency: str = Field(default="INR", max_length=3)
    transacted_on: date
    description: str
    category_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    payment_method_term_id: uuid.UUID | None = Field(
        default=None, foreign_key="term.id"
    )
    asset_id: uuid.UUID | None = Field(default=None, foreign_key="asset.id")
    subscription_id: uuid.UUID | None = Field(
        default=None, foreign_key="subscription.id"
    )
    merchant: str | None = None
    reference: str | None = None  # card last-4, UPI ref, cheque number
    tags: list[Any] | None = Field(default=None, sa_column=Column(JSON))
    import_batch_id: str | None = None  # groups bulk-imported rows
    notes: str | None = None
    created_at: datetime = Field(default_factory=_naive_utc_now)
    updated_at: datetime = Field(default_factory=_naive_utc_now)
    deleted_at: datetime | None = None
