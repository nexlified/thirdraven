import uuid
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.product import Product
from app.models.shopping_list import ShoppingList, ShoppingListItem
from app.models.transaction import Transaction
from app.models.transaction_item import TransactionItem
from app.schemas.product import ProductSlim
from app.schemas.shopping_list import (
    ShoppingListCreate,
    ShoppingListItemCreate,
    ShoppingListItemPublic,
    ShoppingListItemUpdate,
    ShoppingListPublic,
    ShoppingListUpdate,
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


async def _build_item_public(
    db: AsyncSession, row: ShoppingListItem
) -> ShoppingListItemPublic:
    product = await _get_product_slim(db, row.product_id)
    return ShoppingListItemPublic(
        id=row.id,
        shopping_list_id=row.list_id,
        product_id=row.product_id,
        product=product,
        raw_name=row.raw_name,
        quantity=row.quantity,
        unit=row.unit,
        estimated_price=row.estimated_price,
        actual_price=row.actual_price,
        is_checked=row.is_checked,
        source=row.source,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _build_list_public(db: AsyncSession, row: ShoppingList) -> ShoppingListPublic:
    items_result = await db.execute(
        select(ShoppingListItem).where(
            ShoppingListItem.list_id == row.id,
            ShoppingListItem.owner_id == row.owner_id,
        )
    )
    item_rows = items_result.scalars().all()
    items = [await _build_item_public(db, i) for i in item_rows]

    item_count = len(items)
    checked_count = sum(1 for i in items if i.is_checked)

    # estimated_total: sum of estimated_price * quantity for unchecked items only
    unchecked = [i for i in items if not i.is_checked]
    if any(i.estimated_price is not None for i in unchecked):
        estimated_total = round(
            sum((i.estimated_price or 0.0) * i.quantity for i in unchecked), 2
        )
    else:
        estimated_total = None

    return ShoppingListPublic(
        id=row.id,
        owner_id=row.owner_id,
        name=row.name,
        store_name=row.store_name,
        planned_date=row.planned_date,
        is_completed=row.is_completed,
        completed_on=row.completed_on,
        is_active=row.is_active,
        notes=row.notes,
        items=items,
        item_count=item_count,
        checked_count=checked_count,
        estimated_total=estimated_total,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _get_list_row(
    db: AsyncSession, list_id: uuid.UUID, owner_id: uuid.UUID
) -> ShoppingList | None:
    result = await db.execute(
        select(ShoppingList).where(
            ShoppingList.id == list_id,
            ShoppingList.owner_id == owner_id,
            ShoppingList.deleted_at.is_(None),
        )
    )
    return result.scalars().first()


async def get_or_create_default_list(
    db: AsyncSession, owner_id: uuid.UUID
) -> ShoppingList:
    """Return the active 'Auto Shopping List', creating one if none exists."""
    result = await db.execute(
        select(ShoppingList).where(
            ShoppingList.owner_id == owner_id,
            ShoppingList.name == "Auto Shopping List",
            ShoppingList.is_active.is_(True),
            ShoppingList.deleted_at.is_(None),
        )
    )
    shopping_list = result.scalars().first()
    if not shopping_list:
        shopping_list = ShoppingList(
            owner_id=owner_id,
            name="Auto Shopping List",
        )
        db.add(shopping_list)
        await db.flush()
    return shopping_list


async def create_shopping_list(
    db: AsyncSession, owner_id: uuid.UUID, data: ShoppingListCreate
) -> ShoppingListPublic:
    row = ShoppingList(
        owner_id=owner_id,
        name=data.name,
        store_name=data.store_name,
        planned_date=data.planned_date,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_list_public(db, row)


async def list_shopping_lists(
    db: AsyncSession,
    owner_id: uuid.UUID,
    include_completed: bool = False,
) -> list[ShoppingListPublic]:
    query = select(ShoppingList).where(
        ShoppingList.owner_id == owner_id,
        ShoppingList.deleted_at.is_(None),
    )
    if not include_completed:
        query = query.where(ShoppingList.is_completed.is_(False))
    result = await db.execute(query.order_by(ShoppingList.created_at.desc()))
    rows = result.scalars().all()
    return [await _build_list_public(db, row) for row in rows]


async def get_shopping_list(
    db: AsyncSession, list_id: uuid.UUID, owner_id: uuid.UUID
) -> ShoppingListPublic | None:
    row = await _get_list_row(db, list_id, owner_id)
    if not row:
        return None
    return await _build_list_public(db, row)


async def update_shopping_list(
    db: AsyncSession,
    list_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: ShoppingListUpdate,
) -> ShoppingListPublic | None:
    row = await _get_list_row(db, list_id, owner_id)
    if not row:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    row.updated_at = _naive_utc_now()
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_list_public(db, row)


async def delete_shopping_list(
    db: AsyncSession, list_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    row = await _get_list_row(db, list_id, owner_id)
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True


async def add_item(
    db: AsyncSession,
    owner_id: uuid.UUID,
    list_id: uuid.UUID,
    data: ShoppingListItemCreate,
) -> ShoppingListItemPublic | None:
    list_row = await _get_list_row(db, list_id, owner_id)
    if not list_row:
        return None

    # Auto-fill raw_name from product if product_id is provided
    raw_name = data.raw_name
    if data.product_id is not None:
        product_result = await db.execute(
            select(Product).where(
                Product.id == data.product_id,
                Product.owner_id == owner_id,
                Product.deleted_at.is_(None),
            )
        )
        product = product_result.scalars().first()
        if product:
            raw_name = product.name

    # Auto-fill estimated_price from most recent purchase if not provided
    estimated_price = data.estimated_price
    if estimated_price is None and data.product_id is not None:
        price_result = await db.execute(
            select(TransactionItem)
            .where(
                TransactionItem.owner_id == owner_id,
                TransactionItem.product_id == data.product_id,
            )
            .order_by(TransactionItem.created_at.desc())
            .limit(1)
        )
        last = price_result.scalars().first()
        if last:
            estimated_price = last.unit_price

    item = ShoppingListItem(
        owner_id=owner_id,
        list_id=list_id,
        product_id=data.product_id,
        raw_name=raw_name,
        quantity=data.quantity,
        unit=data.unit,
        estimated_price=estimated_price,
        source="manual",
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return await _build_item_public(db, item)


async def update_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: ShoppingListItemUpdate,
) -> ShoppingListItemPublic | None:
    result = await db.execute(
        select(ShoppingListItem).where(
            ShoppingListItem.id == item_id,
            ShoppingListItem.owner_id == owner_id,
        )
    )
    row = result.scalars().first()
    if not row:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    row.updated_at = _naive_utc_now()
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_item_public(db, row)


async def delete_item(
    db: AsyncSession, item_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    result = await db.execute(
        select(ShoppingListItem).where(
            ShoppingListItem.id == item_id,
            ShoppingListItem.owner_id == owner_id,
        )
    )
    row = result.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True


async def complete_list(
    db: AsyncSession,
    list_id: uuid.UUID,
    owner_id: uuid.UUID,
    create_transaction: bool = False,
) -> ShoppingListPublic | None:
    row = await _get_list_row(db, list_id, owner_id)
    if not row:
        return None

    row.is_completed = True
    row.completed_on = date.today()
    row.is_active = False
    row.updated_at = _naive_utc_now()
    db.add(row)

    if create_transaction:
        items_result = await db.execute(
            select(ShoppingListItem).where(
                ShoppingListItem.list_id == list_id,
                ShoppingListItem.owner_id == owner_id,
                ShoppingListItem.is_checked.is_(True),
            )
        )
        checked_items = items_result.scalars().all()

        # Only items with actual_price contribute to the transaction total
        billable = [i for i in checked_items if i.actual_price is not None]
        if billable:
            total = round(sum(i.actual_price * i.quantity for i in billable), 2)
            tx = Transaction(
                owner_id=owner_id,
                transaction_type="expense",
                amount=total,
                currency="INR",
                transacted_on=date.today(),
                description=row.name,
                merchant=row.store_name,
            )
            db.add(tx)
            await db.flush()

            for item in billable:
                tx_item = TransactionItem(
                    owner_id=owner_id,
                    transaction_id=tx.id,
                    product_id=item.product_id,
                    raw_name=item.raw_name,
                    quantity=item.quantity,
                    unit=item.unit,
                    unit_price=item.actual_price,
                    total_price=round(item.actual_price * item.quantity, 2),
                    store_name=row.store_name,
                )
                db.add(tx_item)
                await db.flush()

                if item.product_id is not None:
                    from app.crud.inventory import update_inventory_on_purchase

                    await update_inventory_on_purchase(
                        db, owner_id, item.product_id, item.quantity, date.today()
                    )

    await db.commit()
    await db.refresh(row)
    return await _build_list_public(db, row)
