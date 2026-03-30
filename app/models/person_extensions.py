import uuid
from datetime import date, datetime

from sqlmodel import Field, SQLModel


class PersonProfile(SQLModel, table=True):
    __tablename__ = "person_profile"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", unique=True, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    middle_name: str | None = None
    prefix_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    date_of_birth: date | None = None
    gender_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    nationality_country_id: uuid.UUID | None = Field(
        default=None, foreign_key="country.id"
    )


class PersonProfessional(SQLModel, table=True):
    __tablename__ = "person_professional"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", unique=True, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    occupation_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    company: str | None = None
    job_title: str | None = None


class PersonLocation(SQLModel, table=True):
    __tablename__ = "person_location"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", unique=True, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    timezone_id: uuid.UUID | None = Field(default=None, foreign_key="timezone.id")


class PersonContext(SQLModel, table=True):
    __tablename__ = "person_context"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", unique=True, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    how_we_met: str | None = None
    first_met_on: date | None = None
    last_contacted_on: date | None = None
    contact_frequency_days: int | None = None
    preferred_contact_term_id: uuid.UUID | None = Field(
        default=None, foreign_key="term.id"
    )
    relationship_nature: str | None = None  # "personal" | "professional" | "mixed"


class PersonChannel(SQLModel, table=True):
    """Generic contact channel — replaces PersonContactMethod + PersonSocial."""

    __tablename__ = "person_channel"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", index=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id")
    type: str  # "email" | "mobile" | "phone" | "whatsapp" | "telegram" |
               # "discord" | "twitter" | "instagram" | "github" |
               # "facebook" | "linkedin" | "website" | ...
    value: str
    label: str | None = None  # "work" | "personal" | etc.
    is_primary: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PersonAddress(SQLModel, table=True):
    """Generic address — any number per person with a free type label."""

    __tablename__ = "person_address"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", index=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id")
    type: str = "home"  # "home" | "work" | "other"
    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country_id: uuid.UUID | None = Field(default=None, foreign_key="country.id")
    lat: float | None = None
    lng: float | None = None
    is_primary: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

