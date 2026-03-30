import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.crud.asset import (
    create_asset,
    get_asset_public,
    list_assets,
    soft_delete_asset,
    update_asset,
)
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetPublicRead, AssetUpdate
from app.schemas.paginated import Paginated

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("/", response_model=AssetPublicRead, status_code=status.HTTP_201_CREATED)
async def create(
    data: AssetCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_asset(db, current_user.id, data)


@router.get("/", response_model=Paginated[AssetPublicRead])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
    category: str | None = None,
    status: str | None = None,
):
    items, total = await list_assets(
        db, current_user.id, skip=pagination.skip, limit=pagination.limit, category=category, status=status
    )
    return Paginated(items=items, total=total, skip=pagination.skip, limit=pagination.limit)


@router.get("/{asset_id}", response_model=AssetPublicRead)
async def get_one(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    include: str = "",
):
    include_list = [s.strip() for s in include.split(",") if s.strip()] or None
    asset = await get_asset_public(db, asset_id, current_user.id, include=include_list)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.patch("/{asset_id}", response_model=AssetPublicRead)
async def patch(
    asset_id: uuid.UUID,
    data: AssetUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    asset = await update_asset(db, asset_id, current_user.id, data)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    asset = await soft_delete_asset(db, asset_id, current_user.id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
