import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TermSlim(BaseModel):
    id: uuid.UUID
    name: str
    slug: str

    model_config = {"from_attributes": True}


class VocabularyCreate(BaseModel):
    name: str
    machine_name: str
    description: str | None = None
    is_hierarchical: bool = False
    allows_new_terms: bool = True
    is_locked: bool = False
    source_type: str = "internal"
    external_provider: str | None = None


class VocabularyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    allows_new_terms: bool | None = None
    external_provider: str | None = None
    is_active: bool | None = None


class VocabularyPublic(BaseModel):
    id: uuid.UUID
    name: str
    machine_name: str
    description: str | None
    is_hierarchical: bool
    allows_new_terms: bool
    is_locked: bool
    source_type: str
    external_provider: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TermCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    parent_id: uuid.UUID | None = None
    weight: int = 0
    external_id: str | None = None
    metadata_: dict[str, Any] | None = None


class TermUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    parent_id: uuid.UUID | None = None
    weight: int | None = None
    external_id: str | None = None
    metadata_: dict[str, Any] | None = None
    is_active: bool | None = None


class TermPublic(BaseModel):
    id: uuid.UUID
    vocabulary_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    parent_id: uuid.UUID | None
    weight: int
    external_id: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
