import uuid

from sqlmodel import Field, SQLModel


class ImportRow(SQLModel, table=True):
    __tablename__ = "import_row"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    job_id: uuid.UUID = Field(foreign_key="import_job.id", index=True)
    row_index: int
    raw_snapshot: str  # JSON of parsed row
    status: str  # created|merged|flagged|skipped|awaiting_answer|error
    target_id: uuid.UUID | None = None
    error_msg: str | None = None
    raven_log_id: uuid.UUID | None = None
