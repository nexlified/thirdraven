from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.finance import get_finance_overview
from app.models.user import User
from app.schemas.finance import FinanceOverview

router = APIRouter(prefix="/finances", tags=["finances"])


@router.get("/overview", response_model=FinanceOverview)
async def overview(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    currency: Annotated[str, Query()] = "INR",
):
    return await get_finance_overview(db, current_user.id, currency)
