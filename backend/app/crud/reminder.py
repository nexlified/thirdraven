import uuid
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.reminder import Reminder
from app.schemas.reminder import ReminderCreate, ReminderPublic, ReminderUpdate


async def create_reminder(
    db: AsyncSession, owner_id: uuid.UUID, data: ReminderCreate
) -> ReminderPublic:
    row = Reminder(
        owner_id=owner_id,
        title=data.title,
        body=data.body,
        due_at=data.due_at,
        remind_at=data.remind_at,
        recurrence=data.recurrence,
        person_id=data.person_id,
        asset_id=data.asset_id,
        subscription_id=data.subscription_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ReminderPublic.model_validate(row)


async def get_reminder(
    db: AsyncSession, reminder_id: uuid.UUID, owner_id: uuid.UUID
) -> ReminderPublic | None:
    r = await db.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.owner_id == owner_id,
            Reminder.deleted_at.is_(None),
        )
    )
    row = r.scalars().first()
    if not row:
        return None
    return ReminderPublic.model_validate(row)


async def list_reminders(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    is_done: bool | None = None,
    person_id: uuid.UUID | None = None,
    asset_id: uuid.UUID | None = None,
    subscription_id: uuid.UUID | None = None,
) -> tuple[list[ReminderPublic], int]:
    base = select(Reminder).where(
        Reminder.owner_id == owner_id, Reminder.deleted_at.is_(None)
    )
    if is_done is not None:
        base = base.where(Reminder.is_done == is_done)
    if person_id:
        base = base.where(Reminder.person_id == person_id)
    if asset_id:
        base = base.where(Reminder.asset_id == asset_id)
    if subscription_id:
        base = base.where(Reminder.subscription_id == subscription_id)

    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    r = await db.execute(base.order_by(Reminder.due_at.asc()).offset(skip).limit(limit))
    rows = r.scalars().all()
    return [ReminderPublic.model_validate(row) for row in rows], total


async def update_reminder(
    db: AsyncSession,
    reminder_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: ReminderUpdate,
) -> ReminderPublic | None:
    r = await db.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.owner_id == owner_id,
            Reminder.deleted_at.is_(None),
        )
    )
    row = r.scalars().first()
    if not row:
        return None

    raw = data.model_dump(exclude_unset=True)
    if "is_done" in raw and raw["is_done"] and not row.is_done:
        row.done_at = datetime.now(UTC)
    for field, value in raw.items():
        setattr(row, field, value)
    row.updated_at = datetime.now(UTC)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ReminderPublic.model_validate(row)


async def soft_delete_reminder(
    db: AsyncSession, reminder_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    r = await db.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.owner_id == owner_id,
            Reminder.deleted_at.is_(None),
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    row.deleted_at = datetime.now(UTC)
    db.add(row)
    await db.commit()
    return True
