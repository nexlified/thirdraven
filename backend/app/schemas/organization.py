import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.iso_reference import CountrySlim
from app.schemas.vocabulary import TermSlim


class OrgCreate(BaseModel):
    name: str
    type: str | None = None  # slug from "org-types"
    description: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    industry: str | None = None  # slug from "industries"
    founded_year: int | None = None
    headquarters_city: str | None = None
    country: str | None = None  # ISO alpha2
    linkedin_url: str | None = None
    notes: str | None = None
    visibility: str = "private"  # "private" | "household"


class OrgUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    industry: str | None = None
    founded_year: int | None = None
    headquarters_city: str | None = None
    country: str | None = None
    linkedin_url: str | None = None
    notes: str | None = None
    visibility: str | None = None  # "private" | "household"


class OrgSlim(BaseModel):
    id: uuid.UUID
    name: str
    type: TermSlim | None
    headquarters_city: str | None
    country: CountrySlim | None

    model_config = {"from_attributes": True}


class OrgPublic(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    type: TermSlim | None
    description: str | None
    website: str | None
    email: str | None
    phone: str | None
    industry: TermSlim | None
    founded_year: int | None
    headquarters_city: str | None
    country: CountrySlim | None
    linkedin_url: str | None
    notes: str | None
    visibility: str
    household_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PersonOrgCreate(BaseModel):
    org_id: uuid.UUID
    role: str | None = None
    is_current: bool = True
    started_on: date | None = None
    ended_on: date | None = None


class PersonOrgUpdate(BaseModel):
    role: str | None = None
    is_current: bool | None = None
    started_on: date | None = None
    ended_on: date | None = None


class PersonOrgPublic(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    org: OrgSlim
    role: str | None
    is_current: bool
    started_on: date | None
    ended_on: date | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
