import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class ContactRelationship(SQLModel, table=True):
    __tablename__ = "contact_relationship"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    from_contact_id: uuid.UUID = Field(foreign_key="contact.id", index=True)
    to_contact_id: uuid.UUID = Field(foreign_key="contact.id", index=True)
    label: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
