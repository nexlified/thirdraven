import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.inventory import InventoryProfile
from app.models.product import Product
from app.models.reminder import Reminder
from app.models.shopping_list import ShoppingList, ShoppingListItem
from app.models.transaction_item import TransactionItem
from app.schemas.inventory import (
    InventoryProfileCreate,
    InventoryProfilePublic,
    InventoryProfileUpdate,
)
from app.schemas.product import ProductSlim


def _naive_utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _compute_depletion_date(profile: InventoryProfile) -> date | None:
    if profile.typical_monthly_usage <= 0 or profile.current_stock <= 0:
        return None
    days_remaining = profile.current_stock / (profile.typical_monthly_usage / 30)
    return date.today() + timedelta(days=int(days_remaining))


async def _build_public(
    db: AsyncSession, row: InventoryProfile
) -> InventoryProfilePublic:
    result = await db.execute(select(Product).where(Product.id == row.product_id))
    product_row = result.scalars().first()
    product_slim = ProductSlim(
        id=product_row.id,
        name=product_row.name,
        brand=product_row.brand,
        unit=product_row.unit,
    )
    return InventoryProfilePublic(
        id=row.id,
        owner_id=row.owner_id,
        product=product_slim,
        is_consumable=row.is_consumable,
        restock_unit=row.restock_unit,
        reorder_threshold=row.reorder_threshold,
        typical_monthly_usage=row.typical_monthly_usage,
        current_stock=row.current_stock,
        last_restocked_on=row.last_restocked_on,
        estimated_depletion_date=row.estimated_depletion_date,
        preferred_source=row.preferred_source,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def create_inventory_profile(
    db: AsyncSession,
    owner_id: uuid.UUID,
    product_id: uuid.UUID,
    data: InventoryProfileCreate,
) -> InventoryProfilePublic:
    # Check product exists and belongs to owner
    product_result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.owner_id == owner_id,
            Product.deleted_at.is_(None),
        )
    )
    if not product_result.scalars().first():
        raise HTTPException(status_code=404, detail="Product not found")

    # Enforce uniqueness (one profile per product per owner)
    existing = await db.execute(
        select(InventoryProfile).where(
            InventoryProfile.owner_id == owner_id,
            InventoryProfile.product_id == product_id,
        )
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=409, detail="Inventory profile already exists for this product"
        )

    row = InventoryProfile(
        owner_id=owner_id,
        product_id=product_id,
        is_consumable=data.is_consumable,
        restock_unit=data.restock_unit,
        reorder_threshold=data.reorder_threshold,
        typical_monthly_usage=data.typical_monthly_usage,
        current_stock=data.current_stock,
        last_restocked_on=data.last_restocked_on,
        preferred_source=data.preferred_source,
        notes=data.notes,
    )
    row.estimated_depletion_date = _compute_depletion_date(row)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_public(db, row)


async def get_inventory_profile_row(
    db: AsyncSession, owner_id: uuid.UUID, product_id: uuid.UUID
) -> InventoryProfile | None:
    result = await db.execute(
        select(InventoryProfile).where(
            InventoryProfile.owner_id == owner_id,
            InventoryProfile.product_id == product_id,
        )
    )
    return result.scalars().first()


async def get_inventory_profile(
    db: AsyncSession, owner_id: uuid.UUID, product_id: uuid.UUID
) -> InventoryProfilePublic | None:
    row = await get_inventory_profile_row(db, owner_id, product_id)
    if not row:
        return None
    return await _build_public(db, row)


async def update_inventory_profile(
    db: AsyncSession,
    owner_id: uuid.UUID,
    product_id: uuid.UUID,
    data: InventoryProfileUpdate,
) -> InventoryProfilePublic | None:
    row = await get_inventory_profile_row(db, owner_id, product_id)
    if not row:
        return None

    raw = data.model_dump(exclude_unset=True)
    for field, value in raw.items():
        setattr(row, field, value)

    row.estimated_depletion_date = _compute_depletion_date(row)
    row.updated_at = _naive_utc_now()
    db.add(row)

    if "current_stock" in raw or "reorder_threshold" in raw:
        await check_and_trigger_reorder(db, owner_id, product_id, row)

    await db.commit()
    await db.refresh(row)
    return await _build_public(db, row)


async def list_low_stock(
    db: AsyncSession, owner_id: uuid.UUID
) -> list[InventoryProfilePublic]:
    result = await db.execute(
        select(InventoryProfile).where(
            InventoryProfile.owner_id == owner_id,
            InventoryProfile.current_stock <= InventoryProfile.reorder_threshold,
        )
    )
    rows = result.scalars().all()
    profiles = [await _build_public(db, row) for row in rows]
    profiles.sort(
        key=lambda p: (
            p.days_until_depletion is None,
            p.days_until_depletion if p.days_until_depletion is not None else 0,
        )
    )
    return profiles


async def update_inventory_on_purchase(
    db: AsyncSession,
    owner_id: uuid.UUID,
    product_id: uuid.UUID,
    quantity: float,
    transacted_on: date,
) -> None:
    profile = await get_inventory_profile_row(db, owner_id, product_id)
    if profile is None:
        return

    profile.current_stock += quantity
    profile.last_restocked_on = transacted_on
    profile.estimated_depletion_date = _compute_depletion_date(profile)
    profile.updated_at = _naive_utc_now()
    db.add(profile)
    # Do NOT commit here — caller's transaction handles commit
    await check_and_trigger_reorder(db, owner_id, product_id, profile)


async def check_and_trigger_reorder(
    db: AsyncSession,
    owner_id: uuid.UUID,
    product_id: uuid.UUID,
    profile: InventoryProfile,
) -> None:
    if profile.current_stock > profile.reorder_threshold:
        return

    # Fetch product name for reminder title
    product_result = await db.execute(select(Product).where(Product.id == product_id))
    product = product_result.scalars().first()
    if not product:
        return

    # 1. Create Reminder if no pending one already exists for this product
    existing_result = await db.execute(
        select(Reminder).where(
            Reminder.owner_id == owner_id,
            Reminder.product_id == product_id,
            Reminder.is_done.is_(False),
            Reminder.deleted_at.is_(None),
        )
    )
    if not existing_result.scalars().first():
        remind_dt = datetime.combine(
            date.today() + timedelta(days=1), datetime.min.time()
        ).replace(tzinfo=None)
        reminder = Reminder(
            owner_id=owner_id,
            title=f"Restock: {product.name}",
            due_at=remind_dt,
            remind_at=remind_dt,
            product_id=product_id,
        )
        db.add(reminder)

    # 2. Add ShoppingListItem to active default list
    list_result = await db.execute(
        select(ShoppingList).where(
            ShoppingList.owner_id == owner_id,
            ShoppingList.name == "Auto Shopping List",
            ShoppingList.is_active.is_(True),
            ShoppingList.deleted_at.is_(None),
        )
    )
    shopping_list = list_result.scalars().first()
    if not shopping_list:
        shopping_list = ShoppingList(
            owner_id=owner_id,
            name="Auto Shopping List",
        )
        db.add(shopping_list)
        await db.flush()  # Obtain ID before linking items

    # Check if product is already in the list unchecked
    item_result = await db.execute(
        select(ShoppingListItem).where(
            ShoppingListItem.list_id == shopping_list.id,
            ShoppingListItem.product_id == product_id,
            ShoppingListItem.is_checked.is_(False),
        )
    )
    if not item_result.scalars().first():
        # Use unit_price from the most recent TransactionItem for this product
        price_result = await db.execute(
            select(TransactionItem)
            .where(
                TransactionItem.owner_id == owner_id,
                TransactionItem.product_id == product_id,
            )
            .order_by(TransactionItem.created_at.desc())
            .limit(1)
        )
        last_item = price_result.scalars().first()
        estimated_price = last_item.unit_price if last_item else None

        item = ShoppingListItem(
            owner_id=owner_id,
            list_id=shopping_list.id,
            product_id=product_id,
            name=product.name,
            # Suggest one month's worth as the restock quantity (per spec)
            quantity=profile.typical_monthly_usage,
            unit=profile.restock_unit,
            estimated_price=estimated_price,
            source="auto",
        )
        db.add(item)
