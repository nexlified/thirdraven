import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.followup import PersonFollowUp
from app.schemas.followup import FollowUpCreate, FollowUpPublic, FollowUpUpdate


def _build(row: PersonFollowUp) -> FollowUpPublic:
    return FollowUpPublic.model_validate(row)


async def create_followup(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: FollowUpCreate,
) -> FollowUpPublic:
    row = PersonFollowUp(
        person_id=person_id,
        owner_id=owner_id,
        body=data.body,
        due_on=data.due_on,
        interaction_id=data.interaction_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _build(row)


async def get_followup(
    db: AsyncSession, followup_id: uuid.UUID, owner_id: uuid.UUID
) -> FollowUpPublic | None:
    r = await db.execute(
        select(PersonFollowUp).where(
            PersonFollowUp.id == followup_id,
            PersonFollowUp.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    return _build(row) if row else None


async def list_followups(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    pending_only: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> list[FollowUpPublic]:
    q = select(PersonFollowUp).where(
        PersonFollowUp.person_id == person_id,
        PersonFollowUp.owner_id == owner_id,
    )
    if pending_only:
        q = q.where(PersonFollowUp.cleared_at.is_(None))
    q = q.order_by(PersonFollowUp.due_on.asc().nulls_last()).offset(skip).limit(limit)
    r = await db.execute(q)
    return [_build(row) for row in r.scalars().all()]


async def update_followup(
    db: AsyncSession,
    followup_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: FollowUpUpdate,
) -> FollowUpPublic | None:
    r = await db.execute(
        select(PersonFollowUp).where(
            PersonFollowUp.id == followup_id,
            PersonFollowUp.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return None
    raw = data.model_dump(exclude_unset=True)
    cleared = raw.pop("cleared", None)
    for field, value in raw.items():
        setattr(row, field, value)
    if cleared is True:
        row.cleared_at = datetime.utcnow()
    elif cleared is False:
        row.cleared_at = None
    row.updated_at = datetime.utcnow()
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _build(row)


async def delete_followup(
    db: AsyncSession, followup_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    r = await db.execute(
        select(PersonFollowUp).where(
            PersonFollowUp.id == followup_id,
            PersonFollowUp.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True
