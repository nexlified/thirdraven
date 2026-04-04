import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.vocabulary import resolve_optional_term_slug
from app.models.transaction import Transaction
from app.models.vocabulary import Term
from app.schemas.transaction import (
    TransactionCreate,
    TransactionPublic,
    TransactionUpdate,
)
from app.schemas.vocabulary import TermSlim


async def _get_term(db: AsyncSession, term_id: uuid.UUID | None) -> TermSlim | None:
    if term_id is None:
        return None
    result = await db.execute(select(Term).where(Term.id == term_id))
    t = result.scalars().first()
    return TermSlim.model_validate(t) if t else None


async def _build_transaction_public(
    db: AsyncSession, row: Transaction
) -> TransactionPublic:
    category = await _get_term(db, row.category_term_id)
    payment_method = await _get_term(db, row.payment_method_term_id)
    return TransactionPublic(
        id=row.id,
        owner_id=row.owner_id,
        transaction_type=row.transaction_type,
        amount=row.amount,
        currency=row.currency,
        transacted_on=row.transacted_on,
        description=row.description,
        category=category,
        payment_method=payment_method,
        asset_id=row.asset_id,
        subscription_id=row.subscription_id,
        merchant=row.merchant,
        reference=row.reference,
        tags=row.tags or [],
        import_batch_id=row.import_batch_id,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _category_vocab(transaction_type: str) -> str:
    if transaction_type == "expense":
        return "expense-categories"
    return "income-categories"


async def create_transaction(
    db: AsyncSession, owner_id: uuid.UUID, data: TransactionCreate
) -> TransactionPublic:
    raw = data.model_dump(exclude_unset=True)
    category_slug = raw.pop("category", None)
    payment_method_slug = raw.pop("payment_method", None)
    tags = raw.pop("tags", [])

    category_term_id = await resolve_optional_term_slug(
        db, _category_vocab(data.transaction_type), category_slug
    )
    payment_method_term_id = await resolve_optional_term_slug(
        db, "payment-methods", payment_method_slug
    )

    row = Transaction(
        owner_id=owner_id,
        category_term_id=category_term_id,
        payment_method_term_id=payment_method_term_id,
        tags=tags or None,
        **raw,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_transaction_public(db, row)


async def get_transaction(
    db: AsyncSession, transaction_id: uuid.UUID, owner_id: uuid.UUID
) -> Transaction | None:
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.owner_id == owner_id,
            Transaction.deleted_at.is_(None),
        )
    )
    return result.scalars().first()


async def get_transaction_public(
    db: AsyncSession, transaction_id: uuid.UUID, owner_id: uuid.UUID
) -> TransactionPublic | None:
    row = await get_transaction(db, transaction_id, owner_id)
    if not row:
        return None
    return await _build_transaction_public(db, row)


async def list_transactions(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    *,
    transaction_type: str | None = None,
    category_slug: str | None = None,
    payment_method_slug: str | None = None,
    asset_id: uuid.UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search: str | None = None,
) -> tuple[list[TransactionPublic], int]:
    from datetime import date

    query = select(Transaction).where(
        Transaction.owner_id == owner_id,
        Transaction.deleted_at.is_(None),
    )

    if transaction_type is not None:
        query = query.where(Transaction.transaction_type == transaction_type)

    if category_slug is not None:
        vocab = _category_vocab(transaction_type) if transaction_type else None
        if vocab:
            cat_id = await resolve_optional_term_slug(db, vocab, category_slug)
        else:
            term_result = await db.execute(
                select(Term).where(Term.slug == category_slug, Term.is_active.is_(True))
            )
            term = term_result.scalars().first()
            cat_id = term.id if term else None
        if cat_id is None:
            return [], 0
        query = query.where(Transaction.category_term_id == cat_id)

    if payment_method_slug is not None:
        pm_id = await resolve_optional_term_slug(
            db, "payment-methods", payment_method_slug
        )
        if pm_id is None:
            return [], 0
        query = query.where(Transaction.payment_method_term_id == pm_id)

    if asset_id is not None:
        query = query.where(Transaction.asset_id == asset_id)

    if date_from is not None:
        query = query.where(Transaction.transacted_on >= date.fromisoformat(date_from))

    if date_to is not None:
        query = query.where(Transaction.transacted_on <= date.fromisoformat(date_to))

    if search is not None:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Transaction.description.ilike(pattern),
                Transaction.merchant.ilike(pattern),
            )
        )

    total = (
        await db.execute(select(func.count()).select_from(query.subquery()))
    ).scalar_one()

    result = await db.execute(
        query.order_by(
            Transaction.transacted_on.desc(), Transaction.created_at.desc()
        )
        .offset(skip)
        .limit(limit)
    )
    return [
        await _build_transaction_public(db, row) for row in result.scalars().all()
    ], total


async def update_transaction(
    db: AsyncSession,
    transaction_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: TransactionUpdate,
) -> TransactionPublic | None:
    row = await get_transaction(db, transaction_id, owner_id)
    if not row:
        return None

    raw = data.model_dump(exclude_unset=True)
    category_slug = raw.pop("category", None)
    payment_method_slug = raw.pop("payment_method", None)

    # Resolve category if type or category changed
    if category_slug is not None or "transaction_type" in raw:
        effective_type = raw.get("transaction_type", row.transaction_type)
        row.category_term_id = await resolve_optional_term_slug(
            db, _category_vocab(effective_type), category_slug
        )

    if payment_method_slug is not None:
        row.payment_method_term_id = await resolve_optional_term_slug(
            db, "payment-methods", payment_method_slug
        )

    for field, value in raw.items():
        setattr(row, field, value)

    row.updated_at = datetime.now(UTC)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_transaction_public(db, row)


async def soft_delete_transaction(
    db: AsyncSession, transaction_id: uuid.UUID, owner_id: uuid.UUID
) -> Transaction | None:
    row = await get_transaction(db, transaction_id, owner_id)
    if not row:
        return None
    row.deleted_at = datetime.now(UTC)
    db.add(row)
    await db.commit()
    return row


async def create_transactions_bulk(
    db: AsyncSession, owner_id: uuid.UUID, items: list[TransactionCreate]
) -> list[TransactionPublic]:
    results: list[TransactionPublic] = []
    for item_data in items:
        raw = item_data.model_dump(exclude_unset=True)
        category_slug = raw.pop("category", None)
        payment_method_slug = raw.pop("payment_method", None)
        tags = raw.pop("tags", [])

        category_term_id = await resolve_optional_term_slug(
            db, _category_vocab(item_data.transaction_type), category_slug
        )
        payment_method_term_id = await resolve_optional_term_slug(
            db, "payment-methods", payment_method_slug
        )

        row = Transaction(
            owner_id=owner_id,
            category_term_id=category_term_id,
            payment_method_term_id=payment_method_term_id,
            tags=tags or None,
            **raw,
        )
        db.add(row)
        await db.flush()
        results.append(await _build_transaction_public(db, row))

    await db.commit()
    return results
