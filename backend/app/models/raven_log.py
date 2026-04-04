import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class RavenLog(SQLModel, table=True):
    __tablename__ = "raven_log"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(index=True)
    operation: str  # "import_check" | "import_recheck"
    input_snapshot: str  # JSON — normalized row
    candidates_snapshot: str  # JSON — [{id, name, email, phone}]
    user_answer: str | None = None
    decision: str  # created|merged|flagged|skipped|needs_clarification
    reasoning: str | None = None
    target_id: uuid.UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
