import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.asset import get_asset
from app.crud.asset_event import (
    create_asset_event,
    delete_asset_event,
    list_asset_events,
)
from app.crud.asset_extensions import (
    delete_digital_asset,
    delete_document_asset,
    delete_financial_asset,
    delete_physical_asset,
    get_digital_asset,
    get_document_asset,
    get_financial_asset,
    get_physical_asset,
    upsert_digital_asset,
    upsert_document_asset,
    upsert_financial_asset,
    upsert_physical_asset,
)
from app.models.user import User
from app.schemas.asset_event import AssetEventCreate, AssetEventPublic
from app.schemas.asset_extensions import (
    DigitalAssetCreate,
    DigitalAssetPublic,
    DocumentAssetCreate,
    DocumentAssetPublic,
    FinancialAssetCreate,
    FinancialAssetPublic,
    PhysicalAssetCreate,
    PhysicalAssetPublic,
)

router = APIRouter(prefix="/assets/{asset_id}", tags=["asset-extensions"])


async def _verify_asset(
    db: AsyncSession, asset_id: uuid.UUID, owner_id: uuid.UUID
) -> None:
    asset = await get_asset(db, asset_id, owner_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")


# ── Physical ─────────────────────────────────────────────────────────────────


@router.get("/physical/", response_model=PhysicalAssetPublic)
async def get_physical(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _verify_asset(db, asset_id, current_user.id)
    ext = await get_physical_asset(db, asset_id)
    if not ext:
        raise HTTPException(status_code=404, detail="Physical extension not found")
    return ext


@router.post(
    "/physical/",
    response_model=PhysicalAssetPublic,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_physical(
    asset_id: uuid.UUID,
    data: PhysicalAssetCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _verify_asset(db, asset_id, current_user.id)
    return await upsert_physical_asset(db, asset_id, data)


@router.delete("/physical/", status_code=status.HTTP_204_NO_CONTENT)
async def remove_physical(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _verify_asset(db, asset_id, current_user.id)
    if not await delete_physical_asset(db, asset_id):
        raise HTTPException(status_code=404, detail="Physical extension not found")


# ── Document ─────────────────────────────────────────────────────────────────


@router.get("/document/", response_model=DocumentAssetPublic)
async def get_document(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _verify_asset(db, asset_id, current_user.id)
    ext = await get_document_asset(db, asset_id)
    if not ext:
        raise HTTPException(status_code=404, detail="Document extension not found")
    return ext


@router.post(
    "/document/",
    response_model=DocumentAssetPublic,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_document(
    asset_id: uuid.UUID,
    data: DocumentAssetCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _verify_asset(db, asset_id, current_user.id)
    return await upsert_document_asset(db, asset_id, data)


@router.delete("/document/", status_code=status.HTTP_204_NO_CONTENT)
async def remove_document(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _verify_asset(db, asset_id, current_user.id)
    if not await delete_document_asset(db, asset_id):
        raise HTTPException(status_code=404, detail="Document extension not found")


# ── Financial ────────────────────────────────────────────────────────────────


@router.get("/financial/", response_model=FinancialAssetPublic)
async def get_financial(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _verify_asset(db, asset_id, current_user.id)
    ext = await get_financial_asset(db, asset_id)
    if not ext:
        raise HTTPException(status_code=404, detail="Financial extension not found")
    return ext


@router.post(
    "/financial/",
    response_model=FinancialAssetPublic,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_financial(
    asset_id: uuid.UUID,
    data: FinancialAssetCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _verify_asset(db, asset_id, current_user.id)
    return await upsert_financial_asset(db, asset_id, data)


@router.delete("/financial/", status_code=status.HTTP_204_NO_CONTENT)
async def remove_financial(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _verify_asset(db, asset_id, current_user.id)
    if not await delete_financial_asset(db, asset_id):
        raise HTTPException(status_code=404, detail="Financial extension not found")


# ── Digital ──────────────────────────────────────────────────────────────────


@router.get("/digital/", response_model=DigitalAssetPublic)
async def get_digital(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _verify_asset(db, asset_id, current_user.id)
    ext = await get_digital_asset(db, asset_id)
    if not ext:
        raise HTTPException(status_code=404, detail="Digital extension not found")
    return ext


@router.post(
    "/digital/", response_model=DigitalAssetPublic, status_code=status.HTTP_201_CREATED
)
async def upsert_digital(
    asset_id: uuid.UUID,
    data: DigitalAssetCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _verify_asset(db, asset_id, current_user.id)
    return await upsert_digital_asset(db, asset_id, data)


@router.delete("/digital/", status_code=status.HTTP_204_NO_CONTENT)
async def remove_digital(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _verify_asset(db, asset_id, current_user.id)
    if not await delete_digital_asset(db, asset_id):
        raise HTTPException(status_code=404, detail="Digital extension not found")


# ── Asset Lifecycle Events ───────────────────────────────────────────────────


@router.get("/events/", response_model=list[AssetEventPublic])
async def list_events(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _verify_asset(db, asset_id, current_user.id)
    return await list_asset_events(db, asset_id, current_user.id)


@router.post(
    "/events/", response_model=AssetEventPublic, status_code=status.HTTP_201_CREATED
)
async def create_event(
    asset_id: uuid.UUID,
    data: AssetEventCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _verify_asset(db, asset_id, current_user.id)
    return await create_asset_event(db, asset_id, current_user.id, data)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_event(
    asset_id: uuid.UUID,
    event_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _verify_asset(db, asset_id, current_user.id)
    if not await delete_asset_event(db, event_id, asset_id, current_user.id):
        raise HTTPException(status_code=404, detail="Asset event not found")
