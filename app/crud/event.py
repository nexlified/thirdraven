import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.person import _build_person_slim
from app.crud.vocabulary import resolve_optional_term_slug
from app.models.event import Event, EventPerson
from app.models.person import Person
from app.models.vocabulary import Term
from app.schemas.event import (
    EventCreate,
    EventPersonCreate,
    EventPersonPublic,
    EventPublic,
    EventUpdate,
)
from app.schemas.vocabulary import TermSlim


async def _build_event_public(db: AsyncSession, row: Event) -> EventPublic:
    event_type = None
    if row.event_type_term_id:
        r = await db.execute(select(Term).where(Term.id == row.event_type_term_id))
        t = r.scalars().first()
        if t:
            event_type = TermSlim.model_validate(t)

    ep_result = await db.execute(
        select(EventPerson).where(EventPerson.event_id == row.id)
    )
    persons = []
    for ep in ep_result.scalars().all():
        pr = await db.execute(select(Person).where(Person.id == ep.person_id))
        person_row = pr.scalars().first()
        if person_row:
            persons.append(await _build_person_slim(db, person_row))

    return EventPublic(
        id=row.id,
        owner_id=row.owner_id,
        title=row.title,
        event_type=event_type,
        description=row.description,
        occurred_on=row.occurred_on,
        location=row.location,
        notes=row.notes,
        persons=persons,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _resolve_event_type(db: AsyncSession, raw: dict) -> dict:
    result = {}
    for k, v in raw.items():
        if k == "event_type":
            result["event_type_term_id"] = await resolve_optional_term_slug(
                db, "event-types", v
            )
        else:
            result[k] = v
    return result


async def create_event(
    db: AsyncSession, owner_id: uuid.UUID, data: EventCreate
) -> EventPublic:
    db_fields = await _resolve_event_type(db, data.model_dump(exclude_unset=True))
    row = Event(owner_id=owner_id, **db_fields)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_event_public(db, row)


async def get_event(
    db: AsyncSession, event_id: uuid.UUID, owner_id: uuid.UUID
) -> EventPublic | None:
    r = await db.execute(
        select(Event).where(
            Event.id == event_id,
            Event.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    return await _build_event_public(db, row) if row else None


async def list_events(
    db: AsyncSession, owner_id: uuid.UUID, skip: int = 0, limit: int = 50
) -> tuple[list[EventPublic], int]:
    base = select(Event).where(Event.owner_id == owner_id)
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    r = await db.execute(
        base.order_by(Event.occurred_on.desc().nulls_last()).offset(skip).limit(limit)
    )
    return [await _build_event_public(db, row) for row in r.scalars().all()], total


async def update_event(
    db: AsyncSession, event_id: uuid.UUID, owner_id: uuid.UUID, data: EventUpdate
) -> EventPublic | None:
    r = await db.execute(
        select(Event).where(
            Event.id == event_id,
            Event.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return None
    db_fields = await _resolve_event_type(db, data.model_dump(exclude_unset=True))
    for field, value in db_fields.items():
        setattr(row, field, value)
    row.updated_at = datetime.utcnow()
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_event_public(db, row)


async def delete_event(
    db: AsyncSession, event_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    r = await db.execute(
        select(Event).where(
            Event.id == event_id,
            Event.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True


# ── EventPerson CRUD ───────────────────────────────────────────────────────────


async def add_event_person(
    db: AsyncSession,
    event_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: EventPersonCreate,
) -> EventPersonPublic | None:
    # Verify event belongs to owner
    r = await db.execute(
        select(Event).where(Event.id == event_id, Event.owner_id == owner_id)
    )
    if not r.scalars().first():
        return None

    ep = EventPerson(event_id=event_id, person_id=data.person_id, role=data.role)
    db.add(ep)
    await db.commit()
    await db.refresh(ep)

    pr = await db.execute(select(Person).where(Person.id == ep.person_id))
    person_row = pr.scalars().first()
    person_slim = await _build_person_slim(db, person_row) if person_row else None

    return EventPersonPublic(
        id=ep.id,
        event_id=ep.event_id,
        person=person_slim,
        role=ep.role,
        created_at=ep.created_at,
    )


async def list_event_persons(
    db: AsyncSession, event_id: uuid.UUID, owner_id: uuid.UUID
) -> list[EventPersonPublic]:
    # Verify event belongs to owner
    r = await db.execute(
        select(Event).where(Event.id == event_id, Event.owner_id == owner_id)
    )
    if not r.scalars().first():
        return []

    ep_result = await db.execute(
        select(EventPerson)
        .where(EventPerson.event_id == event_id)
        .order_by(EventPerson.created_at)
    )
    results = []
    for ep in ep_result.scalars().all():
        pr = await db.execute(select(Person).where(Person.id == ep.person_id))
        person_row = pr.scalars().first()
        person_slim = await _build_person_slim(db, person_row) if person_row else None
        results.append(
            EventPersonPublic(
                id=ep.id,
                event_id=ep.event_id,
                person=person_slim,
                role=ep.role,
                created_at=ep.created_at,
            )
        )
    return results


async def remove_event_person(
    db: AsyncSession,
    event_id: uuid.UUID,
    event_person_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> bool:
    # Verify event belongs to owner
    r = await db.execute(
        select(Event).where(Event.id == event_id, Event.owner_id == owner_id)
    )
    if not r.scalars().first():
        return False

    r = await db.execute(
        select(EventPerson).where(
            EventPerson.id == event_person_id,
            EventPerson.event_id == event_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True
