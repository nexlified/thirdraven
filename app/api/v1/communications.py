import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.communication import (
    create_communication,
    delete_communication,
    get_communication,
    ingest_communication,
    list_communications,
    match_communication,
    update_communication,
)
from app.models.user import User
from app.schemas.communication import (
    CommCreate,
    CommIngest,
    CommPublic,
    CommUpdate,
)

router = APIRouter(prefix="/communications", tags=["communications"])


@router.post(
    "/ingest", response_model=CommPublic, status_code=status.HTTP_201_CREATED
)
async def ingest(
    data: CommIngest,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Flexible dump endpoint — unknown fields stored in raw_payload."""
    return await ingest_communication(db, current_user.id, data)


@router.post("/", response_model=CommPublic, status_code=status.HTTP_201_CREATED)
async def create(
    data: CommCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_communication(db, current_user.id, data)


@router.get("/", response_model=list[CommPublic])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 50,
    channel: str | None = None,
    status: str | None = None,
    person_id: uuid.UUID | None = None,
):
    return await list_communications(
        db,
        current_user.id,
        skip=skip,
        limit=limit,
        channel=channel,
        status=status,
        person_id=person_id,
    )


@router.get("/{comm_id}", response_model=CommPublic)
async def get_one(
    comm_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    comm = await get_communication(db, comm_id, current_user.id)
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    return comm


@router.patch("/{comm_id}", response_model=CommPublic)
async def patch(
    comm_id: uuid.UUID,
    data: CommUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    comm = await update_communication(db, comm_id, current_user.id, data)
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    return comm


@router.delete("/{comm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    comm_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await delete_communication(db, comm_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Communication not found")


@router.post("/{comm_id}/match", response_model=CommPublic)
async def trigger_match(
    comm_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Re-attempt person matching. Creates Interaction if person_id is already set."""
    comm = await match_communication(db, comm_id, current_user.id)
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    return comm


@router.post("/{comm_id}/extract-actions", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def extract_actions(
    comm_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Phase 2: AI-powered extraction of follow-ups and observations."""
    raise HTTPException(
        status_code=501,
        detail="Actionable extraction is not yet implemented (Phase 2).",
    )
