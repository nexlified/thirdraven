import uuid
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.vocabulary import resolve_term_slug
from app.models.observation import PersonObservation, PersonObservationTag
from app.models.vocabulary import Term
from app.schemas.observation import (
    ObservationCreate,
    ObservationPublic,
    ObservationUpdate,
)
from app.schemas.vocabulary import TermSlim


async def _get_tags(db: AsyncSession, observation_id: uuid.UUID) -> list[TermSlim]:
    result = await db.execute(
        select(Term)
        .join(PersonObservationTag, Term.id == PersonObservationTag.term_id)
        .where(PersonObservationTag.observation_id == observation_id)
        .order_by(Term.name)
    )
    return [TermSlim.model_validate(t) for t in result.scalars().all()]


async def _set_tags(
    db: AsyncSession, observation_id: uuid.UUID, tag_slugs: list[str]
) -> None:
    existing = await db.execute(
        select(PersonObservationTag).where(
            PersonObservationTag.observation_id == observation_id
        )
    )
    for row in existing.scalars().all():
        await db.delete(row)
    for slug in tag_slugs:
        term_id = await resolve_term_slug(db, "observation-tags", slug)
        db.add(PersonObservationTag(observation_id=observation_id, term_id=term_id))


async def _build(db: AsyncSession, row: PersonObservation) -> ObservationPublic:
    tags = await _get_tags(db, row.id)
    return ObservationPublic(
        id=row.id,
        person_id=row.person_id,
        owner_id=row.owner_id,
        body=row.body,
        observed_on=row.observed_on,
        source=row.source,
        context=row.context,
        is_sensitive=row.is_sensitive,
        tags=tags,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def create_observation(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: ObservationCreate,
) -> ObservationPublic:
    row = PersonObservation(
        person_id=person_id,
        owner_id=owner_id,
        body=data.body,
        observed_on=data.observed_on,
        source=data.source,
        is_sensitive=data.is_sensitive,
    )
    db.add(row)
    await db.flush()
    await _set_tags(db, row.id, data.tags)
    await db.commit()
    await db.refresh(row)
    return await _build(db, row)


async def get_observation(
    db: AsyncSession, obs_id: uuid.UUID, owner_id: uuid.UUID
) -> ObservationPublic | None:
    r = await db.execute(
        select(PersonObservation).where(
            PersonObservation.id == obs_id,
            PersonObservation.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    return await _build(db, row) if row else None


async def list_observations(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    include_sensitive: bool = True,
    context: str | None = None,
) -> tuple[list[ObservationPublic], int]:
    base = select(PersonObservation).where(
        PersonObservation.person_id == person_id,
        PersonObservation.owner_id == owner_id,
    )
    if not include_sensitive:
        base = base.where(PersonObservation.is_sensitive.is_(False))
    if context is not None:
        base = base.where(PersonObservation.context == context)
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    r = await db.execute(
        base.order_by(PersonObservation.observed_on.desc().nulls_last())
        .offset(skip)
        .limit(limit)
    )
    return [await _build(db, row) for row in r.scalars().all()], total


async def update_observation(
    db: AsyncSession,
    obs_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: ObservationUpdate,
) -> ObservationPublic | None:
    r = await db.execute(
        select(PersonObservation).where(
            PersonObservation.id == obs_id,
            PersonObservation.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return None
    raw = data.model_dump(exclude_unset=True)
    tags_slugs = raw.pop("tags", None)
    for field, value in raw.items():
        setattr(row, field, value)
    row.updated_at = datetime.now(UTC)
    db.add(row)
    if tags_slugs is not None:
        await _set_tags(db, row.id, tags_slugs)
    await db.commit()
    await db.refresh(row)
    return await _build(db, row)


async def delete_observation(
    db: AsyncSession, obs_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    r = await db.execute(
        select(PersonObservation).where(
            PersonObservation.id == obs_id,
            PersonObservation.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True
