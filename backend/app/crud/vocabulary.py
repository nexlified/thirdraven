import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.vocabulary import Term, Vocabulary
from app.schemas.vocabulary import (
    TermCreate,
    TermUpdate,
    VocabularyCreate,
    VocabularyUpdate,
)

# ── Resolver helpers ───────────────────────────────────────────────────────────


async def resolve_term_slug(
    db: AsyncSession, machine_name: str, slug: str
) -> uuid.UUID:
    """Resolve vocab machine_name + term slug → term.id.

    Raises HTTP 422 if not found.
    """
    result = await db.execute(
        select(Term)
        .join(Vocabulary, Term.vocabulary_id == Vocabulary.id)
        .where(
            Vocabulary.machine_name == machine_name,
            Term.slug == slug,
            Term.is_active.is_(True),
        )
    )
    term = result.scalars().first()
    if not term:
        raise HTTPException(
            status_code=422,
            detail=f"Term '{slug}' not found in vocabulary '{machine_name}'",
        )
    return term.id


async def resolve_optional_term_slug(
    db: AsyncSession, machine_name: str, slug: str | None
) -> uuid.UUID | None:
    """Like resolve_term_slug but returns None if slug is None."""
    if slug is None:
        return None
    return await resolve_term_slug(db, machine_name, slug)


# ── Vocabulary CRUD ────────────────────────────────────────────────────────────


async def list_vocabularies(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[Vocabulary]:
    result = await db.execute(
        select(Vocabulary)
        .where(Vocabulary.is_active.is_(True))
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_vocabulary(db: AsyncSession, data: VocabularyCreate) -> Vocabulary:
    vocab = Vocabulary(**data.model_dump())
    db.add(vocab)
    await db.commit()
    await db.refresh(vocab)
    return vocab


async def get_vocabulary_by_machine_name(
    db: AsyncSession, machine_name: str
) -> Vocabulary | None:
    result = await db.execute(
        select(Vocabulary).where(Vocabulary.machine_name == machine_name)
    )
    return result.scalars().first()


async def update_vocabulary(
    db: AsyncSession, machine_name: str, data: VocabularyUpdate
) -> Vocabulary | None:
    vocab = await get_vocabulary_by_machine_name(db, machine_name)
    if not vocab:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(vocab, field, value)
    db.add(vocab)
    await db.commit()
    await db.refresh(vocab)
    return vocab


async def delete_vocabulary(db: AsyncSession, machine_name: str) -> bool:
    vocab = await get_vocabulary_by_machine_name(db, machine_name)
    if not vocab:
        return False
    if vocab.is_locked:
        raise HTTPException(
            status_code=409,
            detail=f"Vocabulary '{machine_name}' is locked and cannot be deleted",
        )
    await db.delete(vocab)
    await db.commit()
    return True


# ── Term CRUD ──────────────────────────────────────────────────────────────────


async def list_terms(
    db: AsyncSession,
    machine_name: str,
    skip: int = 0,
    limit: int = 200,
    parent_slug: str | None = None,
    search: str | None = None,
) -> list[Term]:
    vocab = await get_vocabulary_by_machine_name(db, machine_name)
    if not vocab:
        return []
    query = select(Term).where(
        Term.vocabulary_id == vocab.id,
        Term.is_active.is_(True),
    )
    if parent_slug is not None:
        parent_result = await db.execute(
            select(Term).where(
                Term.vocabulary_id == vocab.id,
                Term.slug == parent_slug,
            )
        )
        parent = parent_result.scalars().first()
        if parent:
            query = query.where(Term.parent_id == parent.id)
        else:
            return []
    if search:
        query = query.where(Term.name.ilike(f"%{search}%"))
    query = query.order_by(Term.weight, Term.name)
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def create_term(db: AsyncSession, machine_name: str, data: TermCreate) -> Term:
    vocab = await get_vocabulary_by_machine_name(db, machine_name)
    if not vocab:
        raise HTTPException(
            status_code=404,
            detail=f"Vocabulary '{machine_name}' not found",
        )
    term = Term(
        vocabulary_id=vocab.id,
        name=data.name,
        slug=data.slug,
        description=data.description,
        parent_id=data.parent_id,
        weight=data.weight,
        external_id=data.external_id,
        metadata_=data.metadata_,
        icon=data.icon,
    )
    db.add(term)
    await db.commit()
    await db.refresh(term)
    return term


async def get_term_by_slug(
    db: AsyncSession, machine_name: str, slug: str
) -> Term | None:
    result = await db.execute(
        select(Term)
        .join(Vocabulary, Term.vocabulary_id == Vocabulary.id)
        .where(
            Vocabulary.machine_name == machine_name,
            Term.slug == slug,
        )
    )
    return result.scalars().first()


async def update_term(
    db: AsyncSession, machine_name: str, slug: str, data: TermUpdate
) -> Term | None:
    term = await get_term_by_slug(db, machine_name, slug)
    if not term:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(term, field, value)
    db.add(term)
    await db.commit()
    await db.refresh(term)
    return term


async def delete_term(db: AsyncSession, machine_name: str, slug: str) -> bool:
    term = await get_term_by_slug(db, machine_name, slug)
    if not term:
        return False
    await db.delete(term)
    await db.commit()
    return True
