import uuid
from datetime import date, datetime

from pydantic import BaseModel


class LoanCreate(BaseModel):
    person_id: uuid.UUID
    direction: str  # "lent" | "borrowed"
    loan_type: str  # "money" | "item"
    description: str
    amount: float | None = None
    currency: str | None = None  # ISO 4217
    item_name: str | None = None
    loaned_on: date | None = None
    due_on: date | None = None
    notes: str | None = None


class LoanUpdate(BaseModel):
    description: str | None = None
    amount: float | None = None
    currency: str | None = None
    item_name: str | None = None
    loaned_on: date | None = None
    due_on: date | None = None
    returned_on: date | None = None
    status: str | None = None  # "outstanding"|"returned"|"forgiven"|"disputed"
    notes: str | None = None


class LoanPublic(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    person_id: uuid.UUID
    direction: str
    loan_type: str
    description: str
    amount: float | None
    currency: str | None
    item_name: str | None
    loaned_on: date | None
    due_on: date | None
    returned_on: date | None
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
