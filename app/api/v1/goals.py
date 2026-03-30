import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.crud.goal import (
    create_goal,
    delete_goal,
    get_goal,
    list_goals,
    update_goal,
)
from app.crud.person import get_person
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalPublic, GoalUpdate
from app.schemas.paginated import Paginated

router = APIRouter(
    prefix="/persons/{person_id}/goals", tags=["goals"]
)


@router.post("/", response_model=GoalPublic, status_code=status.HTTP_201_CREATED)
async def create(
    person_id: uuid.UUID,
    data: GoalCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return await create_goal(db, person_id, current_user.id, data)


@router.get("/", response_model=Paginated[GoalPublic])
async def list_all(
    person_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
    active_only: bool = False,
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    items, total = await list_goals(
        db, person_id, current_user.id,
        active_only=active_only, skip=pagination.skip, limit=pagination.limit,
    )
    return Paginated(items=items, total=total, skip=pagination.skip, limit=pagination.limit)


@router.get("/{goal_id}", response_model=GoalPublic)
async def get_one(
    person_id: uuid.UUID,
    goal_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    goal = await get_goal(db, goal_id, current_user.id)
    if not goal or goal.person_id != person_id:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.patch("/{goal_id}", response_model=GoalPublic)
async def patch(
    person_id: uuid.UUID,
    goal_id: uuid.UUID,
    data: GoalUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    goal = await update_goal(db, goal_id, current_user.id, data)
    if not goal or goal.person_id != person_id:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    person_id: uuid.UUID,
    goal_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    deleted = await delete_goal(db, goal_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Goal not found")
