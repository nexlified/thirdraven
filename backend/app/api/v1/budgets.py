import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.budget import (
    create_budget,
    delete_budget,
    list_budgets,
    update_budget,
)
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetPublic, BudgetUpdate, BudgetWithSpend

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("/", response_model=BudgetPublic, status_code=status.HTTP_201_CREATED)
async def create(
    data: BudgetCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_budget(db, current_user.id, data)


@router.get("/", response_model=list[BudgetWithSpend])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    year: Annotated[int, Query()],
    month: Annotated[int, Query()],
):
    return await list_budgets(db, current_user.id, year, month)


@router.patch("/{budget_id}", response_model=BudgetPublic)
async def patch(
    budget_id: uuid.UUID,
    data: BudgetUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await update_budget(db, budget_id, current_user.id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Budget not found")
    return result


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    budget_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await delete_budget(db, budget_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Budget not found")
