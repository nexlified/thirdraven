import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field, SQLModel


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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None
