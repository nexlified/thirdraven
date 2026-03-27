import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


class Vocabulary(SQLModel, table=True):
    __tablename__ = "vocabulary"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    name: str
    machine_name: str = Field(index=True, unique=True)
    description: str | None = None
    is_hierarchical: bool = Field(default=False)
    allows_new_terms: bool = Field(default=True)
    is_locked: bool = Field(default=False)
    source_type: str = Field(default="internal")
    external_provider: str | None = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Term(SQLModel, table=True):
    __tablename__ = "term"
    __table_args__ = (UniqueConstraint("vocabulary_id", "slug"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    vocabulary_id: uuid.UUID = Field(foreign_key="vocabulary.id", index=True)
    name: str
    slug: str = Field(index=True)
    description: str | None = None
    parent_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    weight: int = Field(default=0)
    external_id: str | None = None
    metadata_: dict[str, Any] | None = Field(
        default=None, sa_column=Column("metadata", JSON, nullable=True)
    )
    reverse_slug: str | None = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PersonTag(SQLModel, table=True):
    __tablename__ = "person_tag"

    person_id: uuid.UUID = Field(foreign_key="person.id", primary_key=True)
    term_id: uuid.UUID = Field(foreign_key="term.id", primary_key=True)


class PersonLanguage(SQLModel, table=True):
    __tablename__ = "person_language"

    person_id: uuid.UUID = Field(foreign_key="person.id", primary_key=True)
    language_id: uuid.UUID = Field(foreign_key="language.id", primary_key=True)


class AssetTag(SQLModel, table=True):
    __tablename__ = "asset_tag"

    asset_id: uuid.UUID = Field(foreign_key="asset.id", primary_key=True)
    term_id: uuid.UUID = Field(foreign_key="term.id", primary_key=True)
