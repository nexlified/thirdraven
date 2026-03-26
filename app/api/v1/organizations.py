import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.organization import (
    create_org,
    get_org,
    link_person_org,
    list_orgs,
    list_person_orgs,
    soft_delete_org,
    unlink_person_org,
    update_org,
    update_person_org,
)
from app.crud.household import get_user_household_id
from app.crud.person import get_person
from app.models.user import User
from app.schemas.organization import (
    OrgCreate,
    OrgPublic,
    OrgUpdate,
    PersonOrgCreate,
    PersonOrgPublic,
    PersonOrgUpdate,
)

orgs_router = APIRouter(prefix="/organizations", tags=["organizations"])
person_orgs_router = APIRouter(
    prefix="/persons/{person_id}/organizations", tags=["organizations"]
)


# ── /organizations CRUD ────────────────────────────────────────────────────────


@orgs_router.post("/", response_model=OrgPublic, status_code=status.HTTP_201_CREATED)
async def create(
    data: OrgCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    household_id = await get_user_household_id(db, current_user.id)
    return await create_org(db, current_user.id, data, household_id=household_id)


@orgs_router.get("/", response_model=list[OrgPublic])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 50,
):
    household_id = await get_user_household_id(db, current_user.id)
    return await list_orgs(db, current_user.id, skip=skip, limit=limit, household_id=household_id)


@orgs_router.get("/{org_id}", response_model=OrgPublic)
async def get_one(
    org_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    household_id = await get_user_household_id(db, current_user.id)
    org = await get_org(db, org_id, current_user.id, household_id=household_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@orgs_router.patch("/{org_id}", response_model=OrgPublic)
async def patch(
    org_id: uuid.UUID,
    data: OrgUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    household_id = await get_user_household_id(db, current_user.id)
    org = await update_org(db, org_id, current_user.id, data, household_id=household_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@orgs_router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    org_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await soft_delete_org(db, org_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Organization not found")


# ── /persons/{person_id}/organizations ────────────────────────────────────────


@person_orgs_router.post(
    "/", response_model=PersonOrgPublic, status_code=status.HTTP_201_CREATED
)
async def link_org(
    person_id: uuid.UUID,
    data: PersonOrgCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    household_id = await get_user_household_id(db, current_user.id)
    person = await get_person(db, person_id, current_user.id, household_id=household_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return await link_person_org(db, person_id, data)


@person_orgs_router.get("/", response_model=list[PersonOrgPublic])
async def list_links(
    person_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    household_id = await get_user_household_id(db, current_user.id)
    person = await get_person(db, person_id, current_user.id, household_id=household_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return await list_person_orgs(db, person_id)


@person_orgs_router.patch("/{link_id}", response_model=PersonOrgPublic)
async def patch_link(
    person_id: uuid.UUID,
    link_id: uuid.UUID,
    data: PersonOrgUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    link = await update_person_org(db, link_id, person_id, data)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link


@person_orgs_router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_org(
    person_id: uuid.UUID,
    link_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await unlink_person_org(db, link_id, person_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Link not found")
