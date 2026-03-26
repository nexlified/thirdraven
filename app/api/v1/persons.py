import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.context_package import get_context_package, get_relationship_health
from app.crud.household import get_user_household_id
from app.crud.person import (
    add_relationship,
    create_person,
    get_person,
    get_relationships_for_person,
    list_persons,
    soft_delete_person,
    update_person,
)
from app.crud.reference import add_person_term, list_person_terms, remove_person_term
from app.models.user import User
from app.schemas.context_package import ContextPackage, RelationshipHealthEntry
from app.schemas.person import (
    PersonCreate,
    PersonSlim,
    PersonUpdate,
    PersonWithRelationships,
    RelationshipCreate,
    RelationshipPublic,
)
from app.schemas.reference import PersonTermCreate, PersonTermPublic

router = APIRouter(prefix="/persons", tags=["persons"])


@router.post("/", response_model=PersonSlim, status_code=status.HTTP_201_CREATED)
async def create(
    data: PersonCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    household_id = await get_user_household_id(db, current_user.id)
    return await create_person(db, current_user.id, data, household_id=household_id)


@router.get("/", response_model=list[PersonSlim])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 50,
):
    household_id = await get_user_household_id(db, current_user.id)
    return await list_persons(db, current_user.id, skip=skip, limit=limit, household_id=household_id)


@router.get("/relationship-health", response_model=list[RelationshipHealthEntry])
async def relationship_health(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await get_relationship_health(db, current_user.id)


@router.get("/{person_id}", response_model=PersonWithRelationships)
async def get_one(
    person_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    include: str = "",
):
    household_id = await get_user_household_id(db, current_user.id)
    include_list = [s.strip() for s in include.split(",") if s.strip()]
    person = await get_person(
        db, person_id, current_user.id, include=include_list or None, household_id=household_id
    )
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    relationships = await get_relationships_for_person(db, person_id)
    return PersonWithRelationships(
        **person.model_dump(),
        relationships=[RelationshipPublic.model_validate(r) for r in relationships],
    )


@router.patch("/{person_id}", response_model=PersonSlim)
async def patch(
    person_id: uuid.UUID,
    data: PersonUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    household_id = await get_user_household_id(db, current_user.id)
    person = await update_person(db, person_id, current_user.id, data, household_id=household_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    person_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await soft_delete_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")


@router.post(
    "/{person_id}/relationships",
    response_model=RelationshipPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_relationship(
    person_id: uuid.UUID,
    data: RelationshipCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    # Source person must be owned by current user (relationships are personal)
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    household_id = await get_user_household_id(db, current_user.id)
    target = await get_person(db, data.to_person_id, current_user.id, household_id=household_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target person not found")
    return await add_relationship(
        db, person_id, data.to_person_id, data.label, current_user.id
    )


@router.post(
    "/{person_id}/terms",
    response_model=PersonTermPublic,
    status_code=status.HTTP_201_CREATED,
)
async def link_term(
    person_id: uuid.UUID,
    data: PersonTermCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return await add_person_term(db, person_id, data)


@router.get("/{person_id}/terms", response_model=list[PersonTermPublic])
async def list_terms(
    person_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return await list_person_terms(db, person_id)


@router.delete(
    "/{person_id}/terms/{term_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unlink_term(
    person_id: uuid.UUID,
    term_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    removed = await remove_person_term(db, person_id, term_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Term link not found")


@router.get("/{person_id}/context-package", response_model=ContextPackage)
async def context_package(
    person_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    pkg = await get_context_package(db, person_id, current_user.id)
    if not pkg:
        raise HTTPException(status_code=404, detail="Person not found")
    return pkg
