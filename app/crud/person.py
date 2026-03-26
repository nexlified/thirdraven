import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, or_, select

from app.crud.iso_reference import (
    resolve_country_alpha2,
    resolve_language_code,
    resolve_timezone_name,
)
from app.crud.vocabulary import resolve_optional_term_slug, resolve_term_slug
from app.models.iso_reference import Country, Language, Timezone
from app.models.person import Person
from app.models.person_extensions import (
    PersonContext,
    PersonLocation,
    PersonPersonality,
    PersonPhysical,
    PersonProfessional,
    PersonProfile,
    PersonSocial,
)
from app.models.person_relationship import PersonRelationship
from app.models.vocabulary import PersonLanguage, PersonTag, Term
from app.schemas.iso_reference import CountrySlim, LanguageSlim, TimezonePublic
from app.schemas.person import (
    PersonContextSection,
    PersonCreate,
    PersonExtended,
    PersonLocationSection,
    PersonPersonalitySection,
    PersonPhysicalSection,
    PersonProfessionalSection,
    PersonProfileSection,
    PersonSlim,
    PersonSocialSection,
    PersonUpdate,
)
from app.schemas.vocabulary import TermSlim

# ── Household visibility helper ────────────────────────────────────────────────


def _visibility_clause(
    owner_id: uuid.UUID, household_id: uuid.UUID | None
):
    """WHERE clause covering owner's own records + household-visible records."""
    if household_id:
        return or_(
            Person.owner_id == owner_id,
            and_(
                Person.visibility == "household",
                Person.household_id == household_id,
            ),
        )
    return Person.owner_id == owner_id


# ── Field routing constants ────────────────────────────────────────────────────

_PROFILE_FIELDS = {
    "middle_name",
    "prefix",
    "date_of_birth",
    "gender",
    "nationality",
    "languages",
}
_PROFESSIONAL_FIELDS = {
    "occupation",
    "company",
    "job_title",
    "linkedin_url",
    "phone_secondary",
}
_SOCIAL_FIELDS = {
    "twitter_handle",
    "instagram_handle",
    "website_url",
    "facebook_url",
    "github_handle",
    "discord_handle",
    "telegram_handle",
}
_LOCATION_FIELDS = {"address_home", "address_work", "city", "country", "timezone"}
_CONTEXT_FIELDS = {
    "how_we_met",
    "first_met_on",
    "last_contacted_on",
    "contact_frequency_days",
    "preferred_contact",
}
_PHYSICAL_FIELDS = {"height_cm", "eye_color", "hair_color", "blood_type"}
_PERSONALITY_FIELDS = {
    "interests",
    "food_preferences",
    "dietary_restrictions",
    "personality_notes",
    "communication_style",
}

_ALL_EXT_FIELDS = (
    _PROFILE_FIELDS
    | _PROFESSIONAL_FIELDS
    | _SOCIAL_FIELDS
    | _LOCATION_FIELDS
    | _CONTEXT_FIELDS
    | _PHYSICAL_FIELDS
    | _PERSONALITY_FIELDS
)


def _split_fields(
    data: dict,
) -> tuple[dict, dict, dict, dict, dict, dict, dict, dict]:
    """Partition a flat dict into (core, profile, professional, social, location, context, physical, personality)."""  # noqa: E501
    core: dict = {}
    profile: dict = {}
    professional: dict = {}
    social: dict = {}
    location: dict = {}
    context: dict = {}
    physical: dict = {}
    personality: dict = {}

    buckets = {
        **{k: profile for k in _PROFILE_FIELDS},
        **{k: professional for k in _PROFESSIONAL_FIELDS},
        **{k: social for k in _SOCIAL_FIELDS},
        **{k: location for k in _LOCATION_FIELDS},
        **{k: context for k in _CONTEXT_FIELDS},
        **{k: physical for k in _PHYSICAL_FIELDS},
        **{k: personality for k in _PERSONALITY_FIELDS},
    }

    for k, v in data.items():
        if k in _ALL_EXT_FIELDS:
            buckets[k][k] = v
        else:
            core[k] = v

    return core, profile, professional, social, location, context, physical, personality


# ── Slug-to-FK resolution helpers ─────────────────────────────────────────────


async def _resolve_profile_fields(db: AsyncSession, raw: dict) -> dict:
    """Convert profile slug/code fields to FK UUIDs for DB storage."""
    result = {}
    for k, v in raw.items():
        if k == "prefix":
            result["prefix_term_id"] = await resolve_optional_term_slug(
                db, "name-prefixes", v
            )
        elif k == "gender":
            result["gender_term_id"] = await resolve_optional_term_slug(
                db, "genders", v
            )
        elif k == "nationality":
            result["nationality_country_id"] = await resolve_country_alpha2(db, v)
        elif k == "languages":
            pass  # Handled as junction table separately
        else:
            result[k] = v
    return result


async def _resolve_professional_fields(db: AsyncSession, raw: dict) -> dict:
    result = {}
    for k, v in raw.items():
        if k == "occupation":
            result["occupation_term_id"] = await resolve_optional_term_slug(
                db, "occupations", v
            )
        else:
            result[k] = v
    return result


async def _resolve_location_fields(db: AsyncSession, raw: dict) -> dict:
    result = {}
    for k, v in raw.items():
        if k == "country":
            result["country_id"] = await resolve_country_alpha2(db, v)
        elif k == "timezone":
            result["timezone_id"] = await resolve_timezone_name(db, v)
        else:
            result[k] = v
    return result


async def _resolve_context_fields(db: AsyncSession, raw: dict) -> dict:
    result = {}
    for k, v in raw.items():
        if k == "preferred_contact":
            result["preferred_contact_term_id"] = await resolve_optional_term_slug(
                db, "contact-channels", v
            )
        else:
            result[k] = v
    return result


async def _resolve_physical_fields(db: AsyncSession, raw: dict) -> dict:
    result = {}
    for k, v in raw.items():
        if k == "eye_color":
            result["eye_color_term_id"] = await resolve_optional_term_slug(
                db, "eye-colors", v
            )
        elif k == "hair_color":
            result["hair_color_term_id"] = await resolve_optional_term_slug(
                db, "hair-colors", v
            )
        else:
            result[k] = v
    return result


async def _resolve_personality_fields(db: AsyncSession, raw: dict) -> dict:
    result = {}
    for k, v in raw.items():
        if k == "communication_style":
            result["communication_style_term_id"] = await resolve_optional_term_slug(
                db, "communication-styles", v
            )
        else:
            result[k] = v
    return result


# ── Junction table helpers ─────────────────────────────────────────────────────


async def _get_person_tags(db: AsyncSession, person_id: uuid.UUID) -> list[TermSlim]:
    result = await db.execute(
        select(Term)
        .join(PersonTag, Term.id == PersonTag.term_id)
        .where(PersonTag.person_id == person_id, Term.is_active.is_(True))
        .order_by(Term.name)
    )
    return [TermSlim.model_validate(t) for t in result.scalars().all()]


async def _set_person_tags(
    db: AsyncSession, person_id: uuid.UUID, tag_slugs: list[str]
) -> None:
    """Replace all tags for a person."""
    existing = await db.execute(
        select(PersonTag).where(PersonTag.person_id == person_id)
    )
    for row in existing.scalars().all():
        await db.delete(row)
    for slug in tag_slugs:
        term_id = await resolve_term_slug(db, "person-tags", slug)
        db.add(PersonTag(person_id=person_id, term_id=term_id))


async def _get_person_languages(
    db: AsyncSession, person_id: uuid.UUID
) -> list[LanguageSlim]:
    result = await db.execute(
        select(Language)
        .join(PersonLanguage, Language.id == PersonLanguage.language_id)
        .where(PersonLanguage.person_id == person_id, Language.is_active.is_(True))
        .order_by(Language.name)
    )
    return [LanguageSlim.model_validate(lang) for lang in result.scalars().all()]


async def _set_person_languages(
    db: AsyncSession, person_id: uuid.UUID, codes: list[str]
) -> None:
    """Replace all languages for a person."""
    existing = await db.execute(
        select(PersonLanguage).where(PersonLanguage.person_id == person_id)
    )
    for row in existing.scalars().all():
        await db.delete(row)
    for code in codes:
        lang_id = await resolve_language_code(db, code)
        if lang_id:
            db.add(PersonLanguage(person_id=person_id, language_id=lang_id))


# ── PersonSlim builder ─────────────────────────────────────────────────────────


async def _build_person_slim(db: AsyncSession, person: Person) -> PersonSlim:
    tags = await _get_person_tags(db, person.id)
    return PersonSlim(
        id=person.id,
        owner_id=person.owner_id,
        first_name=person.first_name,
        last_name=person.last_name,
        nickname=person.nickname,
        email=person.email,
        phone=person.phone,
        notes=person.notes,
        closeness_level=person.closeness_level,
        visibility=person.visibility,
        household_id=person.household_id,
        created_at=person.created_at,
        updated_at=person.updated_at,
        tags=tags,
    )


# ── Section builders ───────────────────────────────────────────────────────────


async def _build_profile_section(
    db: AsyncSession, person_id: uuid.UUID, row: PersonProfile
) -> PersonProfileSection:
    prefix = None
    if row.prefix_term_id:
        r = await db.execute(select(Term).where(Term.id == row.prefix_term_id))
        t = r.scalars().first()
        if t:
            prefix = TermSlim.model_validate(t)

    gender = None
    if row.gender_term_id:
        r = await db.execute(select(Term).where(Term.id == row.gender_term_id))
        t = r.scalars().first()
        if t:
            gender = TermSlim.model_validate(t)

    nationality = None
    if row.nationality_country_id:
        r = await db.execute(
            select(Country).where(Country.id == row.nationality_country_id)
        )
        c = r.scalars().first()
        if c:
            nationality = CountrySlim.model_validate(c)

    languages = await _get_person_languages(db, person_id)

    return PersonProfileSection(
        middle_name=row.middle_name,
        prefix=prefix,
        date_of_birth=row.date_of_birth,
        gender=gender,
        nationality=nationality,
        languages=languages,
    )


async def _build_professional_section(
    db: AsyncSession, row: PersonProfessional
) -> PersonProfessionalSection:
    occupation = None
    if row.occupation_term_id:
        r = await db.execute(select(Term).where(Term.id == row.occupation_term_id))
        t = r.scalars().first()
        if t:
            occupation = TermSlim.model_validate(t)

    return PersonProfessionalSection(
        occupation=occupation,
        company=row.company,
        job_title=row.job_title,
        linkedin_url=row.linkedin_url,
        phone_secondary=row.phone_secondary,
    )


async def _build_location_section(
    db: AsyncSession, row: PersonLocation
) -> PersonLocationSection:
    country = None
    if row.country_id:
        r = await db.execute(select(Country).where(Country.id == row.country_id))
        c = r.scalars().first()
        if c:
            country = CountrySlim.model_validate(c)

    timezone = None
    if row.timezone_id:
        r = await db.execute(select(Timezone).where(Timezone.id == row.timezone_id))
        tz = r.scalars().first()
        if tz:
            timezone = TimezonePublic.model_validate(tz)

    return PersonLocationSection(
        address_home=row.address_home,
        address_work=row.address_work,
        city=row.city,
        country=country,
        timezone=timezone,
    )


async def _build_context_section(
    db: AsyncSession, row: PersonContext
) -> PersonContextSection:
    preferred_contact = None
    if row.preferred_contact_term_id:
        r = await db.execute(
            select(Term).where(Term.id == row.preferred_contact_term_id)
        )
        t = r.scalars().first()
        if t:
            preferred_contact = TermSlim.model_validate(t)

    return PersonContextSection(
        how_we_met=row.how_we_met,
        first_met_on=row.first_met_on,
        last_contacted_on=row.last_contacted_on,
        contact_frequency_days=row.contact_frequency_days,
        preferred_contact=preferred_contact,
    )


async def _build_physical_section(
    db: AsyncSession, row: PersonPhysical
) -> PersonPhysicalSection:
    eye_color = None
    if row.eye_color_term_id:
        r = await db.execute(select(Term).where(Term.id == row.eye_color_term_id))
        t = r.scalars().first()
        if t:
            eye_color = TermSlim.model_validate(t)

    hair_color = None
    if row.hair_color_term_id:
        r = await db.execute(select(Term).where(Term.id == row.hair_color_term_id))
        t = r.scalars().first()
        if t:
            hair_color = TermSlim.model_validate(t)

    return PersonPhysicalSection(
        height_cm=row.height_cm,
        eye_color=eye_color,
        hair_color=hair_color,
        blood_type=row.blood_type,
    )


async def _build_personality_section(
    db: AsyncSession, row: PersonPersonality
) -> PersonPersonalitySection:
    communication_style = None
    if row.communication_style_term_id:
        r = await db.execute(
            select(Term).where(Term.id == row.communication_style_term_id)
        )
        t = r.scalars().first()
        if t:
            communication_style = TermSlim.model_validate(t)

    return PersonPersonalitySection(
        interests=row.interests,
        food_preferences=row.food_preferences,
        dietary_restrictions=row.dietary_restrictions,
        personality_notes=row.personality_notes,
        communication_style=communication_style,
    )


# ── CRUD operations ────────────────────────────────────────────────────────────


async def create_person(
    db: AsyncSession,
    owner_id: uuid.UUID,
    data: PersonCreate,
    household_id: uuid.UUID | None = None,
) -> PersonSlim:
    raw = data.model_dump(exclude_unset=True)

    # Handle visibility before splitting fields
    requested_visibility = raw.get("visibility", "private")
    if requested_visibility == "household":
        if not household_id:
            raise HTTPException(
                status_code=400,
                detail="You must be in a household to share records.",
            )
        raw["household_id"] = household_id
        raw["visibility"] = "household"
    else:
        raw["visibility"] = "private"
        raw.pop("household_id", None)

    # Extract junction-table fields before splitting
    tags_slugs = raw.pop("tags", [])
    languages_codes = raw.pop("languages", [])

    (
        core,
        profile_raw,
        professional_raw,
        social_raw,
        location_raw,
        context_raw,
        physical_raw,
        personality_raw,
    ) = _split_fields(raw)

    # Resolve slug/code fields to FK UUIDs
    profile_db = await _resolve_profile_fields(db, profile_raw)
    professional_db = await _resolve_professional_fields(db, professional_raw)
    location_db = await _resolve_location_fields(db, location_raw)
    context_db = await _resolve_context_fields(db, context_raw)
    physical_db = await _resolve_physical_fields(db, physical_raw)
    personality_db = await _resolve_personality_fields(db, personality_raw)

    person = Person(owner_id=owner_id, **core)
    db.add(person)
    await db.flush()

    # Extension rows (only create if any fields were provided)
    if profile_db:
        db.add(PersonProfile(person_id=person.id, **profile_db))
    if professional_db:
        db.add(PersonProfessional(person_id=person.id, **professional_db))
    if social_raw:
        db.add(PersonSocial(person_id=person.id, **social_raw))
    if location_db:
        db.add(PersonLocation(person_id=person.id, **location_db))
    if context_db:
        db.add(PersonContext(person_id=person.id, **context_db))
    if physical_db:
        db.add(PersonPhysical(person_id=person.id, **physical_db))
    if personality_db:
        db.add(PersonPersonality(person_id=person.id, **personality_db))

    # Junction rows
    for slug in tags_slugs:
        term_id = await resolve_term_slug(db, "person-tags", slug)
        db.add(PersonTag(person_id=person.id, term_id=term_id))

    for code in languages_codes:
        lang_id = await resolve_language_code(db, code)
        if lang_id:
            db.add(PersonLanguage(person_id=person.id, language_id=lang_id))

    await db.commit()
    await db.refresh(person)
    return await _build_person_slim(db, person)


async def get_person(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    include: list[str] | None = None,
    household_id: uuid.UUID | None = None,
) -> PersonExtended | None:
    result = await db.execute(
        select(Person).where(
            Person.id == person_id,
            _visibility_clause(owner_id, household_id),
            Person.deleted_at.is_(None),
        )
    )
    person = result.scalars().first()
    if not person:
        return None

    slim = await _build_person_slim(db, person)
    sections: dict = {}

    if include:
        all_requested = "all" in include

        if all_requested or "profile" in include:
            r = await db.execute(
                select(PersonProfile).where(PersonProfile.person_id == person_id)
            )
            row = r.scalars().first()
            if row:
                sections["profile"] = await _build_profile_section(db, person_id, row)

        if all_requested or "professional" in include:
            r = await db.execute(
                select(PersonProfessional).where(
                    PersonProfessional.person_id == person_id
                )
            )
            row = r.scalars().first()
            if row:
                sections["professional"] = await _build_professional_section(db, row)

        if all_requested or "social" in include:
            r = await db.execute(
                select(PersonSocial).where(PersonSocial.person_id == person_id)
            )
            row = r.scalars().first()
            if row:
                sections["social"] = PersonSocialSection.model_validate(row)

        if all_requested or "location" in include:
            r = await db.execute(
                select(PersonLocation).where(PersonLocation.person_id == person_id)
            )
            row = r.scalars().first()
            if row:
                sections["location"] = await _build_location_section(db, row)

        if all_requested or "context" in include:
            r = await db.execute(
                select(PersonContext).where(PersonContext.person_id == person_id)
            )
            row = r.scalars().first()
            if row:
                sections["context"] = await _build_context_section(db, row)

        if all_requested or "physical" in include:
            r = await db.execute(
                select(PersonPhysical).where(PersonPhysical.person_id == person_id)
            )
            row = r.scalars().first()
            if row:
                sections["physical"] = await _build_physical_section(db, row)

        if all_requested or "personality" in include:
            r = await db.execute(
                select(PersonPersonality).where(
                    PersonPersonality.person_id == person_id
                )
            )
            row = r.scalars().first()
            if row:
                sections["personality"] = await _build_personality_section(db, row)

    return PersonExtended(**slim.model_dump(), **sections)


async def list_persons(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    household_id: uuid.UUID | None = None,
) -> list[PersonSlim]:
    result = await db.execute(
        select(Person)
        .where(_visibility_clause(owner_id, household_id), Person.deleted_at.is_(None))
        .offset(skip)
        .limit(limit)
    )
    persons = result.scalars().all()
    return [await _build_person_slim(db, p) for p in persons]


async def update_person(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: PersonUpdate,
    include: list[str] | None = None,
    household_id: uuid.UUID | None = None,
) -> PersonExtended | None:
    result = await db.execute(
        select(Person).where(
            Person.id == person_id,
            Person.owner_id == owner_id,
            Person.deleted_at.is_(None),
        )
    )
    person = result.scalars().first()
    if not person:
        return None

    raw = data.model_dump(exclude_unset=True)

    # Extract junction-table fields before splitting
    tags_slugs = raw.pop("tags", None)
    languages_codes = raw.pop("languages", None)

    (
        core,
        profile_raw,
        professional_raw,
        social_raw,
        location_raw,
        context_raw,
        physical_raw,
        personality_raw,
    ) = _split_fields(raw)

    # Handle visibility change in core fields
    if "visibility" in core:
        new_vis = core.pop("visibility")
        if new_vis == "household":
            if not household_id:
                raise HTTPException(
                    status_code=400,
                    detail="You must be in a household to share records.",
                )
            person.visibility = "household"
            person.household_id = household_id
        else:
            person.visibility = "private"
            person.household_id = None

    # Update core fields
    for field, value in core.items():
        setattr(person, field, value)
    person.updated_at = datetime.utcnow()
    db.add(person)

    # Update extension rows (with resolver)
    for ext_raw, resolver, ext_cls in [
        (profile_raw, _resolve_profile_fields, PersonProfile),
        (professional_raw, _resolve_professional_fields, PersonProfessional),
        (location_raw, _resolve_location_fields, PersonLocation),
        (context_raw, _resolve_context_fields, PersonContext),
        (physical_raw, _resolve_physical_fields, PersonPhysical),
        (personality_raw, _resolve_personality_fields, PersonPersonality),
    ]:
        if ext_raw:
            ext_db = await resolver(db, ext_raw)
            row_result = await db.execute(
                select(ext_cls).where(ext_cls.person_id == person_id)
            )
            ext_row = row_result.scalars().first()
            if ext_row:
                for field, value in ext_db.items():
                    setattr(ext_row, field, value)
                ext_row.updated_at = datetime.utcnow()
                db.add(ext_row)
            else:
                db.add(ext_cls(person_id=person_id, **ext_db))

    # Update social (no resolver needed — raw values stored directly)
    if social_raw:
        row_result = await db.execute(
            select(PersonSocial).where(PersonSocial.person_id == person_id)
        )
        ext_row = row_result.scalars().first()
        if ext_row:
            for field, value in social_raw.items():
                setattr(ext_row, field, value)
            ext_row.updated_at = datetime.utcnow()
            db.add(ext_row)
        else:
            db.add(PersonSocial(person_id=person_id, **social_raw))

    # Update junction tables (replace-all semantics)
    if tags_slugs is not None:
        await _set_person_tags(db, person_id, tags_slugs)

    if languages_codes is not None:
        await _set_person_languages(db, person_id, languages_codes)

    await db.commit()
    return await get_person(db, person_id, owner_id, include=include, household_id=household_id)


async def soft_delete_person(
    db: AsyncSession, person_id: uuid.UUID, owner_id: uuid.UUID
) -> Person | None:
    result = await db.execute(
        select(Person).where(
            Person.id == person_id,
            Person.owner_id == owner_id,
            Person.deleted_at.is_(None),
        )
    )
    person = result.scalars().first()
    if not person:
        return None
    person.deleted_at = datetime.utcnow()
    db.add(person)
    await db.commit()
    return person


async def add_relationship(
    db: AsyncSession,
    from_id: uuid.UUID,
    to_id: uuid.UUID,
    label: str,
    owner_id: uuid.UUID,
) -> PersonRelationship:
    label_term_id = await resolve_term_slug(db, "relationship-types", label)
    rel = PersonRelationship(
        from_person_id=from_id,
        to_person_id=to_id,
        label_term_id=label_term_id,
    )
    db.add(rel)
    await db.commit()
    await db.refresh(rel)
    return rel


async def get_relationships_for_person(
    db: AsyncSession, person_id: uuid.UUID
) -> list[PersonRelationship]:
    result = await db.execute(
        select(PersonRelationship).where(PersonRelationship.from_person_id == person_id)
    )
    return list(result.scalars().all())
