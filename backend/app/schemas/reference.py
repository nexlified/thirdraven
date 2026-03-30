import uuid
from datetime import datetime

from pydantic import BaseModel


class PersonTermCreate(BaseModel):
    term_id: uuid.UUID
    context: str | None = None


class PersonTermPublic(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    term_id: uuid.UUID
    context: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
