import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.loan import Loan
from app.schemas.loan import LoanCreate, LoanPublic, LoanUpdate


async def create_loan(
    db: AsyncSession, owner_id: uuid.UUID, data: LoanCreate
) -> LoanPublic:
    row = Loan(
        owner_id=owner_id,
        person_id=data.person_id,
        direction=data.direction,
        loan_type=data.loan_type,
        description=data.description,
        amount=data.amount,
        currency=data.currency,
        item_name=data.item_name,
        loaned_on=data.loaned_on,
        due_on=data.due_on,
        notes=data.notes,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return LoanPublic.model_validate(row)


async def get_loan(
    db: AsyncSession, loan_id: uuid.UUID, owner_id: uuid.UUID
) -> LoanPublic | None:
    r = await db.execute(
        select(Loan).where(
            Loan.id == loan_id,
            Loan.owner_id == owner_id,
            Loan.deleted_at.is_(None),
        )
    )
    row = r.scalars().first()
    if not row:
        return None
    return LoanPublic.model_validate(row)


async def list_loans(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    direction: str | None = None,
    person_id: uuid.UUID | None = None,
) -> tuple[list[LoanPublic], int]:
    base = select(Loan).where(Loan.owner_id == owner_id, Loan.deleted_at.is_(None))
    if status:
        base = base.where(Loan.status == status)
    if direction:
        base = base.where(Loan.direction == direction)
    if person_id:
        base = base.where(Loan.person_id == person_id)

    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    r = await db.execute(
        base.order_by(Loan.created_at.desc()).offset(skip).limit(limit)
    )
    rows = r.scalars().all()
    return [LoanPublic.model_validate(row) for row in rows], total


async def update_loan(
    db: AsyncSession,
    loan_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: LoanUpdate,
) -> LoanPublic | None:
    r = await db.execute(
        select(Loan).where(
            Loan.id == loan_id,
            Loan.owner_id == owner_id,
            Loan.deleted_at.is_(None),
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
    return LoanPublic.model_validate(row)


async def soft_delete_loan(
    db: AsyncSession, loan_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    r = await db.execute(
        select(Loan).where(
            Loan.id == loan_id,
            Loan.owner_id == owner_id,
            Loan.deleted_at.is_(None),
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    row.deleted_at = datetime.utcnow()
    db.add(row)
    await db.commit()
    return True
