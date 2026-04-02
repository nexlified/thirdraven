import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.crud.note import (
    create_note,
    get_note_public,
    get_note_statistics,
    list_notes,
    soft_delete_note,
    update_note,
)
from app.models.user import User
from app.schemas.note import NoteCreate, NotePublicRead, NoteStatistics, NoteUpdate
from app.schemas.paginated import Paginated

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=NotePublicRead, status_code=status.HTTP_201_CREATED)
async def create(
    data: NoteCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_note(db, current_user.id, data)


@router.get("/", response_model=Paginated[NotePublicRead])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
    q: str | None = None,
    pinned: bool | None = None,
    person_id: uuid.UUID | None = None,
    asset_id: uuid.UUID | None = None,
    subscription_id: uuid.UUID | None = None,
    event_id: uuid.UUID | None = None,
):
    items, total = await list_notes(
        db,
        current_user.id,
        skip=pagination.skip,
        limit=pagination.limit,
        q=q,
        pinned=pinned,
        person_id=person_id,
        asset_id=asset_id,
        subscription_id=subscription_id,
        event_id=event_id,
    )
    return Paginated(
        items=items, total=total, skip=pagination.skip, limit=pagination.limit
    )


@router.get("/statistics", response_model=NoteStatistics)
async def statistics(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await get_note_statistics(db, current_user.id)


@router.get("/{note_id}", response_model=NotePublicRead)
async def get_one(
    note_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    note = await get_note_public(db, note_id, current_user.id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.patch("/{note_id}", response_model=NotePublicRead)
async def patch(
    note_id: uuid.UUID,
    data: NoteUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    note = await update_note(db, note_id, current_user.id, data)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    note_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    note = await soft_delete_note(db, note_id, current_user.id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
