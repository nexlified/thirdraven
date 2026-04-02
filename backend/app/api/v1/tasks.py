import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.crud.task import (
    create_task,
    get_task_public,
    get_task_summary,
    list_tasks,
    soft_delete_task,
    update_task,
)
from app.models.user import User
from app.schemas.paginated import Paginated
from app.schemas.task import TaskCreate, TaskPublicRead, TaskSummary, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskPublicRead, status_code=status.HTTP_201_CREATED)
async def create(
    data: TaskCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_task(db, current_user.id, data)


@router.get("/summary", response_model=TaskSummary)
async def summary(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await get_task_summary(db, current_user.id)


@router.get("/", response_model=Paginated[TaskPublicRead])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
    status: str | None = None,
    priority: str | None = None,
    person_id: uuid.UUID | None = None,
    asset_id: uuid.UUID | None = None,
    subscription_id: uuid.UUID | None = None,
    event_id: uuid.UUID | None = None,
    due_before: date | None = None,
    due_after: date | None = None,
    overdue: bool | None = None,
):
    items, total = await list_tasks(
        db,
        current_user.id,
        skip=pagination.skip,
        limit=pagination.limit,
        status=status,
        priority=priority,
        person_id=person_id,
        asset_id=asset_id,
        subscription_id=subscription_id,
        event_id=event_id,
        due_before=due_before,
        due_after=due_after,
        overdue=overdue,
    )
    return Paginated(
        items=items, total=total, skip=pagination.skip, limit=pagination.limit
    )


@router.get("/{task_id}", response_model=TaskPublicRead)
async def get_one(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    task = await get_task_public(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskPublicRead)
async def patch(
    task_id: uuid.UUID,
    data: TaskUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    task = await update_task(db, task_id, current_user.id, data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    task = await soft_delete_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
