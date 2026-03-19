import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.vocabulary import TermSlim


class SubscriptionCreate(BaseModel):
    name: str
    provider: str | None = None
    category: str | None = None  # slug from "subscription-categories" vocabulary
    status: str = "active"
    cost: float
    currency: str = "USD"
    billing_cycle: str = "monthly"
    billing_cycle_days: int | None = None
    started_on: date | None = None
    next_billing_date: date | None = None
    trial_ends_on: date | None = None
    auto_renews: bool = True
    url: str | None = None
    notes: str | None = None
    asset_id: uuid.UUID | None = None
    tags: list[str] = []  # slugs from "subscription-tags" vocabulary


class SubscriptionUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    category: str | None = None
    status: str | None = None
    cost: float | None = None
    currency: str | None = None
    billing_cycle: str | None = None
    billing_cycle_days: int | None = None
    started_on: date | None = None
    next_billing_date: date | None = None
    trial_ends_on: date | None = None
    cancelled_on: date | None = None
    auto_renews: bool | None = None
    url: str | None = None
    notes: str | None = None
    asset_id: uuid.UUID | None = None
    tags: list[str] | None = None


class SubscriptionPublicRead(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    provider: str | None
    category: TermSlim | None
    status: str
    cost: float
    currency: str
    billing_cycle: str
    billing_cycle_days: int | None
    started_on: date | None
    next_billing_date: date | None
    trial_ends_on: date | None
    cancelled_on: date | None
    auto_renews: bool
    url: str | None
    notes: str | None
    asset_id: uuid.UUID | None
    tags: list[TermSlim]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Payment schemas ─────────────────────────────────────────────────────────────


class BillPaymentCreate(BaseModel):
    amount: float
    currency: str = "USD"
    billing_date: date
    due_date: date | None = None
    paid_on: date | None = None
    status: str = "pending"
    notes: str | None = None


class BillPaymentUpdate(BaseModel):
    amount: float | None = None
    currency: str | None = None
    billing_date: date | None = None
    due_date: date | None = None
    paid_on: date | None = None
    status: str | None = None
    notes: str | None = None


class BillPaymentPublicRead(BaseModel):
    id: uuid.UUID
    subscription_id: uuid.UUID
    owner_id: uuid.UUID
    amount: float
    currency: str
    billing_date: date
    due_date: date | None
    paid_on: date | None
    status: str
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Summary schema ──────────────────────────────────────────────────────────────


class UpcomingRenewal(BaseModel):
    id: uuid.UUID
    name: str
    cost: float
    currency: str
    next_billing_date: date


class CategorySpend(BaseModel):
    category: str  # term name or "Uncategorized"
    monthly_cost: float


class SubscriptionSummary(BaseModel):
    total_active: int
    total_monthly_cost: float
    upcoming_renewals: list[UpcomingRenewal]  # next 30 days
    cost_by_category: list[CategorySpend]
