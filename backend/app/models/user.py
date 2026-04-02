import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    preferences: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=sa.Column(sa.JSON, nullable=True),
    )
    reset_password_token_hash: str | None = Field(default=None, nullable=True)
    reset_password_token_expires_at: datetime | None = Field(
        default=None, nullable=True
    )

    # Link to the user's own Person record (set after creation).
    # use_alter defers the FK constraint so the circular person→user→person
    # dependency is resolved at migration time.
    person_id: uuid.UUID | None = Field(
        default=None,
        sa_column=sa.Column(
            sa.Uuid,
            sa.ForeignKey("person.id", use_alter=True, name="fk_user_person_id"),
            nullable=True,
        ),
    )
