import uuid
from datetime import date, datetime

from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    __tablename__ = "document"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)

    # Polymorphic soft reference — no DB FK, validated at app layer
    # Valid values: "asset" | "tracked_record" | "subscription" | "person" | "general"
    entity_type: str
    entity_id: uuid.UUID | None = None

    doc_type_id: uuid.UUID = Field(foreign_key="term.id")  # vocab: "document-types"
    title: str

    # File metadata — populated in Phase 2 by upload/OCR processing
    file_path: str | None = None
    file_name: str | None = None
    file_size: int | None = None  # bytes
    mime_type: str | None = None

    issued_on: date | None = None
    expires_on: date | None = None  # for docs with validity (insurance cert, visa copy)
    notes: str | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
