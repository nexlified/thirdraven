import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.shopping_list import (
    add_item,
    complete_list,
    create_shopping_list,
    delete_item,
    delete_shopping_list,
    get_shopping_list,
    list_shopping_lists,
    update_item,
    update_shopping_list,
)
from app.models.user import User
from app.schemas.shopping_list import (
    ShoppingListCreate,
    ShoppingListItemCreate,
    ShoppingListItemPublic,
    ShoppingListItemUpdate,
    ShoppingListPublic,
    ShoppingListUpdate,
)

router = APIRouter(prefix="/shopping-lists", tags=["shopping-lists"])


class CompleteListRequest(BaseModel):
    create_transaction: bool = False


@router.post(
    "/",
    response_model=ShoppingListPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    data: ShoppingListCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_shopping_list(db, current_user.id, data)


# IMPORTANT: /active must be declared before /{list_id} to prevent FastAPI
# from parsing "active" as a UUID parameter.
@router.get("/active", response_model=list[ShoppingListPublic])
async def get_active(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await list_shopping_lists(db, current_user.id, include_completed=False)


@router.get("/", response_model=list[ShoppingListPublic])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    include_completed: Annotated[bool, Query()] = False,
):
    return await list_shopping_lists(
        db, current_user.id, include_completed=include_completed
    )


@router.get("/{list_id}", response_model=ShoppingListPublic)
async def get_one(
    list_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    sl = await get_shopping_list(db, list_id, current_user.id)
    if not sl:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    return sl


@router.patch("/{list_id}", response_model=ShoppingListPublic)
async def patch(
    list_id: uuid.UUID,
    data: ShoppingListUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    sl = await update_shopping_list(db, list_id, current_user.id, data)
    if not sl:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    return sl


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    list_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await delete_shopping_list(db, list_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Shopping list not found")


# IMPORTANT: /{list_id}/complete must be declared before /{list_id}/items/
# so the literal "complete" path segment is matched correctly.
@router.post("/{list_id}/complete", response_model=ShoppingListPublic)
async def complete(
    list_id: uuid.UUID,
    body: CompleteListRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    sl = await complete_list(db, list_id, current_user.id, body.create_transaction)
    if not sl:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    return sl


@router.post(
    "/{list_id}/items/",
    response_model=ShoppingListItemPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_item(
    list_id: uuid.UUID,
    data: ShoppingListItemCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    item = await add_item(db, current_user.id, list_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    return item


@router.patch("/{list_id}/items/{item_id}", response_model=ShoppingListItemPublic)
async def patch_item(
    list_id: uuid.UUID,
    item_id: uuid.UUID,
    data: ShoppingListItemUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    _ = list_id  # ownership validated via item's owner_id
    item = await update_item(db, item_id, current_user.id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Shopping list item not found")
    return item


@router.delete("/{list_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item_endpoint(
    list_id: uuid.UUID,
    item_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    _ = list_id  # ownership validated via item's owner_id
    deleted = await delete_item(db, item_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Shopping list item not found")
