import uuid
from datetime import UTC, datetime

from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field, SQLModel


def _naive_utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Contact(SQLModel, table=True):
    __tablename__ = "contact"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    first_name: str
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None
    tags: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    created_at: datetime = Field(default_factory=_naive_utc_now)
    updated_at: datetime = Field(default_factory=_naive_utc_now)
    deleted_at: datetime | None = None
