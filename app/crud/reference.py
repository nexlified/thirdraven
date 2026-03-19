import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.reference import PersonTerm
from app.schemas.reference import PersonTermCreate


async def add_person_term(
    db: AsyncSession,
    person_id: uuid.UUID,
    data: PersonTermCreate,
) -> PersonTerm:
    pt = PersonTerm(
        person_id=person_id,
        term_id=data.term_id,
        context=data.context,
    )
    db.add(pt)
    await db.commit()
    await db.refresh(pt)
    return pt


async def list_person_terms(db: AsyncSession, person_id: uuid.UUID) -> list[PersonTerm]:
    result = await db.exec(select(PersonTerm).where(PersonTerm.person_id == person_id))
    return list(result.all())


async def remove_person_term(
    db: AsyncSession, person_id: uuid.UUID, term_id: uuid.UUID
) -> bool:
    result = await db.exec(
        select(PersonTerm).where(
            PersonTerm.person_id == person_id,
            PersonTerm.term_id == term_id,
        )
    )
    pt = result.first()
    if not pt:
        return False
    await db.delete(pt)
    await db.commit()
    return True
