import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.vocabulary import resolve_optional_term_slug
from app.models.life_event import LifeEvent, LifeEventPerson
from app.models.person import Person
from app.models.person_life_event import PersonSignificantDate
from app.models.vocabulary import Term
from app.schemas.life_event import (
    LifeEventCreate,
    LifeEventParticipantPublic,
    LifeEventPublic,
    LifeEventUpdate,
    SignificantDateCreate,
    SignificantDatePublic,
    SignificantDateUpdate,
)
from app.schemas.vocabulary import TermSlim


async def _resolve_term(db: AsyncSession, term_id: uuid.UUID | None) -> TermSlim | None:
    if not term_id:
        return None
    r = await db.execute(select(Term).where(Term.id == term_id))
    t = r.scalars().first()
    return TermSlim.model_validate(t) if t else None


async def _build_participants(
    db: AsyncSession, life_event_id: uuid.UUID
) -> list[LifeEventParticipantPublic]:
    r = await db.execute(
        select(LifeEventPerson, Person)
        .join(Person, Person.id == LifeEventPerson.person_id)
        .where(LifeEventPerson.life_event_id == life_event_id)
    )
    return [
        LifeEventParticipantPublic(
            person_id=lep.person_id,
            first_name=p.first_name,
            last_name=p.last_name,
            role=lep.role,
        )
        for lep, p in r.all()
    ]


async def _build_life_event_public(
    db: AsyncSession, row: LifeEvent
) -> LifeEventPublic:
    event_type = await _resolve_term(db, row.event_type_term_id)
    emotion = await _resolve_term(db, row.emotion_term_id)
    participants = await _build_participants(db, row.id)

    return LifeEventPublic(
        id=row.id,
        owner_id=row.owner_id,
        event_type=event_type,
        title=row.title,
        description=row.description,
        occurred_on=row.occurred_on,
        occurred_year=row.occurred_year,
        emotion=emotion,
        cost=row.cost,
        currency=row.currency,
        duration_minutes=row.duration_minutes,
        place=row.place,
        metadata_=row.metadata_,
        participants=participants,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


# ── Life Event CRUD ───────────────────────────────────────────────────────────


async def create_life_event(
    db: AsyncSession,
    owner_id: uuid.UUID,
    data: LifeEventCreate,
) -> LifeEventPublic:
    event_type_term_id = None
    if data.event_type:
        event_type_term_id = await resolve_optional_term_slug(
            db, "life-event-types", data.event_type
        )
    emotion_term_id = None
    if data.emotion:
        emotion_term_id = await resolve_optional_term_slug(
            db, "life-event-emotions", data.emotion
        )

    row = LifeEvent(
        owner_id=owner_id,
        event_type_term_id=event_type_term_id,
        title=data.title,
        description=data.description,
        occurred_on=data.occurred_on,
        occurred_year=data.occurred_year,
        emotion_term_id=emotion_term_id,
        cost=data.cost,
        currency=data.currency,
        duration_minutes=data.duration_minutes,
        place=data.place,
        metadata_=data.metadata_,
    )
    db.add(row)
    await db.flush()

    for p in data.participants:
        db.add(LifeEventPerson(
            life_event_id=row.id,
            person_id=p.person_id,
            role=p.role,
        ))

    await db.commit()
    await db.refresh(row)
    return await _build_life_event_public(db, row)


async def get_life_event(
    db: AsyncSession, event_id: uuid.UUID, owner_id: uuid.UUID
) -> LifeEventPublic | None:
    r = await db.execute(
        select(LifeEvent).where(
            LifeEvent.id == event_id,
            LifeEvent.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return None
    return await _build_life_event_public(db, row)


async def list_life_events(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[LifeEventPublic], int]:
    base = select(LifeEvent).where(LifeEvent.owner_id == owner_id)
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    r = await db.execute(
        base.order_by(LifeEvent.occurred_on.asc().nulls_last())
        .offset(skip)
        .limit(limit)
    )
    rows = r.scalars().all()
    return [await _build_life_event_public(db, row) for row in rows], total


async def list_life_events_for_person(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[LifeEventPublic], int]:
    base = (
        select(LifeEvent)
        .join(LifeEventPerson, LifeEventPerson.life_event_id == LifeEvent.id)
        .where(
            LifeEventPerson.person_id == person_id,
            LifeEvent.owner_id == owner_id,
        )
    )
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    r = await db.execute(
        base.order_by(LifeEvent.occurred_on.asc().nulls_last())
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
        select(LifeEvent).where(
            LifeEvent.id == event_id,
            LifeEvent.owner_id == owner_id,
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
    if "emotion" in raw:
        row.emotion_term_id = await resolve_optional_term_slug(
            db, "life-event-emotions", raw.pop("emotion")
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
        select(LifeEvent).where(
            LifeEvent.id == event_id,
            LifeEvent.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    # Delete participants first
    participants = await db.execute(
        select(LifeEventPerson).where(LifeEventPerson.life_event_id == event_id)
    )
    for p in participants.scalars().all():
        await db.delete(p)
    await db.delete(row)
    await db.commit()
    return True


async def add_participant(
    db: AsyncSession,
    event_id: uuid.UUID,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    role: str | None = "participant",
) -> LifeEventPublic | None:
    event = await db.execute(
        select(LifeEvent).where(
            LifeEvent.id == event_id,
            LifeEvent.owner_id == owner_id,
        )
    )
    if not event.scalars().first():
        return None
    db.add(LifeEventPerson(
        life_event_id=event_id,
        person_id=person_id,
        role=role,
    ))
    await db.commit()
    return await get_life_event(db, event_id, owner_id)


async def remove_participant(
    db: AsyncSession,
    event_id: uuid.UUID,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> bool:
    event = await db.execute(
        select(LifeEvent).where(
            LifeEvent.id == event_id,
            LifeEvent.owner_id == owner_id,
        )
    )
    if not event.scalars().first():
        return False
    r = await db.execute(
        select(LifeEventPerson).where(
            LifeEventPerson.life_event_id == event_id,
            LifeEventPerson.person_id == person_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True


# ── Significant Date CRUD ─────────────────────────────────────────────────────


async def _build_significant_date_public(
    db: AsyncSession, row: PersonSignificantDate
) -> SignificantDatePublic:
    date_type = await _resolve_term(db, row.date_type_term_id)
    return SignificantDatePublic(
        id=row.id,
        person_id=row.person_id,
        date_type=date_type,
        label=row.label,
        month=row.month,
        day=row.day,
        year=row.year,
        recurs_annually=row.recurs_annually,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def create_significant_date(
    db: AsyncSession,
    person_id: uuid.UUID,
    data: SignificantDateCreate,
) -> SignificantDatePublic:
    date_type_term_id = None
    if data.date_type:
        date_type_term_id = await resolve_optional_term_slug(
            db, "significant-date-types", data.date_type
        )
    row = PersonSignificantDate(
        person_id=person_id,
        date_type_term_id=date_type_term_id,
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
    return await _build_significant_date_public(db, row)


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
    return await _build_significant_date_public(db, row)


async def list_significant_dates(
    db: AsyncSession, person_id: uuid.UUID
) -> list[SignificantDatePublic]:
    r = await db.execute(
        select(PersonSignificantDate)
        .where(PersonSignificantDate.person_id == person_id)
        .order_by(PersonSignificantDate.month.asc(), PersonSignificantDate.day.asc())
    )
    rows = r.scalars().all()
    return [await _build_significant_date_public(db, row) for row in rows]


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

    raw = data.model_dump(exclude_unset=True)
    if "date_type" in raw:
        slug = raw.pop("date_type")
        row.date_type_term_id = await resolve_optional_term_slug(
            db, "significant-date-types", slug
        ) if slug else None
    for field, value in raw.items():
        setattr(row, field, value)
    row.updated_at = datetime.utcnow()
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_significant_date_public(db, row)


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
