import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.vocabulary import TermSlim


class DocumentCreate(BaseModel):
    # Valid values: "asset" | "tracked_record" | "subscription" | "person" | "general"
    entity_type: str
    entity_id: uuid.UUID | None = None
    doc_type: str  # vocab slug from "document-types"
    title: str
    file_path: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    issued_on: date | None = None
    expires_on: date | None = None
    notes: str | None = None


class DocumentUpdate(BaseModel):
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    doc_type: str | None = None
    title: str | None = None
    file_path: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    issued_on: date | None = None
    expires_on: date | None = None
    notes: str | None = None


class DocumentPublic(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID | None
    doc_type: TermSlim
    title: str
    file_path: str | None
    file_name: str | None
    file_size: int | None
    mime_type: str | None
    issued_on: date | None
    expires_on: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
