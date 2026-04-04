import uuid
from datetime import date, datetime

from pydantic import BaseModel, field_validator

from app.schemas.vocabulary import TermSlim


class TransactionCreate(BaseModel):
    transaction_type: str  # "expense" | "income"
    amount: float
    currency: str = "INR"
    transacted_on: date
    description: str
    category: str | None = None  # term slug, resolved at CRUD layer
    payment_method: str | None = None  # term slug
    asset_id: uuid.UUID | None = None
    subscription_id: uuid.UUID | None = None
    merchant: str | None = None
    reference: str | None = None
    tags: list[str] = []
    import_batch_id: str | None = None
    notes: str | None = None

    @field_validator("transaction_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("expense", "income"):
            raise ValueError("Must be 'expense' or 'income'")
        return v


class TransactionUpdate(BaseModel):
    transaction_type: str | None = None
    amount: float | None = None
    currency: str | None = None
    transacted_on: date | None = None
    description: str | None = None
    category: str | None = None
    payment_method: str | None = None
    asset_id: uuid.UUID | None = None
    subscription_id: uuid.UUID | None = None
    merchant: str | None = None
    reference: str | None = None
    tags: list[str] | None = None
    import_batch_id: str | None = None
    notes: str | None = None

    @field_validator("transaction_type")
    @classmethod
    def validate_type(cls, v: str | None) -> str | None:
        if v is not None and v not in ("expense", "income"):
            raise ValueError("Must be 'expense' or 'income'")
        return v


class TransactionPublic(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    transaction_type: str
    amount: float
    currency: str
    transacted_on: date
    description: str
    category: TermSlim | None
    payment_method: TermSlim | None
    asset_id: uuid.UUID | None
    subscription_id: uuid.UUID | None
    merchant: str | None
    reference: str | None
    tags: list[str]
    import_batch_id: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CategoryBreakdown(BaseModel):
    category_slug: str
    category_name: str
    total: float
    count: int
    percentage: float


class DailyTotal(BaseModel):
    date: date
    income: float
    expense: float


class TransactionSummary(BaseModel):
    period_from: date
    period_to: date
    total_income: float
    total_expense: float
    net: float
    savings_rate: float | None
    expense_by_category: list[CategoryBreakdown]
    income_by_category: list[CategoryBreakdown]
    daily_totals: list[DailyTotal]
    currency: str
