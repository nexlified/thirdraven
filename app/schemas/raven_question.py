import uuid
from datetime import datetime

from pydantic import BaseModel


class RavenQuestionPublic(BaseModel):
    id: uuid.UUID
    question: str
    context_snapshot: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RavenAnswerRequest(BaseModel):
    answer: str
