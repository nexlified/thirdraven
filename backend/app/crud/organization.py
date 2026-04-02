import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, or_, select

from app.crud.iso_reference import resolve_country_alpha2
from app.crud.vocabulary import resolve_optional_term_slug
from app.models.iso_reference import Country
from app.models.organization import Organization, PersonOrganization
from app.models.vocabulary import Term
from app.schemas.iso_reference import CountrySlim
from app.schemas.organization import (
    OrgCreate,
    OrgPublic,
    OrgSlim,
    OrgUpdate,
    PersonOrgCreate,
    PersonOrgPublic,
    PersonOrgUpdate,
)
from app.schemas.vocabulary import TermSlim


def _org_visibility_clause(owner_id: uuid.UUID, household_id: uuid.UUID | None):
    """WHERE clause covering owner's own orgs + household-visible orgs."""
    if household_id:
        return or_(
            Organization.owner_id == owner_id,
            and_(
                Organization.visibility == "household",
                Organization.household_id == household_id,
            ),
        )
    return Organization.owner_id == owner_id


async def _build_org_public(db: AsyncSession, row: Organization) -> OrgPublic:
    org_type = None
    if row.type_term_id:
        r = await db.execute(select(Term).where(Term.id == row.type_term_id))
        t = r.scalars().first()
        if t:
            org_type = TermSlim.model_validate(t)

    industry = None
    if row.industry_term_id:
        r = await db.execute(select(Term).where(Term.id == row.industry_term_id))
        t = r.scalars().first()
        if t:
            industry = TermSlim.model_validate(t)

    country = None
    if row.country_id:
        r = await db.execute(select(Country).where(Country.id == row.country_id))
        c = r.scalars().first()
        if c:
            country = CountrySlim.model_validate(c)

    return OrgPublic(
        id=row.id,
        owner_id=row.owner_id,
        name=row.name,
        type=org_type,
        description=row.description,
        website=row.website,
        email=row.email,
        phone=row.phone,
        industry=industry,
        founded_year=row.founded_year,
        headquarters_city=row.headquarters_city,
        country=country,
        linkedin_url=row.linkedin_url,
        notes=row.notes,
        visibility=row.visibility,
        household_id=row.household_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _build_org_slim(db: AsyncSession, row: Organization) -> OrgSlim:
    org_type = None
    if row.type_term_id:
        r = await db.execute(select(Term).where(Term.id == row.type_term_id))
        t = r.scalars().first()
        if t:
            org_type = TermSlim.model_validate(t)

    country = None
    if row.country_id:
        r = await db.execute(select(Country).where(Country.id == row.country_id))
        c = r.scalars().first()
        if c:
            country = CountrySlim.model_validate(c)

    return OrgSlim(
        id=row.id,
        name=row.name,
        type=org_type,
        headquarters_city=row.headquarters_city,
        country=country,
    )


async def _build_person_org_public(
    db: AsyncSession, row: PersonOrganization
) -> PersonOrgPublic:
    r = await db.execute(select(Organization).where(Organization.id == row.org_id))
    org_row = r.scalars().first()
    org_slim = await _build_org_slim(db, org_row) if org_row else None

    return PersonOrgPublic(
        id=row.id,
        person_id=row.person_id,
        org=org_slim,
        role=row.role,
        is_current=row.is_current,
        started_on=row.started_on,
        ended_on=row.ended_on,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _resolve_org_fields(db: AsyncSession, raw: dict) -> dict:
    result = {}
    for k, v in raw.items():
        if k == "type":
            result["type_term_id"] = await resolve_optional_term_slug(
                db, "org-types", v
            )
        elif k == "industry":
            result["industry_term_id"] = await resolve_optional_term_slug(
                db, "industries", v
            )
        elif k == "country":
            result["country_id"] = await resolve_country_alpha2(db, v)
        else:
            result[k] = v
    return result


# ── Organization CRUD ──────────────────────────────────────────────────────────


async def create_org(
    db: AsyncSession,
    owner_id: uuid.UUID,
    data: OrgCreate,
    household_id: uuid.UUID | None = None,
) -> OrgPublic:
    raw = data.model_dump(exclude_unset=True)
    requested_visibility = raw.get("visibility", "private")
    if requested_visibility == "household":
        if not household_id:
            raise HTTPException(
                status_code=400,
                detail="You must be in a household to share records.",
            )
        raw["household_id"] = household_id
        raw["visibility"] = "household"
    else:
        raw["visibility"] = "private"
        raw.pop("household_id", None)
    db_fields = await _resolve_org_fields(db, raw)
    row = Organization(owner_id=owner_id, **db_fields)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_org_public(db, row)


async def get_org(
    db: AsyncSession,
    org_id: uuid.UUID,
    owner_id: uuid.UUID,
    household_id: uuid.UUID | None = None,
) -> OrgPublic | None:
    r = await db.execute(
        select(Organization).where(
            Organization.id == org_id,
            _org_visibility_clause(owner_id, household_id),
            Organization.deleted_at.is_(None),
        )
    )
    row = r.scalars().first()
    return await _build_org_public(db, row) if row else None


async def list_orgs(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    household_id: uuid.UUID | None = None,
) -> tuple[list[OrgPublic], int]:
    base = select(Organization).where(
        _org_visibility_clause(owner_id, household_id),
        Organization.deleted_at.is_(None),
    )
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    r = await db.execute(base.order_by(Organization.name).offset(skip).limit(limit))
    return [await _build_org_public(db, row) for row in r.scalars().all()], total


async def update_org(
    db: AsyncSession,
    org_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: OrgUpdate,
    household_id: uuid.UUID | None = None,
) -> OrgPublic | None:
    # Write path: owner-only (no household visibility)
    r = await db.execute(
        select(Organization).where(
            Organization.id == org_id,
            Organization.owner_id == owner_id,
            Organization.deleted_at.is_(None),
        )
    )
    row = r.scalars().first()
    if not row:
        return None
    raw = data.model_dump(exclude_unset=True)
    # Handle visibility change
    if "visibility" in raw:
        new_vis = raw.pop("visibility")
        if new_vis == "household":
            if not household_id:
                raise HTTPException(
                    status_code=400,
                    detail="You must be in a household to share records.",
                )
            row.visibility = "household"
            row.household_id = household_id
        else:
            row.visibility = "private"
            row.household_id = None
    db_fields = await _resolve_org_fields(db, raw)
    for field, value in db_fields.items():
        setattr(row, field, value)
    row.updated_at = datetime.utcnow()
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_org_public(db, row)


async def soft_delete_org(
    db: AsyncSession, org_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    r = await db.execute(
        select(Organization).where(
            Organization.id == org_id,
            Organization.owner_id == owner_id,
            Organization.deleted_at.is_(None),
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    row.deleted_at = datetime.utcnow()
    db.add(row)
    await db.commit()
    return True


# ── PersonOrganization CRUD ────────────────────────────────────────────────────


async def link_person_org(
    db: AsyncSession, person_id: uuid.UUID, data: PersonOrgCreate
) -> PersonOrgPublic:
    row = PersonOrganization(
        person_id=person_id,
        org_id=data.org_id,
        role=data.role,
        is_current=data.is_current,
        started_on=data.started_on,
        ended_on=data.ended_on,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_person_org_public(db, row)


async def list_person_orgs(
    db: AsyncSession, person_id: uuid.UUID
) -> list[PersonOrgPublic]:
    r = await db.execute(
        select(PersonOrganization)
        .where(PersonOrganization.person_id == person_id)
        .order_by(
            PersonOrganization.is_current.desc(),
            PersonOrganization.started_on.desc().nulls_last(),
        )
    )
    return [await _build_person_org_public(db, row) for row in r.scalars().all()]


async def update_person_org(
    db: AsyncSession,
    link_id: uuid.UUID,
    person_id: uuid.UUID,
    data: PersonOrgUpdate,
) -> PersonOrgPublic | None:
    r = await db.execute(
        select(PersonOrganization).where(
            PersonOrganization.id == link_id,
            PersonOrganization.person_id == person_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    row.updated_at = datetime.utcnow()
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_person_org_public(db, row)


async def unlink_person_org(
    db: AsyncSession, link_id: uuid.UUID, person_id: uuid.UUID
) -> bool:
    r = await db.execute(
        select(PersonOrganization).where(
            PersonOrganization.id == link_id,
            PersonOrganization.person_id == person_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True
