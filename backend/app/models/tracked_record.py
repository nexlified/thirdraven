import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class TrackedRecord(SQLModel, table=True):
    __tablename__ = "tracked_record"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    record_type_id: uuid.UUID = Field(foreign_key="term.id", index=True)

    title: str
    reference_number: str | None = None  # policy no., license no., cert no.
    issuer: str | None = None  # "Apple", "HDFC ERGO", "RTO Delhi"

    issued_on: date | None = None
    expires_on: date | None = None
    reminder_days: int = Field(default=30)  # flag N days before expiry

    cost: float | None = None
    currency: str | None = None  # ISO 4217
    billing_frequency: str | None = None  # "one-time" | "monthly" | "annual" etc.
    auto_renews: bool = Field(default=False)

    coverage_notes: str | None = None  # what's covered / scope of license
    metadata_: dict[str, Any] | None = Field(
        default=None, sa_column=Column("metadata", JSON, nullable=True)
    )

    # Optional cross-references
    asset_id: uuid.UUID | None = Field(default=None, foreign_key="asset.id")
    person_id: uuid.UUID | None = Field(default=None, foreign_key="person.id")

    notes: str | None = None
    deleted_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
