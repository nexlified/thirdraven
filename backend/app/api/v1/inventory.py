from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.inventory import list_low_stock
from app.models.user import User
from app.schemas.inventory import InventoryProfilePublic

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/low-stock", response_model=list[InventoryProfilePublic])
async def get_low_stock(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await list_low_stock(db, current_user.id)
