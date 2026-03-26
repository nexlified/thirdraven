import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.followup import (
    create_followup,
    delete_followup,
    get_followup,
    list_followups,
    update_followup,
)
from app.crud.person import get_person
from app.models.user import User
from app.schemas.followup import FollowUpCreate, FollowUpPublic, FollowUpUpdate

router = APIRouter(
    prefix="/persons/{person_id}/follow-ups", tags=["follow-ups"]
)


@router.post("/", response_model=FollowUpPublic, status_code=status.HTTP_201_CREATED)
async def create(
    person_id: uuid.UUID,
    data: FollowUpCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return await create_followup(db, person_id, current_user.id, data)


@router.get("/", response_model=list[FollowUpPublic])
async def list_all(
    person_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 50,
    pending_only: bool = False,
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return await list_followups(
        db, person_id, current_user.id,
        pending_only=pending_only, skip=skip, limit=limit,
    )


@router.get("/{followup_id}", response_model=FollowUpPublic)
async def get_one(
    person_id: uuid.UUID,
    followup_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    followup = await get_followup(db, followup_id, current_user.id)
    if not followup or followup.person_id != person_id:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    return followup


@router.patch("/{followup_id}", response_model=FollowUpPublic)
async def patch(
    person_id: uuid.UUID,
    followup_id: uuid.UUID,
    data: FollowUpUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    followup = await update_followup(db, followup_id, current_user.id, data)
    if not followup or followup.person_id != person_id:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    return followup


@router.delete("/{followup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    person_id: uuid.UUID,
    followup_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    deleted = await delete_followup(db, followup_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Follow-up not found")
