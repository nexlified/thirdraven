import uuid
from datetime import datetime

from pydantic import BaseModel


class ImportRowPublic(BaseModel):
    row_index: int
    status: str
    target_id: uuid.UUID | None
    error_msg: str | None

    model_config = {"from_attributes": True}


class ImportJobPublic(BaseModel):
    id: uuid.UUID
    data_type: str
    status: str
    total_rows: int | None
    processed_rows: int
    pending_questions: int = 0
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class ImportJobDetail(ImportJobPublic):
    rows: list[ImportRowPublic] = []
