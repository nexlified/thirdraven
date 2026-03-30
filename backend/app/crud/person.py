import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
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
    PersonAddress,
    PersonChannel,
    PersonContext,
    PersonLocation,
    PersonProfessional,
    PersonProfile,
)
from app.models.vocabulary import PersonLanguage, PersonTag, Term
from app.schemas.iso_reference import CountrySlim, LanguageSlim, TimezonePublic
from app.schemas.person import (
    AddressCreate,
    AddressPublic,
    ChannelCreate,
    ChannelPublic,
    ChannelUpdate,
    PersonContextSection,
    PersonCreate,
    PersonExtended,
    PersonLocationSection,
    PersonProfessionalSection,
    PersonProfileSection,
    PersonSlim,
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
}
_LOCATION_FIELDS = {"timezone"}
_CONTEXT_FIELDS = {
    "how_we_met",
    "first_met_on",
    "last_contacted_on",
    "contact_frequency_days",
    "preferred_contact",
    "relationship_nature",
}
_ALL_EXT_FIELDS = (
    _PROFILE_FIELDS
    | _PROFESSIONAL_FIELDS
    | _LOCATION_FIELDS
    | _CONTEXT_FIELDS
)


def _split_fields(
    data: dict,
) -> tuple[dict, dict, dict, dict, dict]:
    """Partition a flat dict into (core, profile, professional, location, context)."""
    core: dict = {}
    profile: dict = {}
    professional: dict = {}
    location: dict = {}
    context: dict = {}

    buckets = {
        **{k: profile for k in _PROFILE_FIELDS},
        **{k: professional for k in _PROFESSIONAL_FIELDS},
        **{k: location for k in _LOCATION_FIELDS},
        **{k: context for k in _CONTEXT_FIELDS},
    }

    for k, v in data.items():
        if k in _ALL_EXT_FIELDS:
            buckets[k][k] = v
        else:
            core[k] = v

    return core, profile, professional, location, context


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
        if k == "timezone":
            result["timezone_id"] = await resolve_timezone_name(db, v)
    return result


async def _resolve_context_fields(db: AsyncSession, raw: dict) -> dict:
    result = {}
    for k, v in raw.items():
        if k == "preferred_contact":
            result["preferred_contact_term_id"] = await resolve_optional_term_slug(
                db, "contact-channels", v
            )
        else:
            result[k] = v  # relationship_nature and other raw strings pass through
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


# ── Channel helpers ────────────────────────────────────────────────────────────


async def _get_primary_channel(
    db: AsyncSession, person_id: uuid.UUID, type_: str
) -> str | None:
    r = await db.execute(
        select(PersonChannel).where(
            PersonChannel.person_id == person_id,
            PersonChannel.type == type_,
            PersonChannel.is_primary.is_(True),
        )
    )
    row = r.scalars().first()
    return row.value if row else None


async def _set_channels(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    channels: list[ChannelCreate],
) -> None:
    """Replace all channels for a person."""
    existing = await db.execute(
        select(PersonChannel).where(PersonChannel.person_id == person_id)
    )
    for row in existing.scalars().all():
        await db.delete(row)
    for ch in channels:
        db.add(
            PersonChannel(
                person_id=person_id,
                owner_id=owner_id,
                type=ch.type,
                value=ch.value,
                label=ch.label,
                is_primary=ch.is_primary,
            )
        )


# ── Address helpers ────────────────────────────────────────────────────────────


async def _set_addresses(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    addresses: list[AddressCreate],
) -> None:
    """Replace all addresses for a person."""
    existing = await db.execute(
        select(PersonAddress).where(PersonAddress.person_id == person_id)
    )
    for row in existing.scalars().all():
        await db.delete(row)
    for addr in addresses:
        country_id = None
        if addr.country:
            country_id = await resolve_country_alpha2(db, addr.country)
        db.add(
            PersonAddress(
                person_id=person_id,
                owner_id=owner_id,
                type=addr.type,
                street=addr.street,
                city=addr.city,
                postal_code=addr.postal_code,
                country_id=country_id,
                lat=addr.lat,
                lng=addr.lng,
                is_primary=addr.is_primary,
            )
        )


async def _build_addresses(
    db: AsyncSession, person_id: uuid.UUID
) -> list[AddressPublic]:
    r = await db.execute(
        select(PersonAddress, Country)
        .outerjoin(Country, Country.id == PersonAddress.country_id)
        .where(PersonAddress.person_id == person_id)
        .order_by(PersonAddress.is_primary.desc(), PersonAddress.created_at)
    )
    addresses = []
    for addr, country in r.all():
        addresses.append(
            AddressPublic(
                id=addr.id,
                type=addr.type,
                street=addr.street,
                city=addr.city,
                postal_code=addr.postal_code,
                country=CountrySlim.model_validate(country) if country else None,
                lat=addr.lat,
                lng=addr.lng,
                is_primary=addr.is_primary,
            )
        )
    return addresses


# ── PersonSlim builder ─────────────────────────────────────────────────────────


async def _build_person_slim(db: AsyncSession, person: Person) -> PersonSlim:
    tags = await _get_person_tags(db, person.id)
    email = await _get_primary_channel(db, person.id, "email")
    phone = await _get_primary_channel(db, person.id, "mobile")
    if phone is None:
        phone = await _get_primary_channel(db, person.id, "phone")
    return PersonSlim(
        id=person.id,
        owner_id=person.owner_id,
        first_name=person.first_name,
        last_name=person.last_name,
        nickname=person.nickname,
        email=email,
        phone=phone,
        notes=person.notes,
        closeness_level=person.closeness_level,
        visibility=person.visibility,
        household_id=person.household_id,
        created_at=person.created_at,
        updated_at=person.updated_at,
        tags=tags,
        is_placeholder=person.is_placeholder,
        is_bot=person.is_bot,
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
    )


async def _build_location_section(
    db: AsyncSession, person_id: uuid.UUID, row: PersonLocation
) -> PersonLocationSection:
    timezone = None
    if row.timezone_id:
        r = await db.execute(select(Timezone).where(Timezone.id == row.timezone_id))
        tz = r.scalars().first()
        if tz:
            timezone = TimezonePublic.model_validate(tz)

    addresses = await _build_addresses(db, person_id)

    return PersonLocationSection(
        timezone=timezone,
        addresses=addresses,
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
        relationship_nature=row.relationship_nature,
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

    # Extract many-per-person and junction-table fields before splitting
    tags_slugs = raw.pop("tags", [])
    languages_codes = raw.pop("languages", [])
    channels_data = raw.pop("channels", [])
    addresses_data = raw.pop("addresses", [])

    core, profile_raw, professional_raw, location_raw, context_raw = _split_fields(raw)

    # Resolve slug/code fields to FK UUIDs
    profile_db = await _resolve_profile_fields(db, profile_raw)
    professional_db = await _resolve_professional_fields(db, professional_raw)
    location_db = await _resolve_location_fields(db, location_raw)
    context_db = await _resolve_context_fields(db, context_raw)

    person = Person(owner_id=owner_id, **core)
    db.add(person)
    await db.flush()

    # Extension rows (only create if any fields were provided)
    if profile_db:
        db.add(PersonProfile(person_id=person.id, **profile_db))
    if professional_db:
        db.add(PersonProfessional(person_id=person.id, **professional_db))
    if location_db:
        db.add(PersonLocation(person_id=person.id, **location_db))
    if context_db:
        db.add(PersonContext(person_id=person.id, **context_db))

    # Junction rows
    for slug in tags_slugs:
        term_id = await resolve_term_slug(db, "person-tags", slug)
        db.add(PersonTag(person_id=person.id, term_id=term_id))

    for code in languages_codes:
        lang_id = await resolve_language_code(db, code)
        if lang_id:
            db.add(PersonLanguage(person_id=person.id, language_id=lang_id))

    # Channels
    channels = [
        ChannelCreate(**ch) if isinstance(ch, dict) else ch for ch in channels_data
    ]
    for ch in channels:
        db.add(PersonChannel(
            person_id=person.id,
            owner_id=owner_id,
            type=ch.type,
            value=ch.value,
            label=ch.label,
            is_primary=ch.is_primary,
        ))

    # Addresses
    addresses = [
        AddressCreate(**addr) if isinstance(addr, dict) else addr
        for addr in addresses_data
    ]
    for addr in addresses:
        country_id = None
        if addr.country:
            country_id = await resolve_country_alpha2(db, addr.country)
        db.add(PersonAddress(
            person_id=person.id,
            owner_id=owner_id,
            type=addr.type,
            street=addr.street,
            city=addr.city,
            postal_code=addr.postal_code,
            country_id=country_id,
            lat=addr.lat,
            lng=addr.lng,
            is_primary=addr.is_primary,
        ))

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

        if all_requested or "location" in include:
            r = await db.execute(
                select(PersonLocation).where(PersonLocation.person_id == person_id)
            )
            row = r.scalars().first()
            # Always return location section when requested (addresses may exist even without timezone)
            loc_row = row or PersonLocation(person_id=person_id)
            sections["location"] = await _build_location_section(db, person_id, loc_row)

        if all_requested or "context" in include:
            r = await db.execute(
                select(PersonContext).where(PersonContext.person_id == person_id)
            )
            row = r.scalars().first()
            if row:
                sections["context"] = await _build_context_section(db, row)

        if all_requested or "channels" in include or "contact_methods" in include:
            r = await db.execute(
                select(PersonChannel)
                .where(PersonChannel.person_id == person_id)
                .order_by(PersonChannel.is_primary.desc(), PersonChannel.created_at)
            )
            sections["channels"] = [
                ChannelPublic.model_validate(ch) for ch in r.scalars().all()
            ]

    return PersonExtended(**slim.model_dump(), **sections)


async def list_persons(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    household_id: uuid.UUID | None = None,
    is_placeholder: bool | None = None,
    is_bot: bool | None = None,
    relationship_nature: str | None = None,
) -> tuple[list[PersonSlim], int]:
    base = select(Person).where(
        _visibility_clause(owner_id, household_id), Person.deleted_at.is_(None)
    )
    if is_placeholder is not None:
        base = base.where(Person.is_placeholder == is_placeholder)
    if is_bot is not None:
        base = base.where(Person.is_bot == is_bot)
    if relationship_nature is not None:
        base = (
            base.outerjoin(PersonContext, PersonContext.person_id == Person.id)
            .where(PersonContext.relationship_nature == relationship_nature)
        )
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    result = await db.execute(
        base.order_by(Person.created_at.desc()).offset(skip).limit(limit)
    )
    persons = result.scalars().all()
    return [await _build_person_slim(db, p) for p in persons], total


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

    # Extract many-per-person and junction-table fields before splitting
    tags_slugs = raw.pop("tags", None)
    languages_codes = raw.pop("languages", None)
    channels_data = raw.pop("channels", None)
    addresses_data = raw.pop("addresses", None)

    core, profile_raw, professional_raw, location_raw, context_raw = _split_fields(raw)

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

    # Update junction tables (replace-all semantics)
    if tags_slugs is not None:
        await _set_person_tags(db, person_id, tags_slugs)

    if languages_codes is not None:
        await _set_person_languages(db, person_id, languages_codes)

    # Many-per-person replace-all
    if channels_data is not None:
        channels = [
            ChannelCreate(**ch) if isinstance(ch, dict) else ch
            for ch in channels_data
        ]
        await _set_channels(db, person_id, owner_id, channels)

    if addresses_data is not None:
        addresses = [
            AddressCreate(**addr) if isinstance(addr, dict) else addr
            for addr in addresses_data
        ]
        await _set_addresses(db, person_id, owner_id, addresses)

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


# ── Channel CRUD ───────────────────────────────────────────────────────────────


async def create_channel(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: ChannelCreate,
) -> ChannelPublic:
    ch = PersonChannel(
        person_id=person_id,
        owner_id=owner_id,
        type=data.type,
        value=data.value,
        label=data.label,
        is_primary=data.is_primary,
    )
    db.add(ch)
    await db.commit()
    await db.refresh(ch)
    return ChannelPublic.model_validate(ch)


async def update_channel(
    db: AsyncSession,
    ch_id: uuid.UUID,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: ChannelUpdate,
) -> ChannelPublic | None:
    r = await db.execute(
        select(PersonChannel).where(
            PersonChannel.id == ch_id,
            PersonChannel.person_id == person_id,
            PersonChannel.owner_id == owner_id,
        )
    )
    ch = r.scalars().first()
    if not ch:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ch, field, value)
    db.add(ch)
    await db.commit()
    await db.refresh(ch)
    return ChannelPublic.model_validate(ch)


async def delete_channel(
    db: AsyncSession,
    ch_id: uuid.UUID,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> bool:
    r = await db.execute(
        select(PersonChannel).where(
            PersonChannel.id == ch_id,
            PersonChannel.person_id == person_id,
            PersonChannel.owner_id == owner_id,
        )
    )
    ch = r.scalars().first()
    if not ch:
        return False
    await db.delete(ch)
    await db.commit()
    return True


# ── Address CRUD ───────────────────────────────────────────────────────────────


async def create_address(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: AddressCreate,
) -> AddressPublic:
    country_id = None
    if data.country:
        country_id = await resolve_country_alpha2(db, data.country)
    addr = PersonAddress(
        person_id=person_id,
        owner_id=owner_id,
        type=data.type,
        street=data.street,
        city=data.city,
        postal_code=data.postal_code,
        country_id=country_id,
        lat=data.lat,
        lng=data.lng,
        is_primary=data.is_primary,
    )
    db.add(addr)
    await db.commit()
    await db.refresh(addr)

    country = None
    if addr.country_id:
        r = await db.execute(select(Country).where(Country.id == addr.country_id))
        c = r.scalars().first()
        if c:
            country = CountrySlim.model_validate(c)

    return AddressPublic(
        id=addr.id,
        type=addr.type,
        street=addr.street,
        city=addr.city,
        postal_code=addr.postal_code,
        country=country,
        lat=addr.lat,
        lng=addr.lng,
        is_primary=addr.is_primary,
    )


async def update_address(
    db: AsyncSession,
    addr_id: uuid.UUID,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: AddressCreate,
) -> AddressPublic | None:
    r = await db.execute(
        select(PersonAddress).where(
            PersonAddress.id == addr_id,
            PersonAddress.person_id == person_id,
            PersonAddress.owner_id == owner_id,
        )
    )
    addr = r.scalars().first()
    if not addr:
        return None

    country_id = addr.country_id
    if data.country is not None:
        country_id = await resolve_country_alpha2(db, data.country) if data.country else None

    for field in ("type", "street", "city", "postal_code", "lat", "lng", "is_primary"):
        val = getattr(data, field, None)
        if val is not None:
            setattr(addr, field, val)
    addr.country_id = country_id
    db.add(addr)
    await db.commit()
    await db.refresh(addr)

    country = None
    if addr.country_id:
        r = await db.execute(select(Country).where(Country.id == addr.country_id))
        c = r.scalars().first()
        if c:
            country = CountrySlim.model_validate(c)

    return AddressPublic(
        id=addr.id,
        type=addr.type,
        street=addr.street,
        city=addr.city,
        postal_code=addr.postal_code,
        country=country,
        lat=addr.lat,
        lng=addr.lng,
        is_primary=addr.is_primary,
    )


async def delete_address(
    db: AsyncSession,
    addr_id: uuid.UUID,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> bool:
    r = await db.execute(
        select(PersonAddress).where(
            PersonAddress.id == addr_id,
            PersonAddress.person_id == person_id,
            PersonAddress.owner_id == owner_id,
        )
    )
    addr = r.scalars().first()
    if not addr:
        return False
    await db.delete(addr)
    await db.commit()
    return True
