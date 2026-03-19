import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

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
    PersonProfessionalSection,
    PersonProfileSection,
    PersonSlim,
    PersonSocialSection,
    PersonUpdate,
)
from app.schemas.vocabulary import TermSlim

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
_SOCIAL_FIELDS = {"twitter_handle", "instagram_handle", "website_url"}
_LOCATION_FIELDS = {"address_home", "address_work", "city", "country", "timezone"}
_CONTEXT_FIELDS = {"how_we_met", "first_met_on"}

_ALL_EXT_FIELDS = (
    _PROFILE_FIELDS
    | _PROFESSIONAL_FIELDS
    | _SOCIAL_FIELDS
    | _LOCATION_FIELDS
    | _CONTEXT_FIELDS
)


def _split_fields(data: dict) -> tuple[dict, dict, dict, dict, dict, dict]:
    """Partition a flat dict into (core, profile, professional, social, location, context)."""  # noqa: E501
    core: dict = {}
    profile: dict = {}
    professional: dict = {}
    social: dict = {}
    location: dict = {}
    context: dict = {}

    buckets = {
        **{k: profile for k in _PROFILE_FIELDS},
        **{k: professional for k in _PROFESSIONAL_FIELDS},
        **{k: social for k in _SOCIAL_FIELDS},
        **{k: location for k in _LOCATION_FIELDS},
        **{k: context for k in _CONTEXT_FIELDS},
    }

    for k, v in data.items():
        if k in _ALL_EXT_FIELDS:
            buckets[k][k] = v
        else:
            core[k] = v

    return core, profile, professional, social, location, context


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


# ── CRUD operations ────────────────────────────────────────────────────────────


async def create_person(
    db: AsyncSession, owner_id: uuid.UUID, data: PersonCreate
) -> PersonSlim:
    raw = data.model_dump(exclude_unset=True)

    # Extract junction-table fields before splitting
    tags_slugs = raw.pop("tags", [])
    languages_codes = raw.pop("languages", [])

    core, profile_raw, professional_raw, social_raw, location_raw, context_raw = (
        _split_fields(raw)
    )

    # Resolve slug/code fields to FK UUIDs
    profile_db = await _resolve_profile_fields(db, profile_raw)
    professional_db = await _resolve_professional_fields(db, professional_raw)
    location_db = await _resolve_location_fields(db, location_raw)

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
    if context_raw:
        db.add(PersonContext(person_id=person.id, **context_raw))

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
                sections["context"] = PersonContextSection.model_validate(row)

    return PersonExtended(**slim.model_dump(), **sections)


async def list_persons(
    db: AsyncSession, owner_id: uuid.UUID, skip: int = 0, limit: int = 50
) -> list[PersonSlim]:
    result = await db.execute(
        select(Person)
        .where(Person.owner_id == owner_id, Person.deleted_at.is_(None))
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

    core, profile_raw, professional_raw, social_raw, location_raw, context_raw = (
        _split_fields(raw)
    )

    # Update core fields
    for field, value in core.items():
        setattr(person, field, value)
    person.updated_at = datetime.utcnow()
    db.add(person)

    # Update extension rows
    for ext_raw, resolver, ext_cls in [
        (profile_raw, _resolve_profile_fields, PersonProfile),
        (professional_raw, _resolve_professional_fields, PersonProfessional),
        (location_raw, _resolve_location_fields, PersonLocation),
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

    for ext_raw, ext_cls in [
        (social_raw, PersonSocial),
        (context_raw, PersonContext),
    ]:
        if ext_raw:
            row_result = await db.execute(
                select(ext_cls).where(ext_cls.person_id == person_id)
            )
            ext_row = row_result.scalars().first()
            if ext_row:
                for field, value in ext_raw.items():
                    setattr(ext_row, field, value)
                ext_row.updated_at = datetime.utcnow()
                db.add(ext_row)
            else:
                db.add(ext_cls(person_id=person_id, **ext_raw))

    # Update junction tables (replace-all semantics)
    if tags_slugs is not None:
        await _set_person_tags(db, person_id, tags_slugs)

    if languages_codes is not None:
        await _set_person_languages(db, person_id, languages_codes)

    await db.commit()
    return await get_person(db, person_id, owner_id, include=include)


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
