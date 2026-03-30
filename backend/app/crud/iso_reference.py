import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.iso_reference import Country, Language, Timezone

# ── Resolver helpers ───────────────────────────────────────────────────────────


async def resolve_country_alpha2(
    db: AsyncSession, alpha2: str | None
) -> uuid.UUID | None:
    """Resolve ISO alpha2 code → country.id. Raises HTTP 422 if not found."""
    if alpha2 is None:
        return None
    result = await db.execute(
        select(Country).where(
            Country.alpha2 == alpha2.upper(),
            Country.is_active.is_(True),
        )
    )
    country = result.scalars().first()
    if not country:
        raise HTTPException(status_code=422, detail=f"Country '{alpha2}' not found")
    return country.id


async def resolve_language_code(
    db: AsyncSession, iso_639_1: str | None
) -> uuid.UUID | None:
    """Resolve ISO 639-1 code → language.id. Raises HTTP 422 if not found."""
    if iso_639_1 is None:
        return None
    result = await db.execute(
        select(Language).where(
            Language.iso_639_1 == iso_639_1.lower(),
            Language.is_active.is_(True),
        )
    )
    lang = result.scalars().first()
    if not lang:
        raise HTTPException(status_code=422, detail=f"Language '{iso_639_1}' not found")
    return lang.id


async def resolve_timezone_name(db: AsyncSession, name: str | None) -> uuid.UUID | None:
    """Resolve IANA timezone name → timezone.id. Raises HTTP 422 if not found."""
    if name is None:
        return None
    result = await db.execute(
        select(Timezone).where(
            Timezone.name == name,
            Timezone.is_active.is_(True),
        )
    )
    tz = result.scalars().first()
    if not tz:
        raise HTTPException(status_code=422, detail=f"Timezone '{name}' not found")
    return tz.id


# ── Country ────────────────────────────────────────────────────────────────────


async def list_countries(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 300,
    search: str | None = None,
) -> list[Country]:
    query = select(Country).where(Country.is_active.is_(True))
    if search:
        query = query.where(Country.name.ilike(f"%{search}%"))
    query = query.order_by(Country.name)
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_country_by_alpha2(db: AsyncSession, alpha2: str) -> Country | None:
    result = await db.execute(select(Country).where(Country.alpha2 == alpha2.upper()))
    return result.scalars().first()


# ── Language ───────────────────────────────────────────────────────────────────


async def list_languages(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 200,
    search: str | None = None,
) -> list[Language]:
    query = select(Language).where(Language.is_active.is_(True))
    if search:
        query = query.where(Language.name.ilike(f"%{search}%"))
    query = query.order_by(Language.name)
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_language_by_code(db: AsyncSession, iso_639_1: str) -> Language | None:
    result = await db.execute(
        select(Language).where(Language.iso_639_1 == iso_639_1.lower())
    )
    return result.scalars().first()


# ── Timezone ───────────────────────────────────────────────────────────────────


async def list_timezones(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 200,
    country_alpha2: str | None = None,
) -> list[Timezone]:
    query = select(Timezone).where(Timezone.is_active.is_(True))
    if country_alpha2:
        country_result = await db.execute(
            select(Country).where(Country.alpha2 == country_alpha2.upper())
        )
        country = country_result.scalars().first()
        if country:
            query = query.where(Timezone.country_id == country.id)
        else:
            return []
    query = query.order_by(Timezone.name)
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_timezone_by_id(
    db: AsyncSession, timezone_id: uuid.UUID
) -> Timezone | None:
    result = await db.execute(select(Timezone).where(Timezone.id == timezone_id))
    return result.scalars().first()
