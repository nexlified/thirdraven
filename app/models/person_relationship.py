import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class PersonRelationship(SQLModel, table=True):
    __tablename__ = "person_relationship"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    from_person_id: uuid.UUID = Field(foreign_key="person.id", index=True)
    to_person_id: uuid.UUID = Field(foreign_key="person.id", index=True)
    label_term_id: uuid.UUID = Field(foreign_key="term.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
