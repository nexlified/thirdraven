import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import extract, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.vocabulary import resolve_term_slug
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.models.vocabulary import Term
from app.schemas.budget import BudgetCreate, BudgetPublic, BudgetUpdate, BudgetWithSpend
from app.schemas.vocabulary import TermSlim


async def _get_term(db: AsyncSession, term_id: uuid.UUID) -> TermSlim:
    result = await db.execute(select(Term).where(Term.id == term_id))
    t = result.scalars().first()
    if not t:
        raise HTTPException(status_code=500, detail="Category term not found")
    return TermSlim.model_validate(t)


async def _build_budget_public(db: AsyncSession, row: Budget) -> BudgetPublic:
    category = await _get_term(db, row.category_term_id)
    return BudgetPublic(
        id=row.id,
        owner_id=row.owner_id,
        category=category,
        year=row.year,
        month=row.month,
        amount=row.amount,
        currency=row.currency,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def create_budget(
    db: AsyncSession, owner_id: uuid.UUID, data: BudgetCreate
) -> BudgetPublic:
    category_term_id = await resolve_term_slug(db, "expense-categories", data.category)
    row = Budget(
        owner_id=owner_id,
        category_term_id=category_term_id,
        year=data.year,
        month=data.month,
        amount=data.amount,
        currency=data.currency,
        notes=data.notes,
    )
    db.add(row)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Budget already exists for this category and month",
        ) from None
    await db.refresh(row)
    return await _build_budget_public(db, row)


async def list_budgets(
    db: AsyncSession, owner_id: uuid.UUID, year: int, month: int
) -> list[BudgetWithSpend]:
    result = await db.execute(
        select(Budget).where(
            Budget.owner_id == owner_id,
            Budget.year == year,
            Budget.month == month,
        )
    )
    budgets = result.scalars().all()

    if not budgets:
        return []

    # Batch aggregate transaction totals grouped by (category_term_id, currency)
    agg_result = await db.execute(
        select(
            Transaction.category_term_id,
            Transaction.currency,
            func.sum(Transaction.amount).label("total"),
        )
        .where(
            Transaction.owner_id == owner_id,
            Transaction.transaction_type == "expense",
            Transaction.deleted_at.is_(None),
            extract("year", Transaction.transacted_on) == year,
            extract("month", Transaction.transacted_on) == month,
        )
        .group_by(Transaction.category_term_id, Transaction.currency)
    )
    spent_map: dict[tuple[uuid.UUID, str], float] = {
        (row.category_term_id, row.currency): float(row.total)
        for row in agg_result.all()
    }

    # Bulk-load all category terms
    term_ids = [b.category_term_id for b in budgets]
    term_result = await db.execute(select(Term).where(Term.id.in_(term_ids)))
    term_map: dict[uuid.UUID, TermSlim] = {
        t.id: TermSlim.model_validate(t) for t in term_result.scalars().all()
    }

    items: list[BudgetWithSpend] = []
    for b in budgets:
        category = term_map.get(b.category_term_id)
        if not category:
            continue
        spent = spent_map.get((b.category_term_id, b.currency), 0.0)
        remaining = b.amount - spent
        utilization = spent / b.amount if b.amount != 0 else 0.0
        items.append(
            BudgetWithSpend(
                id=b.id,
                owner_id=b.owner_id,
                category=category,
                year=b.year,
                month=b.month,
                amount=b.amount,
                currency=b.currency,
                notes=b.notes,
                created_at=b.created_at,
                updated_at=b.updated_at,
                spent=spent,
                remaining=remaining,
                utilization=utilization,
            )
        )

    items.sort(key=lambda x: x.category.name)
    return items


async def update_budget(
    db: AsyncSession, budget_id: uuid.UUID, owner_id: uuid.UUID, data: BudgetUpdate
) -> BudgetPublic | None:
    result = await db.execute(
        select(Budget).where(
            Budget.id == budget_id,
            Budget.owner_id == owner_id,
        )
    )
    row = result.scalars().first()
    if not row:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(row, field, value)

    row.updated_at = datetime.now(UTC).replace(tzinfo=None)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_budget_public(db, row)


async def delete_budget(
    db: AsyncSession, budget_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    result = await db.execute(
        select(Budget).where(
            Budget.id == budget_id,
            Budget.owner_id == owner_id,
        )
    )
    row = result.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True
