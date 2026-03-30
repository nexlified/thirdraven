import uuid
from datetime import date, datetime

from sqlmodel import Field, SQLModel


class Loan(SQLModel, table=True):
    __tablename__ = "loan"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", index=True)

    direction: str  # "lent" | "borrowed"
    loan_type: str  # "money" | "item"
    description: str
    amount: float | None = None
    currency: str | None = None  # ISO 4217
    item_name: str | None = None
    loaned_on: date | None = None
    due_on: date | None = None
    returned_on: date | None = None
    # outstanding|returned|forgiven|disputed
    status: str = Field(default="outstanding")
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None
