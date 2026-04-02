import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.person import (
    create_address,
    delete_address,
    get_person,
    update_address,
)
from app.models.user import User
from app.schemas.person import AddressCreate, AddressPublic

router = APIRouter(prefix="/persons/{person_id}/addresses", tags=["addresses"])


@router.post("/", response_model=AddressPublic, status_code=status.HTTP_201_CREATED)
async def add_address(
    person_id: uuid.UUID,
    data: AddressCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return await create_address(db, person_id, current_user.id, data)


@router.patch(
    "/{address_id}", response_model=AddressPublic, status_code=status.HTTP_200_OK
)
async def edit_address(
    person_id: uuid.UUID,
    address_id: uuid.UUID,
    data: AddressCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await update_address(db, address_id, person_id, current_user.id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Address not found")
    return result


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_address(
    person_id: uuid.UUID,
    address_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await delete_address(db, address_id, person_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Address not found")
