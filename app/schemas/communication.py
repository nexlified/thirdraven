import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CommIngest(BaseModel):
    """Flexible ingest schema — unknown fields fold into raw_payload."""

    channel: str
    direction: str = "inbound"
    sender: str | None = None  # → sender_identifier
    recipients: list[str] | None = None  # → recipient_identifiers
    source_app: str | None = None
    external_id: str | None = None
    thread_id: str | None = None
    subject: str | None = None
    body: str | None = None
    communicated_at: datetime | None = None
    extra: dict[str, Any] | None = None  # explicitly named extras → raw_payload

    model_config = {"extra": "allow"}  # unknown fields captured via __pydantic_extra__

    def build_raw_payload(self) -> dict[str, Any] | None:
        """Merge extra + any unknown fields into a single raw_payload dict."""
        extra_fields: dict[str, Any] = dict(self.__pydantic_extra__ or {})
        if self.extra:
            extra_fields.update(self.extra)
        return extra_fields if extra_fields else None


class CommCreate(BaseModel):
    """Structured creation — all fields explicit."""

    channel: str
    direction: str = "inbound"
    sender_identifier: str | None = None
    recipient_identifiers: list[str] | None = None
    source_app: str | None = None
    external_id: str | None = None
    thread_id: str | None = None
    subject: str | None = None
    body: str | None = None
    communicated_at: datetime | None = None
    raw_payload: dict[str, Any] | None = None


class CommUpdate(BaseModel):
    person_id: uuid.UUID | None = None
    status: str | None = None
    subject: str | None = None
    body: str | None = None
    notes: str | None = None


class CommPublic(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    channel: str
    direction: str
    status: str
    sender_identifier: str | None
    recipient_identifiers: list[str] | None
    source_app: str | None
    external_id: str | None
    thread_id: str | None
    subject: str | None
    body: str | None
    raw_payload: dict[str, Any] | None
    communicated_at: datetime | None
    processed_at: datetime | None
    person_id: uuid.UUID | None
    interaction_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
