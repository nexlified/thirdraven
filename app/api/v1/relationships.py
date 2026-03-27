import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.person_relationship import (
    delete_relationship,
    get_relationship,
    update_relationship,
)
from app.models.user import User
from app.schemas.person import RelationshipPublic, RelationshipUpdate

router = APIRouter(prefix="/relationships", tags=["relationships"])


@router.get("/{rel_id}", response_model=RelationshipPublic)
async def get_one(
    rel_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    rel = await get_relationship(db, rel_id, current_user.id)
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return rel


@router.patch("/{rel_id}", response_model=RelationshipPublic)
async def patch(
    rel_id: uuid.UUID,
    data: RelationshipUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    rel = await update_relationship(db, rel_id, current_user.id, data)
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return rel


@router.delete("/{rel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    rel_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await delete_relationship(db, rel_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Relationship not found")
