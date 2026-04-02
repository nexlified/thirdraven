import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.crud.loan import (
    create_loan,
    get_loan,
    list_loans,
    soft_delete_loan,
    update_loan,
)
from app.models.user import User
from app.schemas.loan import LoanCreate, LoanPublic, LoanUpdate
from app.schemas.paginated import Paginated

router = APIRouter(prefix="/loans", tags=["loans"])
person_loans_router = APIRouter(prefix="/persons/{person_id}/loans", tags=["loans"])


@router.post("/", response_model=LoanPublic, status_code=status.HTTP_201_CREATED)
async def create(
    data: LoanCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_loan(db, current_user.id, data)


@router.get("/", response_model=Paginated[LoanPublic])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
    status_filter: str | None = None,
    direction: str | None = None,
):
    items, total = await list_loans(
        db,
        current_user.id,
        skip=pagination.skip,
        limit=pagination.limit,
        status=status_filter,
        direction=direction,
    )
    return Paginated(
        items=items, total=total, skip=pagination.skip, limit=pagination.limit
    )


@router.get("/{loan_id}", response_model=LoanPublic)
async def get_one(
    loan_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    loan = await get_loan(db, loan_id, current_user.id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan


@router.patch("/{loan_id}", response_model=LoanPublic)
async def patch(
    loan_id: uuid.UUID,
    data: LoanUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    loan = await update_loan(db, loan_id, current_user.id, data)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    loan_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await soft_delete_loan(db, loan_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Loan not found")


# ── Person-scoped loans ──────────────────────────────────────────────────────


@person_loans_router.get("/", response_model=Paginated[LoanPublic])
async def list_person_loans(
    person_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
):
    items, total = await list_loans(
        db,
        current_user.id,
        skip=pagination.skip,
        limit=pagination.limit,
        person_id=person_id,
    )
    return Paginated(
        items=items, total=total, skip=pagination.skip, limit=pagination.limit
    )
