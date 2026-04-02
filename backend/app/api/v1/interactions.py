import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.crud.interaction import (
    create_interaction,
    delete_interaction,
    get_interaction,
    list_interactions,
    update_interaction,
)
from app.crud.person import get_person
from app.models.user import User
from app.schemas.interaction import (
    InteractionCreate,
    InteractionPublicRead,
    InteractionUpdate,
)
from app.schemas.paginated import Paginated

router = APIRouter(prefix="/persons/{person_id}/interactions", tags=["interactions"])


@router.post(
    "/", response_model=InteractionPublicRead, status_code=status.HTTP_201_CREATED
)
async def log_interaction(
    person_id: uuid.UUID,
    data: InteractionCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return await create_interaction(db, person_id, current_user.id, data)


@router.get("/", response_model=Paginated[InteractionPublicRead])
async def list_all(
    person_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
    type_slug: str | None = None,
    context: str | None = Query(default=None),
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    items, total = await list_interactions(
        db,
        person_id,
        current_user.id,
        skip=pagination.skip,
        limit=pagination.limit,
        type_slug=type_slug,
        context=context,
    )
    return Paginated(
        items=items, total=total, skip=pagination.skip, limit=pagination.limit
    )


@router.get("/{interaction_id}", response_model=InteractionPublicRead)
async def get_one(
    person_id: uuid.UUID,
    interaction_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    interaction = await get_interaction(db, interaction_id, current_user.id)
    if not interaction or interaction.person_id != person_id:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.patch("/{interaction_id}", response_model=InteractionPublicRead)
async def patch(
    person_id: uuid.UUID,
    interaction_id: uuid.UUID,
    data: InteractionUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    interaction = await update_interaction(db, interaction_id, current_user.id, data)
    if not interaction or interaction.person_id != person_id:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.delete("/{interaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    person_id: uuid.UUID,
    interaction_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await delete_interaction(db, interaction_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Interaction not found")
