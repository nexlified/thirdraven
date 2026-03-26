import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.tracked_record import (
    create_record,
    delete_record,
    get_record,
    list_records,
    update_record,
)
from app.models.user import User
from app.schemas.tracked_record import RecordCreate, RecordPublic, RecordUpdate

router = APIRouter(prefix="/records", tags=["records"])


@router.post("/", response_model=RecordPublic, status_code=status.HTTP_201_CREATED)
async def create(
    data: RecordCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_record(db, current_user.id, data)


@router.get("/", response_model=list[RecordPublic])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 50,
    record_type: str | None = None,
    asset_id: uuid.UUID | None = None,
    person_id: uuid.UUID | None = None,
    expires_before: date | None = None,
):
    return await list_records(
        db,
        current_user.id,
        skip=skip,
        limit=limit,
        record_type_slug=record_type,
        asset_id=asset_id,
        person_id=person_id,
        expires_before=expires_before,
    )


@router.get("/{record_id}", response_model=RecordPublic)
async def get_one(
    record_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    record = await get_record(db, record_id, current_user.id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.patch("/{record_id}", response_model=RecordPublic)
async def patch(
    record_id: uuid.UUID,
    data: RecordUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    record = await update_record(db, record_id, current_user.id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    record_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await delete_record(db, record_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Record not found")
