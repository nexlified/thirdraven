import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.crud.event import (
    add_event_person,
    create_event,
    delete_event,
    get_event,
    list_event_persons,
    list_events,
    remove_event_person,
    update_event,
)
from app.models.user import User
from app.schemas.paginated import Paginated
from app.schemas.event import (
    EventCreate,
    EventPersonCreate,
    EventPersonPublic,
    EventPublic,
    EventUpdate,
)

events_router = APIRouter(prefix="/events", tags=["events"])
event_persons_router = APIRouter(
    prefix="/events/{event_id}/persons", tags=["events"]
)


# ── /events CRUD ───────────────────────────────────────────────────────────────


@events_router.post(
    "/", response_model=EventPublic, status_code=status.HTTP_201_CREATED
)
async def create(
    data: EventCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_event(db, current_user.id, data)


@events_router.get("/", response_model=Paginated[EventPublic])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
):
    items, total = await list_events(db, current_user.id, skip=pagination.skip, limit=pagination.limit)
    return Paginated(items=items, total=total, skip=pagination.skip, limit=pagination.limit)


@events_router.get("/{event_id}", response_model=EventPublic)
async def get_one(
    event_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    event = await get_event(db, event_id, current_user.id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@events_router.patch("/{event_id}", response_model=EventPublic)
async def patch(
    event_id: uuid.UUID,
    data: EventUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    event = await update_event(db, event_id, current_user.id, data)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@events_router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    event_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await delete_event(db, event_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")


# ── /events/{event_id}/persons ─────────────────────────────────────────────────


@event_persons_router.post(
    "/", response_model=EventPersonPublic, status_code=status.HTTP_201_CREATED
)
async def add_person(
    event_id: uuid.UUID,
    data: EventPersonCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await add_event_person(db, event_id, current_user.id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Event not found")
    return result


@event_persons_router.get("/", response_model=list[EventPersonPublic])
async def list_persons(
    event_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await list_event_persons(db, event_id, current_user.id)


@event_persons_router.delete(
    "/{event_person_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_person(
    event_id: uuid.UUID,
    event_person_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await remove_event_person(db, event_id, event_person_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event person not found")
