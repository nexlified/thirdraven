import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class RavenQuestion(SQLModel, table=True):
    __tablename__ = "raven_question"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    job_id: uuid.UUID = Field(foreign_key="import_job.id")
    import_row_id: uuid.UUID = Field(foreign_key="import_row.id")
    question: str
    context_snapshot: str  # JSON — row + candidates for UI display
    status: str = Field(default="pending")  # "pending" | "answered"
    answer: str | None = None
    answered_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
