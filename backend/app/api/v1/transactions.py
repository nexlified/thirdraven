import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.core.transaction_parser import parse_transaction_input
from app.crud.transaction import (
    create_transaction,
    create_transactions_bulk,
    get_transaction_public,
    get_transaction_summary,
    list_transactions,
    soft_delete_transaction,
    update_transaction,
)
from app.crud.vocabulary import get_vocabulary_slugs
from app.models.user import User
from app.schemas.paginated import Paginated
from app.schemas.transaction import (
    TransactionCreate,
    TransactionPublic,
    TransactionSummary,
    TransactionUpdate,
)


class QuickParseRequest(BaseModel):
    input: str
    currency: str = "INR"


router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionPublic, status_code=status.HTTP_201_CREATED)
async def create(
    data: TransactionCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_transaction(db, current_user.id, data)


@router.post(
    "/bulk",
    response_model=list[TransactionPublic],
    status_code=status.HTTP_201_CREATED,
)
async def bulk_create(
    items: list[TransactionCreate],
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_transactions_bulk(db, current_user.id, items)


# IMPORTANT: /summary must be declared before /{id} to prevent FastAPI
# from parsing "summary" as a UUID parameter.
@router.get("/summary", response_model=TransactionSummary)
async def summary(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    currency: Annotated[str, Query()] = "INR",
):
    if date_from is None:
        date_from = date.today().replace(day=1)
    if date_to is None:
        date_to = date.today()
    return await get_transaction_summary(
        db, current_user.id, date_from, date_to, currency
    )


# IMPORTANT: /parse and /quick-add must be declared before /{transaction_id}
# to prevent FastAPI from parsing them as UUID parameters.
@router.post("/parse", response_model=TransactionCreate)
async def parse_transaction(
    body: QuickParseRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    expense_slugs = await get_vocabulary_slugs(db, "expense-categories")
    income_slugs = await get_vocabulary_slugs(db, "income-categories")
    try:
        parsed = parse_transaction_input(body.input, expense_slugs, income_slugs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TransactionCreate(
        transaction_type=parsed.transaction_type,
        amount=parsed.amount,
        description=parsed.description
        if parsed.description
        else (parsed.merchant if parsed.merchant is not None else body.input),
        category=parsed.category_slug,
        merchant=parsed.merchant,
        transacted_on=parsed.transacted_on,
        currency=body.currency,
    )


@router.post(
    "/quick-add", response_model=TransactionPublic, status_code=status.HTTP_201_CREATED
)
async def quick_add_transaction(
    body: QuickParseRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    tx_create = await parse_transaction(body, db, current_user)
    return await create_transaction(db, current_user.id, tx_create)


@router.get("/", response_model=Paginated[TransactionPublic])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
    transaction_type: str | None = None,
    category: str | None = None,
    payment_method: str | None = None,
    asset_id: uuid.UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search: str | None = None,
):
    items, total = await list_transactions(
        db,
        current_user.id,
        skip=pagination.skip,
        limit=pagination.limit,
        transaction_type=transaction_type,
        category_slug=category,
        payment_method_slug=payment_method,
        asset_id=asset_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )
    return Paginated(
        items=items, total=total, skip=pagination.skip, limit=pagination.limit
    )


@router.get("/{transaction_id}", response_model=TransactionPublic)
async def get_one(
    transaction_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    tx = await get_transaction_public(db, transaction_id, current_user.id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


@router.patch("/{transaction_id}", response_model=TransactionPublic)
async def patch(
    transaction_id: uuid.UUID,
    data: TransactionUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    tx = await update_transaction(db, transaction_id, current_user.id, data)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    transaction_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    tx = await soft_delete_transaction(db, transaction_id, current_user.id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
