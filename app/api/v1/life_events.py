import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.schemas.paginated import Paginated
from app.crud.person import get_person
from app.crud.person_life_event import (
    create_life_event,
    create_significant_date,
    delete_life_event,
    delete_significant_date,
    get_life_event,
    get_significant_date,
    list_life_events,
    list_significant_dates,
    update_life_event,
    update_significant_date,
)
from app.models.user import User
from app.schemas.person_life_event import (
    LifeEventCreate,
    LifeEventPublic,
    LifeEventUpdate,
    SignificantDateCreate,
    SignificantDatePublic,
    SignificantDateUpdate,
)

life_events_router = APIRouter(
    prefix="/persons/{person_id}/life-events", tags=["life-events"]
)
significant_dates_router = APIRouter(
    prefix="/persons/{person_id}/significant-dates", tags=["significant-dates"]
)


# ── Life Events ────────────────────────────────────────────────────────────────


@life_events_router.post(
    "/", response_model=LifeEventPublic, status_code=status.HTTP_201_CREATED
)
async def create_event(
    person_id: uuid.UUID,
    data: LifeEventCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return await create_life_event(db, person_id, current_user.id, data)


@life_events_router.get("/", response_model=Paginated[LifeEventPublic])
async def list_events(
    person_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    items, total = await list_life_events(
        db, person_id, current_user.id, skip=pagination.skip, limit=pagination.limit
    )
    return Paginated(items=items, total=total, skip=pagination.skip, limit=pagination.limit)


@life_events_router.get("/{event_id}", response_model=LifeEventPublic)
async def get_event(
    person_id: uuid.UUID,
    event_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    event = await get_life_event(db, event_id, current_user.id)
    if not event or event.person_id != person_id:
        raise HTTPException(status_code=404, detail="Life event not found")
    return event


@life_events_router.patch("/{event_id}", response_model=LifeEventPublic)
async def patch_event(
    person_id: uuid.UUID,
    event_id: uuid.UUID,
    data: LifeEventUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    event = await update_life_event(db, event_id, current_user.id, data)
    if not event or event.person_id != person_id:
        raise HTTPException(status_code=404, detail="Life event not found")
    return event


@life_events_router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    person_id: uuid.UUID,
    event_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    deleted = await delete_life_event(db, event_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Life event not found")


# ── Significant Dates ──────────────────────────────────────────────────────────


@significant_dates_router.post(
    "/", response_model=SignificantDatePublic, status_code=status.HTTP_201_CREATED
)
async def create_date(
    person_id: uuid.UUID,
    data: SignificantDateCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return await create_significant_date(db, person_id, data)


@significant_dates_router.get("/", response_model=list[SignificantDatePublic])
async def list_dates(
    person_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return await list_significant_dates(db, person_id)


@significant_dates_router.get("/{date_id}", response_model=SignificantDatePublic)
async def get_date(
    person_id: uuid.UUID,
    date_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    date = await get_significant_date(db, date_id, person_id)
    if not date:
        raise HTTPException(status_code=404, detail="Significant date not found")
    return date


@significant_dates_router.patch("/{date_id}", response_model=SignificantDatePublic)
async def patch_date(
    person_id: uuid.UUID,
    date_id: uuid.UUID,
    data: SignificantDateUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    date = await update_significant_date(db, date_id, person_id, data)
    if not date:
        raise HTTPException(status_code=404, detail="Significant date not found")
    return date


@significant_dates_router.delete("/{date_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_date(
    person_id: uuid.UUID,
    date_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    deleted = await delete_significant_date(db, date_id, person_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Significant date not found")
