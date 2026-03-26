"""Raven decision log endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.raven_log import RavenLog
from app.models.user import User
from app.schemas.raven_log import RavenLogPublic

router = APIRouter(prefix="/raven", tags=["raven"])


@router.get("/logs", response_model=list[RavenLogPublic])
async def list_raven_logs(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 50,
    operation: str | None = None,
):
    stmt = (
        select(RavenLog)
        .where(RavenLog.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(RavenLog.created_at.desc())
    )
    if operation:
        stmt = stmt.where(RavenLog.operation == operation)

    result = await db.execute(stmt)
    return [RavenLogPublic.model_validate(r) for r in result.scalars().all()]
