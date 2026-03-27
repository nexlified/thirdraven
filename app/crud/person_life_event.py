import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.vocabulary import resolve_optional_term_slug
from app.models.person_life_event import PersonLifeEvent, PersonSignificantDate
from app.models.vocabulary import Term
from app.schemas.person_life_event import (
    LifeEventCreate,
    LifeEventPublic,
    LifeEventUpdate,
    SignificantDateCreate,
    SignificantDatePublic,
    SignificantDateUpdate,
)
from app.schemas.vocabulary import TermSlim


async def _build_life_event_public(
    db: AsyncSession, row: PersonLifeEvent
) -> LifeEventPublic:
    event_type = None
    if row.event_type_term_id:
        r = await db.execute(select(Term).where(Term.id == row.event_type_term_id))
        t = r.scalars().first()
        if t:
            event_type = TermSlim.model_validate(t)

    return LifeEventPublic(
        id=row.id,
        person_id=row.person_id,
        owner_id=row.owner_id,
        event_type=event_type,
        title=row.title,
        description=row.description,
        occurred_on=row.occurred_on,
        occurred_year=row.occurred_year,
        metadata_=row.metadata_,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


# ── Life Event CRUD ────────────────────────────────────────────────────────────


async def create_life_event(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: LifeEventCreate,
) -> LifeEventPublic:
    event_type_term_id = None
    if data.event_type:
        event_type_term_id = await resolve_optional_term_slug(
            db, "life-event-types", data.event_type
        )

    row = PersonLifeEvent(
        person_id=person_id,
        owner_id=owner_id,
        event_type_term_id=event_type_term_id,
        title=data.title,
        description=data.description,
        occurred_on=data.occurred_on,
        occurred_year=data.occurred_year,
        metadata_=data.metadata_,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_life_event_public(db, row)


async def get_life_event(
    db: AsyncSession, event_id: uuid.UUID, owner_id: uuid.UUID
) -> LifeEventPublic | None:
    r = await db.execute(
        select(PersonLifeEvent).where(
            PersonLifeEvent.id == event_id,
            PersonLifeEvent.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return None
    return await _build_life_event_public(db, row)


async def list_life_events(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[LifeEventPublic], int]:
    base = select(PersonLifeEvent).where(
        PersonLifeEvent.person_id == person_id,
        PersonLifeEvent.owner_id == owner_id,
    )
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    r = await db.execute(
        base.order_by(PersonLifeEvent.occurred_on.asc().nulls_last())
        .offset(skip)
        .limit(limit)
    )
    rows = r.scalars().all()
    return [await _build_life_event_public(db, row) for row in rows], total


async def update_life_event(
    db: AsyncSession,
    event_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: LifeEventUpdate,
) -> LifeEventPublic | None:
    r = await db.execute(
        select(PersonLifeEvent).where(
            PersonLifeEvent.id == event_id,
            PersonLifeEvent.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return None

    raw = data.model_dump(exclude_unset=True)
    if "event_type" in raw:
        row.event_type_term_id = await resolve_optional_term_slug(
            db, "life-event-types", raw.pop("event_type")
        )
    for field, value in raw.items():
        setattr(row, field, value)
    row.updated_at = datetime.utcnow()
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_life_event_public(db, row)


async def delete_life_event(
    db: AsyncSession, event_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    r = await db.execute(
        select(PersonLifeEvent).where(
            PersonLifeEvent.id == event_id,
            PersonLifeEvent.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True


# ── Significant Date CRUD ──────────────────────────────────────────────────────


async def create_significant_date(
    db: AsyncSession,
    person_id: uuid.UUID,
    data: SignificantDateCreate,
) -> SignificantDatePublic:
    row = PersonSignificantDate(
        person_id=person_id,
        label=data.label,
        month=data.month,
        day=data.day,
        year=data.year,
        recurs_annually=data.recurs_annually,
        notes=data.notes,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return SignificantDatePublic.model_validate(row)


async def get_significant_date(
    db: AsyncSession, date_id: uuid.UUID, person_id: uuid.UUID
) -> SignificantDatePublic | None:
    r = await db.execute(
        select(PersonSignificantDate).where(
            PersonSignificantDate.id == date_id,
            PersonSignificantDate.person_id == person_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return None
    return SignificantDatePublic.model_validate(row)


async def list_significant_dates(
    db: AsyncSession, person_id: uuid.UUID
) -> list[SignificantDatePublic]:
    r = await db.execute(
        select(PersonSignificantDate)
        .where(PersonSignificantDate.person_id == person_id)
        .order_by(PersonSignificantDate.month.asc(), PersonSignificantDate.day.asc())
    )
    rows = r.scalars().all()
    return [SignificantDatePublic.model_validate(row) for row in rows]


async def update_significant_date(
    db: AsyncSession,
    date_id: uuid.UUID,
    person_id: uuid.UUID,
    data: SignificantDateUpdate,
) -> SignificantDatePublic | None:
    r = await db.execute(
        select(PersonSignificantDate).where(
            PersonSignificantDate.id == date_id,
            PersonSignificantDate.person_id == person_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    row.updated_at = datetime.utcnow()
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return SignificantDatePublic.model_validate(row)


async def delete_significant_date(
    db: AsyncSession, date_id: uuid.UUID, person_id: uuid.UUID
) -> bool:
    r = await db.execute(
        select(PersonSignificantDate).where(
            PersonSignificantDate.id == date_id,
            PersonSignificantDate.person_id == person_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True
