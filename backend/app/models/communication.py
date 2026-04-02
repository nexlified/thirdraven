import uuid
from datetime import datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Communication(SQLModel, table=True):
    __tablename__ = "communication"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)

    channel: str  # vocab slug: "email" | "whatsapp" | "telegram" etc.
    direction: str = "inbound"  # "inbound" | "outbound"
    status: str = "raw"  # "raw" | "matched" | "placeholder" | "unmatched" | "ignored"
    is_bot: bool = Field(default=False)  # auto-set when matched person is_bot=True

    # Source identification
    sender_identifier: str | None = None  # email addr, phone no., @handle
    recipient_identifiers: list | None = Field(
        default=None,
        sa_column=Column("recipient_identifiers", JSON, nullable=True),
    )
    source_app: str | None = None  # "gmail", "outlook", "slack-workspace"
    external_id: str | None = None  # source message ID (for deduplication)
    thread_id: str | None = None  # conversation thread grouping

    # Content
    subject: str | None = None
    body: str | None = None
    raw_payload: dict | None = Field(
        default=None, sa_column=Column("raw_payload", JSON, nullable=True)
    )

    communicated_at: datetime | None = None  # when message was originally sent
    processed_at: datetime | None = None  # when matched/processed

    # Resolved links
    person_id: uuid.UUID | None = Field(default=None, foreign_key="person.id")
    interaction_id: uuid.UUID | None = Field(default=None, foreign_key="interaction.id")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
