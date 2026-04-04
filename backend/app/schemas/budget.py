import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.schemas.vocabulary import TermSlim


class BudgetCreate(BaseModel):
    category: str  # slug from expense-categories vocabulary
    year: int
    month: int  # 1–12
    amount: float
    currency: str = "INR"
    notes: str | None = None

    @field_validator("month")
    @classmethod
    def validate_month(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError("Month must be between 1 and 12")
        return v


class BudgetUpdate(BaseModel):
    amount: float | None = None
    notes: str | None = None


class BudgetPublic(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    category: TermSlim
    year: int
    month: int
    amount: float
    currency: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BudgetWithSpend(BudgetPublic):
    spent: float
    remaining: float
    utilization: float
