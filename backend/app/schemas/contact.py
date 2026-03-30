import uuid
from datetime import datetime

from pydantic import BaseModel


class ContactCreate(BaseModel):
    first_name: str
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None
    tags: list[str] = []


class ContactUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None
    tags: list[str] | None = None


class RelationshipPublic(BaseModel):
    id: uuid.UUID
    from_contact_id: uuid.UUID
    to_contact_id: uuid.UUID
    label: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ContactPublicRead(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    first_name: str
    last_name: str | None
    email: str | None
    phone: str | None
    notes: str | None
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContactWithRelationships(ContactPublicRead):
    relationships: list[RelationshipPublic] = []


class RelationshipCreate(BaseModel):
    to_contact_id: uuid.UUID
    label: str
