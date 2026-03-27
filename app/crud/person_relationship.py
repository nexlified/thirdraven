import uuid

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.vocabulary import resolve_term_slug
from app.models.person import Person
from app.models.person_relationship import PersonRelationship
from app.models.vocabulary import Term
from app.schemas.person import RelatedPersonRef, RelationshipPublic, RelationshipUpdate
from app.schemas.vocabulary import TermSlim


async def _build_rel_public(db: AsyncSession, row: PersonRelationship) -> RelationshipPublic:
    term_result = await db.execute(select(Term).where(Term.id == row.label_term_id))
    term = term_result.scalars().first()

    from_result = await db.execute(select(Person).where(Person.id == row.from_person_id))
    from_person = from_result.scalars().first()

    to_result = await db.execute(select(Person).where(Person.id == row.to_person_id))
    to_person = to_result.scalars().first()

    return RelationshipPublic(
        id=row.id,
        person=RelatedPersonRef.model_validate(from_person),
        related_person=RelatedPersonRef.model_validate(to_person),
        label=TermSlim.model_validate(term),
        inverse_id=row.inverse_id,
        created_at=row.created_at,
    )


async def add_relationship(
    db: AsyncSession,
    from_id: uuid.UUID,
    to_id: uuid.UUID,
    label_slug: str,
    owner_id: uuid.UUID,
) -> RelationshipPublic:
    # Resolve forward label term
    forward_term_id = await resolve_term_slug(db, "relationship-types", label_slug)

    # Duplicate guard
    existing = await db.execute(
        select(PersonRelationship).where(
            PersonRelationship.from_person_id == from_id,
            PersonRelationship.to_person_id == to_id,
            PersonRelationship.label_term_id == forward_term_id,
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Relationship already exists")

    # Determine reverse label slug
    term_row = await db.execute(select(Term).where(Term.id == forward_term_id))
    term = term_row.scalars().first()
    reverse_slug = term.reverse_slug if term and term.reverse_slug else label_slug
    reverse_term_id = await resolve_term_slug(db, "relationship-types", reverse_slug)

    # Create both rows
    forward = PersonRelationship(
        from_person_id=from_id,
        to_person_id=to_id,
        label_term_id=forward_term_id,
    )
    inverse = PersonRelationship(
        from_person_id=to_id,
        to_person_id=from_id,
        label_term_id=reverse_term_id,
    )
    db.add(forward)
    db.add(inverse)
    await db.flush()  # assign IDs before linking

    forward.inverse_id = inverse.id
    inverse.inverse_id = forward.id
    db.add(forward)
    db.add(inverse)
    await db.commit()
    await db.refresh(forward)

    return await _build_rel_public(db, forward)


async def get_relationship(
    db: AsyncSession, rel_id: uuid.UUID, owner_id: uuid.UUID
) -> RelationshipPublic | None:
    result = await db.execute(
        select(PersonRelationship).where(PersonRelationship.id == rel_id)
    )
    row = result.scalars().first()
    if not row:
        return None

    # Verify ownership — from_person must belong to owner
    person_result = await db.execute(
        select(Person).where(
            Person.id == row.from_person_id,
            Person.owner_id == owner_id,
        )
    )
    if not person_result.scalars().first():
        return None

    return await _build_rel_public(db, row)


async def list_relationships_for_person(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[RelationshipPublic], int]:
    base = select(PersonRelationship).where(
        PersonRelationship.from_person_id == person_id
    )
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    rows_result = await db.execute(
        base.order_by(PersonRelationship.created_at.desc()).offset(skip).limit(limit)
    )
    rows = rows_result.scalars().all()
    return [await _build_rel_public(db, row) for row in rows], total


async def update_relationship(
    db: AsyncSession,
    rel_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: RelationshipUpdate,
) -> RelationshipPublic | None:
    result = await db.execute(
        select(PersonRelationship).where(PersonRelationship.id == rel_id)
    )
    row = result.scalars().first()
    if not row:
        return None

    # Verify ownership
    person_result = await db.execute(
        select(Person).where(
            Person.id == row.from_person_id,
            Person.owner_id == owner_id,
        )
    )
    if not person_result.scalars().first():
        return None

    new_forward_term_id = await resolve_term_slug(db, "relationship-types", data.label)
    term_row = await db.execute(select(Term).where(Term.id == new_forward_term_id))
    term = term_row.scalars().first()
    reverse_slug = term.reverse_slug if term and term.reverse_slug else data.label
    new_reverse_term_id = await resolve_term_slug(db, "relationship-types", reverse_slug)

    row.label_term_id = new_forward_term_id
    db.add(row)

    if row.inverse_id:
        inv_result = await db.execute(
            select(PersonRelationship).where(PersonRelationship.id == row.inverse_id)
        )
        inverse = inv_result.scalars().first()
        if inverse:
            inverse.label_term_id = new_reverse_term_id
            db.add(inverse)

    await db.commit()
    await db.refresh(row)
    return await _build_rel_public(db, row)


async def delete_relationship(
    db: AsyncSession, rel_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    result = await db.execute(
        select(PersonRelationship).where(PersonRelationship.id == rel_id)
    )
    row = result.scalars().first()
    if not row:
        return False

    # Verify ownership
    person_result = await db.execute(
        select(Person).where(
            Person.id == row.from_person_id,
            Person.owner_id == owner_id,
        )
    )
    if not person_result.scalars().first():
        return False

    inverse_id = row.inverse_id

    # Unlink before deleting to avoid FK constraint issues
    row.inverse_id = None
    db.add(row)
    await db.flush()

    if inverse_id:
        inv_result = await db.execute(
            select(PersonRelationship).where(PersonRelationship.id == inverse_id)
        )
        inverse = inv_result.scalars().first()
        if inverse:
            inverse.inverse_id = None
            db.add(inverse)
            await db.flush()
            await db.delete(inverse)

    await db.delete(row)
    await db.commit()
    return True
