import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.asset import (
    create_asset,
    get_asset_public,
    list_assets,
    soft_delete_asset,
    update_asset,
)
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetPublicRead, AssetUpdate

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("/", response_model=AssetPublicRead, status_code=status.HTTP_201_CREATED)
async def create(
    data: AssetCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_asset(db, current_user.id, data)


@router.get("/", response_model=list[AssetPublicRead])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 50,
    category: str | None = None,
    status: str | None = None,
):
    return await list_assets(
        db, current_user.id, skip=skip, limit=limit, category=category, status=status
    )


@router.get("/{asset_id}", response_model=AssetPublicRead)
async def get_one(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    asset = await get_asset_public(db, asset_id, current_user.id)
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
