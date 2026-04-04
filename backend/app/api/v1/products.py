import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.crud.product import (
    create_product,
    get_product_public,
    list_products,
    soft_delete_product,
    update_product,
)
from app.models.user import User
from app.schemas.paginated import Paginated
from app.schemas.product import ProductCreate, ProductPublic, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductPublic)
async def create(
    data: ProductCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    product, is_new = await create_product(db, current_user.id, data)
    status_code = status.HTTP_201_CREATED if is_new else status.HTTP_200_OK
    return JSONResponse(
        content=product.model_dump(mode="json"),
        status_code=status_code,
    )


@router.get("/", response_model=Paginated[ProductPublic])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
    category: str | None = None,
    search: str | None = None,
):
    items, total = await list_products(
        db,
        current_user.id,
        skip=pagination.skip,
        limit=pagination.limit,
        category_slug=category,
        search=search,
    )
    return Paginated(
        items=items, total=total, skip=pagination.skip, limit=pagination.limit
    )


@router.get("/{product_id}", response_model=ProductPublic)
async def get_one(
    product_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    product = await get_product_public(db, product_id, current_user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/{product_id}", response_model=ProductPublic)
async def patch(
    product_id: uuid.UUID,
    data: ProductUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    product = await update_product(db, product_id, current_user.id, data)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    product_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await soft_delete_product(db, product_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")


@router.get("/{product_id}/items", response_model=Paginated[dict])
async def get_items(
    product_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
):
    """Return TransactionItem rows for this product (price history).

    TransactionItem model is introduced in a follow-up issue.
    Until then this endpoint always returns an empty paginated result.
    """
    product = await get_product_public(db, product_id, current_user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return Paginated(
        items=[],
        total=0,
        skip=pagination.skip,
        limit=pagination.limit,
    )
