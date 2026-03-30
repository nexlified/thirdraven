import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.crud.subscription import (
    create_payment,
    create_subscription,
    delete_payment,
    get_subscription_public,
    get_summary,
    list_payments,
    list_subscriptions,
    soft_delete_subscription,
    update_payment,
    update_subscription,
)
from app.models.user import User
from app.schemas.paginated import Paginated
from app.schemas.subscription import (
    BillPaymentCreate,
    BillPaymentPublicRead,
    BillPaymentUpdate,
    SubscriptionCreate,
    SubscriptionPublicRead,
    SubscriptionSummary,
    SubscriptionUpdate,
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post(
    "/", response_model=SubscriptionPublicRead, status_code=status.HTTP_201_CREATED
)
async def create(
    data: SubscriptionCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_subscription(db, current_user.id, data)


@router.get("/summary", response_model=SubscriptionSummary)
async def summary(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await get_summary(db, current_user.id)


@router.get("/", response_model=Paginated[SubscriptionPublicRead])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
    status: str | None = None,
    category: str | None = None,
    billing_cycle: str | None = None,
):
    items, total = await list_subscriptions(
        db,
        current_user.id,
        skip=pagination.skip,
        limit=pagination.limit,
        status=status,
        category=category,
        billing_cycle=billing_cycle,
    )
    return Paginated(items=items, total=total, skip=pagination.skip, limit=pagination.limit)


@router.get("/{subscription_id}", response_model=SubscriptionPublicRead)
async def get_one(
    subscription_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    sub = await get_subscription_public(db, subscription_id, current_user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.patch("/{subscription_id}", response_model=SubscriptionPublicRead)
async def patch(
    subscription_id: uuid.UUID,
    data: SubscriptionUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    sub = await update_subscription(db, subscription_id, current_user.id, data)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    subscription_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    sub = await soft_delete_subscription(db, subscription_id, current_user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")


# ── Payments ────────────────────────────────────────────────────────────────────


@router.post(
    "/{subscription_id}/payments",
    response_model=BillPaymentPublicRead,
    status_code=status.HTTP_201_CREATED,
)
async def log_payment(
    subscription_id: uuid.UUID,
    data: BillPaymentCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    # Verify subscription belongs to user
    sub = await get_subscription_public(db, subscription_id, current_user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return await create_payment(db, subscription_id, current_user.id, data)


@router.get(
    "/{subscription_id}/payments",
    response_model=Paginated[BillPaymentPublicRead],
)
async def list_sub_payments(
    subscription_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
):
    sub = await get_subscription_public(db, subscription_id, current_user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    items, total = await list_payments(
        db, subscription_id, current_user.id, skip=pagination.skip, limit=pagination.limit
    )
    return Paginated(items=items, total=total, skip=pagination.skip, limit=pagination.limit)


@router.patch(
    "/{subscription_id}/payments/{payment_id}",
    response_model=BillPaymentPublicRead,
)
async def patch_payment(
    subscription_id: uuid.UUID,
    payment_id: uuid.UUID,
    data: BillPaymentUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    payment = await update_payment(
        db, subscription_id, payment_id, current_user.id, data
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.delete(
    "/{subscription_id}/payments/{payment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_payment(
    subscription_id: uuid.UUID,
    payment_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await delete_payment(db, subscription_id, payment_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Payment not found")
