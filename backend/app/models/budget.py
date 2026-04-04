import uuid
from datetime import UTC, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def _naive_utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Budget(SQLModel, table=True):
    __tablename__ = "budget"
    __table_args__ = (
        UniqueConstraint(
            "owner_id",
            "category_term_id",
            "year",
            "month",
            name="uq_budget_owner_category_month",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True, nullable=False)
    category_term_id: uuid.UUID = Field(foreign_key="term.id", nullable=False)
    year: int
    month: int  # 1–12
    amount: float
    currency: str = Field(default="INR", max_length=3)
    notes: str | None = None
    created_at: datetime = Field(default_factory=_naive_utc_now)
    updated_at: datetime = Field(default_factory=_naive_utc_now)
