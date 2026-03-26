import uuid
from datetime import date, datetime

from sqlmodel import Field, SQLModel


class Organization(SQLModel, table=True):
    __tablename__ = "organization"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)

    name: str
    type_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    description: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    industry_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    founded_year: int | None = None
    headquarters_city: str | None = None
    country_id: uuid.UUID | None = Field(default=None, foreign_key="country.id")
    linkedin_url: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None


class PersonOrganization(SQLModel, table=True):
    __tablename__ = "person_organization"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", index=True)
    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)

    role: str | None = None
    is_current: bool = Field(default=True)
    started_on: date | None = None
    ended_on: date | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
