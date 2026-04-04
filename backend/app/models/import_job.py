import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class ImportJob(SQLModel, table=True):
    __tablename__ = "import_job"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    data_type: str  # "contact" | "transaction" | ...
    source_format: str  # "csv" | "json" | "vcard"
    status: str = Field(default="pending")  # pending|processing|completed|failed
    raw_data: str
    total_rows: int | None = None
    processed_rows: int = Field(default=0)
    error: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    completed_at: datetime | None = None
