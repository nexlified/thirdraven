import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.crud.contact import (
    add_relationship,
    create_contact,
    get_contact,
    get_relationships_for_contact,
    list_contacts,
    soft_delete_contact,
    update_contact,
)
from app.models.user import User
from app.schemas.paginated import Paginated
from app.schemas.contact import (
    ContactCreate,
    ContactPublicRead,
    ContactUpdate,
    ContactWithRelationships,
    RelationshipCreate,
    RelationshipPublic,
)

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("/", response_model=ContactPublicRead, status_code=status.HTTP_201_CREATED)
async def create(
    data: ContactCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_contact(db, current_user.id, data)


@router.get("/", response_model=Paginated[ContactPublicRead])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
):
    items, total = await list_contacts(db, current_user.id, skip=pagination.skip, limit=pagination.limit)
    return Paginated(items=items, total=total, skip=pagination.skip, limit=pagination.limit)


@router.get("/{contact_id}", response_model=ContactWithRelationships)
async def get_one(
    contact_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    contact = await get_contact(db, contact_id, current_user.id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    relationships = await get_relationships_for_contact(db, contact_id)
    return ContactWithRelationships(
        **ContactPublicRead.model_validate(contact).model_dump(),
        relationships=[RelationshipPublic.model_validate(r) for r in relationships],
    )


@router.patch("/{contact_id}", response_model=ContactPublicRead)
async def patch(
    contact_id: uuid.UUID,
    data: ContactUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    contact = await update_contact(db, contact_id, current_user.id, data)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    contact_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    contact = await soft_delete_contact(db, contact_id, current_user.id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")


@router.post(
    "/{contact_id}/relationships",
    response_model=RelationshipPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_relationship(
    contact_id: uuid.UUID,
    data: RelationshipCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    # Verify source contact belongs to current user
    contact = await get_contact(db, contact_id, current_user.id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    # Verify target contact belongs to current user
    target = await get_contact(db, data.to_contact_id, current_user.id)
    if not target:
        raise HTTPException(status_code=404, detail="Target contact not found")
    return await add_relationship(
        db, contact_id, data.to_contact_id, data.label, current_user.id
    )
