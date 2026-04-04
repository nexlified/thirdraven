import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.vocabulary import resolve_optional_term_slug
from app.models.product import Product
from app.models.vocabulary import Term
from app.schemas.product import ProductCreate, ProductPublic, ProductSlim, ProductUpdate
from app.schemas.vocabulary import TermSlim


async def _get_term(db: AsyncSession, term_id: uuid.UUID | None) -> TermSlim | None:
    if term_id is None:
        return None
    result = await db.execute(select(Term).where(Term.id == term_id))
    t = result.scalars().first()
    return TermSlim.model_validate(t) if t else None


async def _build_product_public(db: AsyncSession, row: Product) -> ProductPublic:
    category = await _get_term(db, row.category_term_id)
    return ProductPublic(
        id=row.id,
        owner_id=row.owner_id,
        name=row.name,
        brand=row.brand,
        category=category,
        unit=row.unit,
        barcode=row.barcode,
        priceraven_product_id=row.priceraven_product_id,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def create_product(
    db: AsyncSession, owner_id: uuid.UUID, data: ProductCreate
) -> tuple[ProductPublic, bool]:
    """Create a product or return the existing one if name+brand match.

    Returns (product, is_new) where is_new=False signals an idempotent duplicate.
    """
    stmt = select(Product).where(
        Product.owner_id == owner_id,
        Product.deleted_at.is_(None),
        func.lower(Product.name) == func.lower(data.name),
    )
    if data.brand is not None:
        stmt = stmt.where(func.lower(Product.brand) == func.lower(data.brand))
    else:
        stmt = stmt.where(Product.brand.is_(None))

    result = await db.execute(stmt)
    existing = result.scalars().first()
    if existing:
        return await _build_product_public(db, existing), False

    raw = data.model_dump(exclude_unset=True)
    category_slug = raw.pop("category", None)
    category_term_id = await resolve_optional_term_slug(
        db, "product-categories", category_slug
    )

    row = Product(
        owner_id=owner_id,
        category_term_id=category_term_id,
        **raw,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_product_public(db, row), True


async def list_products(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    *,
    category_slug: str | None = None,
    search: str | None = None,
) -> tuple[list[ProductPublic], int]:
    query = select(Product).where(
        Product.owner_id == owner_id,
        Product.deleted_at.is_(None),
    )

    if category_slug is not None:
        cat_id = await resolve_optional_term_slug(
            db, "product-categories", category_slug
        )
        if cat_id is None:
            return [], 0
        query = query.where(Product.category_term_id == cat_id)

    if search is not None:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Product.name.ilike(pattern),
                Product.brand.ilike(pattern),
            )
        )

    total = (
        await db.execute(select(func.count()).select_from(query.subquery()))
    ).scalar_one()

    result = await db.execute(
        query.order_by(Product.name.asc()).offset(skip).limit(limit)
    )
    return [
        await _build_product_public(db, row) for row in result.scalars().all()
    ], total


async def get_product(
    db: AsyncSession, product_id: uuid.UUID, owner_id: uuid.UUID
) -> Product | None:
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.owner_id == owner_id,
            Product.deleted_at.is_(None),
        )
    )
    return result.scalars().first()


async def get_product_public(
    db: AsyncSession, product_id: uuid.UUID, owner_id: uuid.UUID
) -> ProductPublic | None:
    row = await get_product(db, product_id, owner_id)
    if not row:
        return None
    return await _build_product_public(db, row)


async def update_product(
    db: AsyncSession,
    product_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: ProductUpdate,
) -> ProductPublic | None:
    row = await get_product(db, product_id, owner_id)
    if not row:
        return None

    raw = data.model_dump(exclude_unset=True)
    category_slug = raw.pop("category", None)
    if category_slug is not None:
        row.category_term_id = await resolve_optional_term_slug(
            db, "product-categories", category_slug
        )

    for field, value in raw.items():
        setattr(row, field, value)

    row.updated_at = datetime.now(UTC).replace(tzinfo=None)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_product_public(db, row)


async def soft_delete_product(
    db: AsyncSession, product_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    row = await get_product(db, product_id, owner_id)
    if not row:
        return False

    # Guard: check for active InventoryProfile or TransactionItem references.
    # These models will be wired in when they are introduced in future issues.

    row.deleted_at = datetime.now(UTC).replace(tzinfo=None)
    db.add(row)
    await db.commit()
    return True


async def get_product_slim(
    db: AsyncSession, product_id: uuid.UUID, owner_id: uuid.UUID
) -> ProductSlim | None:
    row = await get_product(db, product_id, owner_id)
    if not row:
        return None
    return ProductSlim(
        id=row.id,
        name=row.name,
        brand=row.brand,
        unit=row.unit,
    )
