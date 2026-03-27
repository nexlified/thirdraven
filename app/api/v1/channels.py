import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.person import (
    create_channel,
    delete_channel,
    get_person,
    update_channel,
)
from app.models.user import User
from app.schemas.person import ChannelCreate, ChannelPublic, ChannelUpdate

router = APIRouter(
    prefix="/persons/{person_id}/channels", tags=["channels"]
)


@router.post("/", response_model=ChannelPublic, status_code=status.HTTP_201_CREATED)
async def add_channel(
    person_id: uuid.UUID,
    data: ChannelCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return await create_channel(db, person_id, current_user.id, data)


@router.patch("/{channel_id}", response_model=ChannelPublic, status_code=status.HTTP_200_OK)
async def edit_channel(
    person_id: uuid.UUID,
    channel_id: uuid.UUID,
    data: ChannelUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await update_channel(db, channel_id, person_id, current_user.id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Channel not found")
    return result


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_channel(
    person_id: uuid.UUID,
    channel_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await delete_channel(db, channel_id, person_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Channel not found")
