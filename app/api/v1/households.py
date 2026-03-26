import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.household import (
    create_household,
    get_my_household,
    invite_member,
    leave_household,
    remove_member,
)
from app.models.user import User
from app.schemas.household import HouseholdCreate, HouseholdInvite, HouseholdPublic

router = APIRouter(prefix="/households", tags=["households"])


@router.post("/", response_model=HouseholdPublic, status_code=status.HTTP_201_CREATED)
async def create(
    data: HouseholdCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_household(db, current_user.id, data)


@router.get("/me", response_model=HouseholdPublic)
async def get_mine(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    household = await get_my_household(db, current_user.id)
    if not household:
        raise HTTPException(status_code=404, detail="Not in a household.")
    return household


@router.post("/{household_id}/members", response_model=HouseholdPublic)
async def invite(
    household_id: uuid.UUID,
    data: HouseholdInvite,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await invite_member(db, household_id, current_user.id, data.username)


@router.delete(
    "/{household_id}/members/{user_id}", response_model=HouseholdPublic
)
async def kick_member(
    household_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await remove_member(db, household_id, current_user.id, user_id)


@router.delete("/me/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await leave_household(db, current_user.id)
