import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.interaction import Interaction
from app.models.vocabulary import Term
from app.schemas.interaction import InteractionCreate, InteractionUpdate


async def create_interaction(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: InteractionCreate,
) -> Interaction:
    interaction = Interaction(
        person_id=person_id,
        owner_id=owner_id,
        **data.model_dump(),
    )
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)
    return interaction


async def get_interaction(
    db: AsyncSession, interaction_id: uuid.UUID, owner_id: uuid.UUID
) -> Interaction | None:
    result = await db.execute(
        select(Interaction).where(
            Interaction.id == interaction_id,
            Interaction.owner_id == owner_id,
        )
    )
    return result.scalars().first()


async def list_interactions(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    type_slug: str | None = None,
    context: str | None = None,
) -> tuple[list[Interaction], int]:
    base = select(Interaction).where(
        Interaction.person_id == person_id,
        Interaction.owner_id == owner_id,
    )
    if type_slug:
        base = base.join(
            Term,
            Interaction.interaction_type_id == Term.id,
        ).where(Term.slug == type_slug)
    if context is not None:
        base = base.where(Interaction.context == context)
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    result = await db.execute(
        base.order_by(Interaction.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all()), total


async def update_interaction(
    db: AsyncSession,
    interaction_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: InteractionUpdate,
) -> Interaction | None:
    interaction = await get_interaction(db, interaction_id, owner_id)
    if not interaction:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(interaction, field, value)
    interaction.updated_at = datetime.utcnow()
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)
    return interaction


async def delete_interaction(
    db: AsyncSession, interaction_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    interaction = await get_interaction(db, interaction_id, owner_id)
    if not interaction:
        return False
    await db.delete(interaction)
    await db.commit()
    return True
