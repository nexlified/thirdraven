from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.renewal import get_upcoming_renewals
from app.models.user import User
from app.schemas.renewal import RenewalEntry

router = APIRouter(prefix="/renewals", tags=["renewals"])


@router.get("/upcoming", response_model=list[RenewalEntry])
async def upcoming(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: int = 30,
):
    return await get_upcoming_renewals(db, current_user.id, days=days)
