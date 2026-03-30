import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.asset_event import AssetEvent
from app.schemas.asset_event import AssetEventCreate, AssetEventPublic


async def create_asset_event(
    db: AsyncSession,
    asset_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: AssetEventCreate,
) -> AssetEventPublic:
    row = AssetEvent(
        asset_id=asset_id,
        owner_id=owner_id,
        event_type=data.event_type,
        occurred_on=data.occurred_on,
        description=data.description,
        cost=data.cost,
        currency=data.currency,
        vendor=data.vendor,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return AssetEventPublic.model_validate(row)


async def list_asset_events(
    db: AsyncSession, asset_id: uuid.UUID, owner_id: uuid.UUID
) -> list[AssetEventPublic]:
    r = await db.execute(
        select(AssetEvent)
        .where(AssetEvent.asset_id == asset_id, AssetEvent.owner_id == owner_id)
        .order_by(AssetEvent.occurred_on.desc().nulls_last())
    )
    return [AssetEventPublic.model_validate(row) for row in r.scalars().all()]


async def delete_asset_event(
    db: AsyncSession,
    event_id: uuid.UUID,
    asset_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> bool:
    r = await db.execute(
        select(AssetEvent).where(
            AssetEvent.id == event_id,
            AssetEvent.asset_id == asset_id,
            AssetEvent.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True
