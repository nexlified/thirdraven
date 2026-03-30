import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.crud.reminder import (
    create_reminder,
    get_reminder,
    list_reminders,
    soft_delete_reminder,
    update_reminder,
)
from app.models.user import User
from app.schemas.paginated import Paginated
from app.schemas.reminder import ReminderCreate, ReminderPublic, ReminderUpdate

router = APIRouter(prefix="/reminders", tags=["reminders"])
person_reminders_router = APIRouter(
    prefix="/persons/{person_id}/reminders", tags=["reminders"]
)
asset_reminders_router = APIRouter(
    prefix="/assets/{asset_id}/reminders", tags=["reminders"]
)
subscription_reminders_router = APIRouter(
    prefix="/subscriptions/{sub_id}/reminders", tags=["reminders"]
)


@router.post("/", response_model=ReminderPublic, status_code=status.HTTP_201_CREATED)
async def create(
    data: ReminderCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_reminder(db, current_user.id, data)


@router.get("/", response_model=Paginated[ReminderPublic])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
    is_done: bool | None = None,
):
    items, total = await list_reminders(
        db, current_user.id, skip=pagination.skip, limit=pagination.limit, is_done=is_done
    )
    return Paginated(items=items, total=total, skip=pagination.skip, limit=pagination.limit)


@router.get("/{reminder_id}", response_model=ReminderPublic)
async def get_one(
    reminder_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    reminder = await get_reminder(db, reminder_id, current_user.id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder


@router.patch("/{reminder_id}", response_model=ReminderPublic)
async def patch(
    reminder_id: uuid.UUID,
    data: ReminderUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    reminder = await update_reminder(db, reminder_id, current_user.id, data)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    reminder_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await soft_delete_reminder(db, reminder_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Reminder not found")


# ── Entity-scoped reminders ──────────────────────────────────────────────────


@person_reminders_router.get("/", response_model=Paginated[ReminderPublic])
async def list_person_reminders(
    person_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
):
    items, total = await list_reminders(
        db, current_user.id, skip=pagination.skip, limit=pagination.limit, person_id=person_id
    )
    return Paginated(items=items, total=total, skip=pagination.skip, limit=pagination.limit)


@asset_reminders_router.get("/", response_model=Paginated[ReminderPublic])
async def list_asset_reminders(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
):
    items, total = await list_reminders(
        db, current_user.id, skip=pagination.skip, limit=pagination.limit, asset_id=asset_id
    )
    return Paginated(items=items, total=total, skip=pagination.skip, limit=pagination.limit)


@subscription_reminders_router.get("/", response_model=Paginated[ReminderPublic])
async def list_subscription_reminders(
    sub_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
):
    items, total = await list_reminders(
        db, current_user.id, skip=pagination.skip, limit=pagination.limit, subscription_id=sub_id
    )
    return Paginated(items=items, total=total, skip=pagination.skip, limit=pagination.limit)
