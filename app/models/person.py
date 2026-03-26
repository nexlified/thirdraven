import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class Person(SQLModel, table=True):
    __tablename__ = "person"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None

    # Identity
    first_name: str
    last_name: str | None = None
    nickname: str | None = None

    # Primary contact
    email: str | None = None
    phone: str | None = None

    # CRM essentials
    notes: str | None = None
    closeness_level: int | None = None
