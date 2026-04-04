import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.transaction import CategoryBreakdown


class AssetSummaryItem(BaseModel):
    asset_id: uuid.UUID
    name: str
    account_type: str | None
    institution: str | None
    current_balance: float | None
    currency: str | None


class LoanSummaryItem(BaseModel):
    loan_id: uuid.UUID
    direction: str  # "lent" | "borrowed"
    person_name: str
    amount: float | None
    currency: str | None
    status: str
    due_on: date | None


class FinanceOverview(BaseModel):
    financial_assets: list[AssetSummaryItem]
    total_asset_value_by_currency: dict[str, float]

    outstanding_loans: list[LoanSummaryItem]
    total_lent_by_currency: dict[str, float]
    total_borrowed_by_currency: dict[str, float]

    current_month_income: float
    current_month_expenses: float
    current_month_net: float
    current_month_savings_rate: float | None
    current_month_currency: str

    top_expense_categories: list[CategoryBreakdown]

    monthly_subscription_cost_by_currency: dict[str, float]

    as_of: datetime
