import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.vocabulary import resolve_term_slug
from app.models.asset import Asset
from app.models.vocabulary import AssetTag, Term
from app.schemas.asset import AssetCreate, AssetPublicRead, AssetUpdate
from app.schemas.vocabulary import TermSlim

# ── Tag helpers ────────────────────────────────────────────────────────────────


async def _get_asset_tags(db: AsyncSession, asset_id: uuid.UUID) -> list[TermSlim]:
    result = await db.exec(
        select(Term)
        .join(AssetTag, Term.id == AssetTag.term_id)
        .where(AssetTag.asset_id == asset_id, Term.is_active.is_(True))
        .order_by(Term.name)
    )
    return [TermSlim.model_validate(t) for t in result.all()]


async def _set_asset_tags(
    db: AsyncSession, asset_id: uuid.UUID, tag_slugs: list[str]
) -> None:
    existing = await db.exec(select(AssetTag).where(AssetTag.asset_id == asset_id))
    for row in existing.all():
        await db.delete(row)
    for slug in tag_slugs:
        term_id = await resolve_term_slug(db, "asset-tags", slug)
        db.add(AssetTag(asset_id=asset_id, term_id=term_id))


async def _get_term(db: AsyncSession, term_id: uuid.UUID) -> TermSlim | None:
    result = await db.exec(select(Term).where(Term.id == term_id))
    t = result.first()
    return TermSlim.model_validate(t) if t else None


async def _build_asset_public(db: AsyncSession, asset: Asset) -> AssetPublicRead:
    category = await _get_term(db, asset.category_term_id)
    status = await _get_term(db, asset.status_term_id)
    tags = await _get_asset_tags(db, asset.id)
    return AssetPublicRead(
        id=asset.id,
        owner_id=asset.owner_id,
        name=asset.name,
        category=category,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        description=asset.description,
        serial_number=asset.serial_number,
        vendor=asset.vendor,
        purchase_date=asset.purchase_date,
        purchase_price=asset.purchase_price,
        current_value=asset.current_value,
        tags=tags,
        notes=asset.notes,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


# ── CRUD ───────────────────────────────────────────────────────────────────────


async def create_asset(
    db: AsyncSession, owner_id: uuid.UUID, data: AssetCreate
) -> AssetPublicRead:
    raw = data.model_dump(exclude_unset=True)
    tags_slugs = raw.pop("tags", [])
    category_slug = raw.pop("category")
    status_slug = raw.pop("status", "active")

    category_term_id = await resolve_term_slug(db, "asset-categories", category_slug)
    status_term_id = await resolve_term_slug(db, "asset-statuses", status_slug)

    asset = Asset(
        owner_id=owner_id,
        category_term_id=category_term_id,
        status_term_id=status_term_id,
        **raw,
    )
    db.add(asset)
    await db.flush()

    for slug in tags_slugs:
        term_id = await resolve_term_slug(db, "asset-tags", slug)
        db.add(AssetTag(asset_id=asset.id, term_id=term_id))

    await db.commit()
    await db.refresh(asset)
    return await _build_asset_public(db, asset)


async def get_asset(
    db: AsyncSession, asset_id: uuid.UUID, owner_id: uuid.UUID
) -> Asset | None:
    result = await db.exec(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.owner_id == owner_id,
            Asset.deleted_at.is_(None),
        )
    )
    return result.first()


async def get_asset_public(
    db: AsyncSession, asset_id: uuid.UUID, owner_id: uuid.UUID
) -> AssetPublicRead | None:
    asset = await get_asset(db, asset_id, owner_id)
    if not asset:
        return None
    return await _build_asset_public(db, asset)


async def list_assets(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    category: str | None = None,
    status: str | None = None,
) -> list[AssetPublicRead]:
    query = select(Asset).where(Asset.owner_id == owner_id, Asset.deleted_at.is_(None))

    if category is not None:
        cat_id = await resolve_term_slug(db, "asset-categories", category)
        query = query.where(Asset.category_term_id == cat_id)

    if status is not None:
        stat_id = await resolve_term_slug(db, "asset-statuses", status)
        query = query.where(Asset.status_term_id == stat_id)

    result = await db.exec(query.offset(skip).limit(limit))
    assets = result.all()
    return [await _build_asset_public(db, a) for a in assets]


async def update_asset(
    db: AsyncSession,
    asset_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: AssetUpdate,
) -> AssetPublicRead | None:
    asset = await get_asset(db, asset_id, owner_id)
    if not asset:
        return None

    raw = data.model_dump(exclude_unset=True)
    tags_slugs = raw.pop("tags", None)

    if "category" in raw:
        asset.category_term_id = await resolve_term_slug(
            db, "asset-categories", raw.pop("category")
        )
    if "status" in raw:
        asset.status_term_id = await resolve_term_slug(
            db, "asset-statuses", raw.pop("status")
        )

    for field, value in raw.items():
        setattr(asset, field, value)
    asset.updated_at = datetime.utcnow()
    db.add(asset)

    if tags_slugs is not None:
        await _set_asset_tags(db, asset_id, tags_slugs)

    await db.commit()
    await db.refresh(asset)
    return await _build_asset_public(db, asset)


async def soft_delete_asset(
    db: AsyncSession, asset_id: uuid.UUID, owner_id: uuid.UUID
) -> Asset | None:
    asset = await get_asset(db, asset_id, owner_id)
    if not asset:
        return None
    asset.deleted_at = datetime.utcnow()
    db.add(asset)
    await db.commit()
    return asset
