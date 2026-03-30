import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.crud.context_package import get_context_package, get_relationship_health
from app.crud.household import get_user_household_id
from app.crud.person import (
    create_person,
    get_person,
    list_persons,
    soft_delete_person,
    update_person,
)
from app.crud.person_relationship import (
    add_relationship,
    list_relationships_for_person,
)
from app.crud.reference import add_person_term, list_person_terms, remove_person_term
from app.crud.vocabulary import list_terms as list_vocab_terms
from app.models.user import User
from app.schemas.context_package import ContextPackage, RelationshipHealthEntry
from app.schemas.paginated import Paginated
from app.schemas.person import (
    PersonCreate,
    PersonFieldOptions,
    PersonSlim,
    PersonUpdate,
    PersonWithRelationships,
    RelationshipCreate,
    RelationshipPublic,
)
from app.schemas.reference import PersonTermCreate, PersonTermPublic
from app.schemas.vocabulary import TermSlim

router = APIRouter(prefix="/persons", tags=["persons"])


@router.post("/", response_model=PersonSlim, status_code=status.HTTP_201_CREATED)
async def create(
    data: PersonCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    household_id = await get_user_household_id(db, current_user.id)
    return await create_person(db, current_user.id, data, household_id=household_id)


@router.get("/", response_model=Paginated[PersonSlim])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
    is_placeholder: bool | None = Query(default=None),
    is_bot: bool | None = Query(default=None),
    relationship_nature: str | None = Query(default=None),
):
    household_id = await get_user_household_id(db, current_user.id)
    items, total = await list_persons(
        db,
        current_user.id,
        skip=pagination.skip,
        limit=pagination.limit,
        household_id=household_id,
        is_placeholder=is_placeholder,
        is_bot=is_bot,
        relationship_nature=relationship_nature,
    )
    return Paginated(items=items, total=total, skip=pagination.skip, limit=pagination.limit)


@router.get("/relationship-health", response_model=list[RelationshipHealthEntry])
async def relationship_health(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await get_relationship_health(db, current_user.id)


@router.get("/schema", response_model=PersonFieldOptions)
async def get_schema(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return PersonFieldOptions(
        prefixes=[TermSlim.model_validate(t) for t in await list_vocab_terms(db, "name-prefixes")],
        genders=[TermSlim.model_validate(t) for t in await list_vocab_terms(db, "genders")],
        occupations=[TermSlim.model_validate(t) for t in await list_vocab_terms(db, "occupations")],
        tags=[TermSlim.model_validate(t) for t in await list_vocab_terms(db, "person-tags")],
        relationship_types=[TermSlim.model_validate(t) for t in await list_vocab_terms(db, "relationship-types")],
        preferred_contact=[TermSlim.model_validate(t) for t in await list_vocab_terms(db, "preferred-contact")],
        address_types=["home", "work", "other"],
        channel_types=[
            "email", "mobile", "phone", "whatsapp", "telegram", "discord",
            "twitter", "instagram", "github", "facebook", "linkedin", "website",
            "signal", "slack", "other",
        ],
    )


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
    rels, _ = await list_relationships_for_person(
        db, person_id, current_user.id, skip=0, limit=500
    )
    return PersonWithRelationships(**person.model_dump(), relationships=rels)


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
    try:
        person = await soft_delete_person(db, person_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=403, detail="Cannot delete your own person record")
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


@router.get("/{person_id}/relationships", response_model=Paginated[RelationshipPublic])
async def list_person_relationships(
    person_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
):
    person = await get_person(db, person_id, current_user.id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    items, total = await list_relationships_for_person(
        db, person_id, current_user.id, skip=pagination.skip, limit=pagination.limit
    )
    return Paginated(items=items, total=total, skip=pagination.skip, limit=pagination.limit)


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
