import uuid
from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.vocabulary import resolve_optional_term_slug, resolve_term_slug
from app.models.tracked_record import TrackedRecord
from app.models.vocabulary import Term
from app.schemas.tracked_record import RecordCreate, RecordPublic, RecordUpdate
from app.schemas.vocabulary import TermSlim


def _compute_expiry(expires_on: date | None) -> tuple[bool, int | None]:
    today = date.today()
    if expires_on is None:
        return False, None
    delta = (expires_on - today).days
    return delta < 0, delta if delta >= 0 else None


async def _build(db: AsyncSession, row: TrackedRecord) -> RecordPublic:
    r = await db.execute(select(Term).where(Term.id == row.record_type_id))
    term = r.scalars().first()
    record_type = (
        TermSlim.model_validate(term)
        if term
        else TermSlim(id=row.record_type_id, name="", slug="")
    )

    is_expired, days_until_expiry = _compute_expiry(row.expires_on)

    return RecordPublic(
        id=row.id,
        owner_id=row.owner_id,
        record_type=record_type,
        title=row.title,
        reference_number=row.reference_number,
        issuer=row.issuer,
        issued_on=row.issued_on,
        expires_on=row.expires_on,
        reminder_days=row.reminder_days,
        cost=row.cost,
        currency=row.currency,
        billing_frequency=row.billing_frequency,
        auto_renews=row.auto_renews,
        coverage_notes=row.coverage_notes,
        metadata_=row.metadata_,
        asset_id=row.asset_id,
        person_id=row.person_id,
        notes=row.notes,
        is_expired=is_expired,
        days_until_expiry=days_until_expiry,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _resolve_fields(db: AsyncSession, raw: dict) -> dict:
    result = {}
    for k, v in raw.items():
        if k == "record_type":
            result["record_type_id"] = await resolve_term_slug(db, "record-types", v)
        else:
            result[k] = v
    return result


async def create_record(
    db: AsyncSession, owner_id: uuid.UUID, data: RecordCreate
) -> RecordPublic:
    db_fields = await _resolve_fields(db, data.model_dump(exclude_unset=True))
    row = TrackedRecord(owner_id=owner_id, **db_fields)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build(db, row)


async def get_record(
    db: AsyncSession, record_id: uuid.UUID, owner_id: uuid.UUID
) -> RecordPublic | None:
    r = await db.execute(
        select(TrackedRecord).where(
            TrackedRecord.id == record_id,
            TrackedRecord.owner_id == owner_id,
            TrackedRecord.deleted_at.is_(None),
        )
    )
    row = r.scalars().first()
    return await _build(db, row) if row else None


async def list_records(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    record_type_slug: str | None = None,
    asset_id: uuid.UUID | None = None,
    person_id: uuid.UUID | None = None,
    expires_before: date | None = None,
) -> tuple[list[RecordPublic], int]:
    base = select(TrackedRecord).where(
        TrackedRecord.owner_id == owner_id,
        TrackedRecord.deleted_at.is_(None),
    )
    if record_type_slug is not None:
        term_id = await resolve_optional_term_slug(db, "record-types", record_type_slug)
        if term_id:
            base = base.where(TrackedRecord.record_type_id == term_id)
    if asset_id is not None:
        base = base.where(TrackedRecord.asset_id == asset_id)
    if person_id is not None:
        base = base.where(TrackedRecord.person_id == person_id)
    if expires_before is not None:
        base = base.where(TrackedRecord.expires_on <= expires_before)
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    r = await db.execute(
        base.order_by(TrackedRecord.expires_on.asc().nulls_last())
        .offset(skip)
        .limit(limit)
    )
    return [await _build(db, row) for row in r.scalars().all()], total


async def update_record(
    db: AsyncSession,
    record_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: RecordUpdate,
) -> RecordPublic | None:
    r = await db.execute(
        select(TrackedRecord).where(
            TrackedRecord.id == record_id,
            TrackedRecord.owner_id == owner_id,
            TrackedRecord.deleted_at.is_(None),
        )
    )
    row = r.scalars().first()
    if not row:
        return None
    db_fields = await _resolve_fields(db, data.model_dump(exclude_unset=True))
    for field, value in db_fields.items():
        setattr(row, field, value)
    row.updated_at = datetime.utcnow()
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build(db, row)


async def delete_record(
    db: AsyncSession, record_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    r = await db.execute(
        select(TrackedRecord).where(
            TrackedRecord.id == record_id,
            TrackedRecord.owner_id == owner_id,
            TrackedRecord.deleted_at.is_(None),
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    row.deleted_at = datetime.utcnow()
    db.add(row)
    await db.commit()
    return True
