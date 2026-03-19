import uuid
from datetime import date, datetime

from sqlmodel import Field, SQLModel


class PersonProfile(SQLModel, table=True):
    __tablename__ = "person_profile"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
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

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", unique=True, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    occupation_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    company: str | None = None
    job_title: str | None = None
    linkedin_url: str | None = None
    phone_secondary: str | None = None


class PersonSocial(SQLModel, table=True):
    __tablename__ = "person_social"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", unique=True, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    twitter_handle: str | None = None
    instagram_handle: str | None = None
    website_url: str | None = None


class PersonLocation(SQLModel, table=True):
    __tablename__ = "person_location"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", unique=True, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    address_home: str | None = None
    address_work: str | None = None
    city: str | None = None
    country_id: uuid.UUID | None = Field(default=None, foreign_key="country.id")
    timezone_id: uuid.UUID | None = Field(default=None, foreign_key="timezone.id")


class PersonContext(SQLModel, table=True):
    __tablename__ = "person_context"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", unique=True, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    how_we_met: str | None = None
    first_met_on: date | None = None
