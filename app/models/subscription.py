import uuid
from datetime import date, datetime

from sqlmodel import Field, SQLModel


class Subscription(SQLModel, table=True):
    __tablename__ = "subscription"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    name: str
    provider: str | None = None
    category_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    status: str = "active"  # active | trial | paused | cancelled | expired
    cost: float
    currency: str = "INR"
    payment_mode: str = "manual"  # "auto_debit" | "manual"
    # daily | weekly | monthly | quarterly | semi_annual | annual | custom
    billing_cycle: str = "monthly"
    billing_cycle_days: int | None = None  # only for custom cycle
    started_on: date | None = None
    next_billing_date: date | None = None
    trial_ends_on: date | None = None
    cancelled_on: date | None = None
    auto_renews: bool = True
    url: str | None = None
    notes: str | None = None
    asset_id: uuid.UUID | None = Field(default=None, foreign_key="asset.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None


class SubscriptionTag(SQLModel, table=True):
    __tablename__ = "subscription_tag"

    subscription_id: uuid.UUID = Field(foreign_key="subscription.id", primary_key=True)
    term_id: uuid.UUID = Field(foreign_key="term.id", primary_key=True)


class BillPayment(SQLModel, table=True):
    __tablename__ = "bill_payment"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    subscription_id: uuid.UUID = Field(foreign_key="subscription.id", index=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    amount: float
    currency: str = "INR"
    paid_amount: float | None = None
    paid_currency: str = "INR"
    exchange_rate: float | None = None
    payment_mode: str = "manual"  # "auto_debit" | "manual"
    billing_date: date
    due_date: date | None = None
    paid_on: date | None = None
    status: str = "pending"  # pending | paid | overdue | failed
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
