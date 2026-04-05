import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.product import Product
from app.models.transaction import Transaction
from app.models.transaction_item import TransactionItem
from app.schemas.product import ProductSlim
from app.schemas.transaction_item import (
    TransactionItemCreate,
    TransactionItemPublic,
    TransactionItemUpdate,
)


def _naive_utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def _get_product_slim(
    db: AsyncSession, product_id: uuid.UUID | None
) -> ProductSlim | None:
    if product_id is None:
        return None
    result = await db.execute(select(Product).where(Product.id == product_id))
    row = result.scalars().first()
    if not row:
        return None
    return ProductSlim(id=row.id, name=row.name, brand=row.brand, unit=row.unit)


async def _build_public(
    db: AsyncSession, row: TransactionItem
) -> TransactionItemPublic:
    product = await _get_product_slim(db, row.product_id)
    return TransactionItemPublic(
        id=row.id,
        transaction_id=row.transaction_id,
        product_id=row.product_id,
        product=product,
        raw_name=row.raw_name,
        quantity=row.quantity,
        unit=row.unit,
        unit_price=row.unit_price,
        total_price=row.total_price,
        currency=row.currency,
        discount=row.discount,
        store_name=row.store_name,
        import_batch_id=row.import_batch_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _get_transaction(
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


async def create_transaction_item(
    db: AsyncSession,
    owner_id: uuid.UUID,
    transaction_id: uuid.UUID,
    data: TransactionItemCreate,
) -> TransactionItemPublic | None:
    tx = await _get_transaction(db, transaction_id, owner_id)
    if not tx:
        return None

    row = TransactionItem(
        owner_id=owner_id,
        transaction_id=transaction_id,
        **data.model_dump(exclude_unset=True),
    )
    db.add(row)
    await db.flush()  # Obtain ID without committing

    if row.product_id is not None:
        from app.crud.inventory import update_inventory_on_purchase

        await update_inventory_on_purchase(
            db, owner_id, row.product_id, row.quantity, tx.transacted_on
        )

    await db.commit()
    await db.refresh(row)
    return await _build_public(db, row)


async def create_transaction_items_bulk(
    db: AsyncSession,
    owner_id: uuid.UUID,
    transaction_id: uuid.UUID,
    items: list[TransactionItemCreate],
) -> list[TransactionItemPublic] | None:
    tx = await _get_transaction(db, transaction_id, owner_id)
    if not tx:
        return None

    rows: list[TransactionItem] = []
    for data in items:
        row = TransactionItem(
            owner_id=owner_id,
            transaction_id=transaction_id,
            **data.model_dump(exclude_unset=True),
        )
        db.add(row)
        await db.flush()
        rows.append(row)

    for row in rows:
        if row.product_id is not None:
            from app.crud.inventory import update_inventory_on_purchase

            await update_inventory_on_purchase(
                db, owner_id, row.product_id, row.quantity, tx.transacted_on
            )

    await db.commit()
    return [await _build_public(db, row) for row in rows]


async def list_transaction_items(
    db: AsyncSession,
    owner_id: uuid.UUID,
    transaction_id: uuid.UUID,
) -> list[TransactionItemPublic] | None:
    tx = await _get_transaction(db, transaction_id, owner_id)
    if not tx:
        return None

    result = await db.execute(
        select(TransactionItem).where(
            TransactionItem.transaction_id == transaction_id,
            TransactionItem.owner_id == owner_id,
        )
    )
    rows = result.scalars().all()
    return [await _build_public(db, row) for row in rows]


async def update_transaction_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: TransactionItemUpdate,
) -> TransactionItemPublic | None:
    result = await db.execute(
        select(TransactionItem).where(
            TransactionItem.id == item_id,
            TransactionItem.owner_id == owner_id,
        )
    )
    row = result.scalars().first()
    if not row:
        return None

    raw = data.model_dump(exclude_unset=True)
    for field, value in raw.items():
        setattr(row, field, value)

    row.updated_at = _naive_utc_now()
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_public(db, row)


async def delete_transaction_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> bool:
    result = await db.execute(
        select(TransactionItem).where(
            TransactionItem.id == item_id,
            TransactionItem.owner_id == owner_id,
        )
    )
    row = result.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True
