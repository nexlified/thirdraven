import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.iso_reference import CountrySlim, LanguageSlim, TimezonePublic
from app.schemas.vocabulary import TermSlim


class RelationshipCreate(BaseModel):
    to_person_id: uuid.UUID
    label: str  # slug from "relationship-types" vocabulary


class RelationshipPublic(BaseModel):
    id: uuid.UUID
    from_person_id: uuid.UUID
    to_person_id: uuid.UUID
    label_term_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Request schemas (flat — CRUD routes fields to the correct tables) ──────────


class PersonCreate(BaseModel):
    first_name: str
    last_name: str | None = None
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None
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
    linkedin_url: str | None = None
    phone_secondary: str | None = None
    # social section
    twitter_handle: str | None = None
    instagram_handle: str | None = None
    website_url: str | None = None
    facebook_url: str | None = None
    github_handle: str | None = None
    discord_handle: str | None = None
    telegram_handle: str | None = None
    # location section
    address_home: str | None = None
    address_work: str | None = None
    city: str | None = None
    country: str | None = None  # ISO alpha2 country code
    timezone: str | None = None  # IANA timezone name
    # context section
    how_we_met: str | None = None
    first_met_on: date | None = None
    last_contacted_on: date | None = None
    contact_frequency_days: int | None = None
    preferred_contact: str | None = None  # slug from "contact-channels"
    # physical section
    height_cm: float | None = None
    eye_color: str | None = None  # slug from "eye-colors"
    hair_color: str | None = None  # slug from "hair-colors"
    blood_type: str | None = None
    # personality section
    interests: str | None = None
    food_preferences: str | None = None
    dietary_restrictions: str | None = None
    personality_notes: str | None = None
    communication_style: str | None = None  # slug from "communication-styles"


class PersonUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None
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
    linkedin_url: str | None = None
    phone_secondary: str | None = None
    # social section
    twitter_handle: str | None = None
    instagram_handle: str | None = None
    website_url: str | None = None
    facebook_url: str | None = None
    github_handle: str | None = None
    discord_handle: str | None = None
    telegram_handle: str | None = None
    # location section
    address_home: str | None = None
    address_work: str | None = None
    city: str | None = None
    country: str | None = None
    timezone: str | None = None
    # context section
    how_we_met: str | None = None
    first_met_on: date | None = None
    last_contacted_on: date | None = None
    contact_frequency_days: int | None = None
    preferred_contact: str | None = None
    # physical section
    height_cm: float | None = None
    eye_color: str | None = None
    hair_color: str | None = None
    blood_type: str | None = None
    # personality section
    interests: str | None = None
    food_preferences: str | None = None
    dietary_restrictions: str | None = None
    personality_notes: str | None = None
    communication_style: str | None = None


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
    linkedin_url: str | None = None
    phone_secondary: str | None = None

    model_config = {"from_attributes": True}


class PersonSocialSection(BaseModel):
    twitter_handle: str | None = None
    instagram_handle: str | None = None
    website_url: str | None = None
    facebook_url: str | None = None
    github_handle: str | None = None
    discord_handle: str | None = None
    telegram_handle: str | None = None

    model_config = {"from_attributes": True}


class PersonLocationSection(BaseModel):
    address_home: str | None = None
    address_work: str | None = None
    city: str | None = None
    country: CountrySlim | None = None
    timezone: TimezonePublic | None = None

    model_config = {"from_attributes": True}


class PersonContextSection(BaseModel):
    how_we_met: str | None = None
    first_met_on: date | None = None
    last_contacted_on: date | None = None
    contact_frequency_days: int | None = None
    preferred_contact: TermSlim | None = None

    model_config = {"from_attributes": True}


class PersonPhysicalSection(BaseModel):
    height_cm: float | None = None
    eye_color: TermSlim | None = None
    hair_color: TermSlim | None = None
    blood_type: str | None = None

    model_config = {"from_attributes": True}


class PersonPersonalitySection(BaseModel):
    interests: str | None = None
    food_preferences: str | None = None
    dietary_restrictions: str | None = None
    personality_notes: str | None = None
    communication_style: TermSlim | None = None

    model_config = {"from_attributes": True}


class PersonExtended(PersonSlim):
    """Slim core + opt-in extension sections."""

    profile: PersonProfileSection | None = None
    professional: PersonProfessionalSection | None = None
    social: PersonSocialSection | None = None
    location: PersonLocationSection | None = None
    context: PersonContextSection | None = None
    physical: PersonPhysicalSection | None = None
    personality: PersonPersonalitySection | None = None


class PersonWithRelationships(PersonExtended):
    relationships: list[RelationshipPublic] = []


# Alias kept for any stale internal references
PersonPublicRead = PersonSlim
