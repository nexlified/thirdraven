import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.crud.observation import (
    create_observation,
    delete_observation,
    get_observation,
    list_observations,
    update_observation,
)
from app.crud.person import get_person
from app.models.user import User
from app.schemas.paginated import Paginated
from app.schemas.observation import (
    ObservationCreate,
    ObservationPublic,
    ObservationUpdate,
)

router = APIRouter(
    prefix="/persons/{person_id}/observations", tags=["observations"]
)


@router.post("/", response_model=ObservationPublic, status_code=status.HTTP_201_CREATED)
async def create(
    person_id: uuid.UUID,
    data: ObservationCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return await create_observation(db, person_id, current_user.id, data)


@router.get("/", response_model=Paginated[ObservationPublic])
async def list_all(
    person_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
    include_sensitive: bool = True,
    context: str | None = Query(default=None),
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    items, total = await list_observations(
        db, person_id, current_user.id,
        skip=pagination.skip, limit=pagination.limit, include_sensitive=include_sensitive,
        context=context,
    )
    return Paginated(items=items, total=total, skip=pagination.skip, limit=pagination.limit)


@router.get("/{obs_id}", response_model=ObservationPublic)
async def get_one(
    person_id: uuid.UUID,
    obs_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    obs = await get_observation(db, obs_id, current_user.id)
    if not obs or obs.person_id != person_id:
        raise HTTPException(status_code=404, detail="Observation not found")
    return obs


@router.patch("/{obs_id}", response_model=ObservationPublic)
async def patch(
    person_id: uuid.UUID,
    obs_id: uuid.UUID,
    data: ObservationUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    obs = await update_observation(db, obs_id, current_user.id, data)
    if not obs or obs.person_id != person_id:
        raise HTTPException(status_code=404, detail="Observation not found")
    return obs


@router.delete("/{obs_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    person_id: uuid.UUID,
    obs_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    deleted = await delete_observation(db, obs_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Observation not found")
