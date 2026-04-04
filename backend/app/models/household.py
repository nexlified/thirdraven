import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Household(SQLModel, table=True):
    __tablename__ = "household"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    name: str
    created_by: uuid.UUID = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )


class HouseholdMember(SQLModel, table=True):
    __tablename__ = "household_member"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    household_id: uuid.UUID = Field(foreign_key="household.id", index=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", unique=True, index=True)
    role: str = Field(default="member")  # "admin" | "member"
    joined_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
