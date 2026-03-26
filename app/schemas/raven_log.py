import uuid
from datetime import datetime

from pydantic import BaseModel


class RavenLogPublic(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    operation: str
    input_snapshot: str
    candidates_snapshot: str
    user_answer: str | None
    decision: str
    reasoning: str | None
    target_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
