import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.iso_reference import CountrySlim, LanguageSlim, TimezonePublic
from app.schemas.vocabulary import TermSlim


class RelatedPersonRef(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str | None
    nickname: str | None

    model_config = {"from_attributes": True}


class RelationshipCreate(BaseModel):
    to_person_id: uuid.UUID
    label: str  # slug from "relationship-types" vocabulary


class RelationshipUpdate(BaseModel):
    label: str  # new slug from "relationship-types" vocabulary


class RelationshipPublic(BaseModel):
    id: uuid.UUID
    person: RelatedPersonRef
    related_person: RelatedPersonRef
    label: TermSlim
    inverse_id: uuid.UUID | None
    created_at: datetime


# ── Address schemas ────────────────────────────────────────────────────────────


class AddressCreate(BaseModel):
    type: str = "home"  # "home" | "work" | "other"
    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str | None = None  # ISO alpha2 code
    lat: float | None = None
    lng: float | None = None
    is_primary: bool = False


class AddressPublic(BaseModel):
    id: uuid.UUID
    type: str
    street: str | None
    city: str | None
    postal_code: str | None
    country: CountrySlim | None
    lat: float | None
    lng: float | None
    is_primary: bool

    model_config = {"from_attributes": True}


# ── Channel schemas ────────────────────────────────────────────────────────────


class ChannelCreate(BaseModel):
    type: str  # "email" | "mobile" | "phone" | "whatsapp" | "telegram" | "discord" | ..
    value: str
    label: str | None = None  # "work" | "personal" | etc.
    is_primary: bool = False


class ChannelUpdate(BaseModel):
    type: str | None = None
    value: str | None = None
    label: str | None = None
    is_primary: bool | None = None


class ChannelPublic(BaseModel):
    id: uuid.UUID
    type: str
    value: str
    label: str | None
    is_primary: bool

    model_config = {"from_attributes": True}


# ── Request schemas (flat — CRUD routes fields to the correct tables) ──────────


class PersonCreate(BaseModel):
    first_name: str
    last_name: str | None = None
    nickname: str | None = None
    channels: list[ChannelCreate] = []
    addresses: list[AddressCreate] = []
    notes: str | None = None
    tags: list[str] = []  # slugs from "person-tags" vocabulary
    closeness_level: int | None = None
    # profile section
    middle_name: str | None = None
    prefix: str | None = None  # slug from "name-prefixes"
    date_of_birth: date | None = None
    gender: str | None = None  # slug from "genders"
    nationality: str | None = None  # ISO alpha2 country code
    languages: list[str] = []  # ISO 639-1 language codes
    # professional section
    occupation: str | None = None  # slug from "occupations"
    company: str | None = None
    job_title: str | None = None
    # location section
    timezone: str | None = None  # IANA timezone name
    # context section
    how_we_met: str | None = None
    first_met_on: date | None = None
    last_contacted_on: date | None = None
    contact_frequency_days: int | None = None
    preferred_contact: str | None = None  # slug from "contact-channels"
    relationship_nature: str | None = None  # "personal" | "professional" | "mixed"
    # household sharing
    visibility: str = "private"  # "private" | "household"
    # identity flags
    is_placeholder: bool = False
    is_bot: bool = False


class PersonUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    nickname: str | None = None
    channels: list[ChannelCreate] | None = None  # replaces all channels
    addresses: list[AddressCreate] | None = None  # replaces all addresses
    notes: str | None = None
    tags: list[str] | None = None
    closeness_level: int | None = None
    # profile section
    middle_name: str | None = None
    prefix: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    nationality: str | None = None
    languages: list[str] | None = None
    # professional section
    occupation: str | None = None
    company: str | None = None
    job_title: str | None = None
    # location section
    timezone: str | None = None
    # context section
    how_we_met: str | None = None
    first_met_on: date | None = None
    last_contacted_on: date | None = None
    contact_frequency_days: int | None = None
    preferred_contact: str | None = None
    relationship_nature: str | None = None  # "personal" | "professional" | "mixed"
    # household sharing
    visibility: str | None = None  # "private" | "household"
    # identity flags
    is_placeholder: bool | None = None
    is_bot: bool | None = None


# ── Response schemas ───────────────────────────────────────────────────────────


class PersonSlim(BaseModel):
    """Core response — always returned."""

    id: uuid.UUID
    owner_id: uuid.UUID
    first_name: str
    last_name: str | None
    nickname: str | None
    email: str | None
    phone: str | None
    notes: str | None
    tags: list[TermSlim]
    closeness_level: int | None
    visibility: str
    household_id: uuid.UUID | None
    is_placeholder: bool
    is_bot: bool
    is_self: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Extension section schemas (opt-in via ?include=) ──────────────────────────


class PersonProfileSection(BaseModel):
    middle_name: str | None = None
    prefix: TermSlim | None = None
    date_of_birth: date | None = None
    gender: TermSlim | None = None
    nationality: CountrySlim | None = None
    languages: list[LanguageSlim] = []

    model_config = {"from_attributes": True}


class PersonProfessionalSection(BaseModel):
    occupation: TermSlim | None = None
    company: str | None = None
    job_title: str | None = None

    model_config = {"from_attributes": True}


class PersonLocationSection(BaseModel):
    timezone: TimezonePublic | None = None
    addresses: list[AddressPublic] = []

    model_config = {"from_attributes": True}


class PersonContextSection(BaseModel):
    how_we_met: str | None = None
    first_met_on: date | None = None
    last_contacted_on: date | None = None
    contact_frequency_days: int | None = None
    preferred_contact: TermSlim | None = None
    relationship_nature: str | None = None  # "personal" | "professional" | "mixed"

    model_config = {"from_attributes": True}


class PersonExtended(PersonSlim):
    """Slim core + opt-in extension sections."""

    profile: PersonProfileSection | None = None
    professional: PersonProfessionalSection | None = None
    location: PersonLocationSection | None = None
    context: PersonContextSection | None = None
    channels: list[ChannelPublic] | None = None


class PersonWithRelationships(PersonExtended):
    relationships: list[RelationshipPublic] = []


# Alias kept for any stale internal references
PersonPublicRead = PersonSlim


# ── Schema metadata (field options for dropdowns) ─────────────────────────────


class PersonFieldOptions(BaseModel):
    prefixes: list[TermSlim]
    genders: list[TermSlim]
    occupations: list[TermSlim]
    tags: list[TermSlim]
    relationship_types: list[TermSlim]
    preferred_contact: list[TermSlim]
    address_types: list[str]
    channel_types: list[str]
