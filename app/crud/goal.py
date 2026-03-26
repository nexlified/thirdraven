import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.goal import PersonGoal
from app.schemas.goal import GoalCreate, GoalPublic, GoalUpdate


def _build(row: PersonGoal) -> GoalPublic:
    return GoalPublic.model_validate(row)


async def create_goal(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: GoalCreate,
) -> GoalPublic:
    row = PersonGoal(
        person_id=person_id,
        owner_id=owner_id,
        goal_type=data.goal_type,
        body=data.body,
        target_date=data.target_date,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _build(row)


async def get_goal(
    db: AsyncSession, goal_id: uuid.UUID, owner_id: uuid.UUID
) -> GoalPublic | None:
    r = await db.execute(
        select(PersonGoal).where(
            PersonGoal.id == goal_id,
            PersonGoal.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    return _build(row) if row else None


async def list_goals(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> list[GoalPublic]:
    q = select(PersonGoal).where(
        PersonGoal.person_id == person_id,
        PersonGoal.owner_id == owner_id,
    )
    if active_only:
        q = q.where(PersonGoal.achieved_at.is_(None))
    q = q.order_by(PersonGoal.created_at.desc()).offset(skip).limit(limit)
    r = await db.execute(q)
    return [_build(row) for row in r.scalars().all()]


async def update_goal(
    db: AsyncSession,
    goal_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: GoalUpdate,
) -> GoalPublic | None:
    r = await db.execute(
        select(PersonGoal).where(
            PersonGoal.id == goal_id,
            PersonGoal.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return None
    raw = data.model_dump(exclude_unset=True)
    achieved = raw.pop("achieved", None)
    for field, value in raw.items():
        setattr(row, field, value)
    if achieved is True and row.achieved_at is None:
        row.achieved_at = datetime.utcnow()
    elif achieved is False:
        row.achieved_at = None
    row.updated_at = datetime.utcnow()
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _build(row)


async def delete_goal(
    db: AsyncSession, goal_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    r = await db.execute(
        select(PersonGoal).where(
            PersonGoal.id == goal_id,
            PersonGoal.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True
