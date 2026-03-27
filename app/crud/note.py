import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.vocabulary import resolve_term_slug
from app.models.note import Note, NoteTag
from app.models.vocabulary import Term
from app.schemas.note import NoteCreate, NotePublicRead, NoteUpdate
from app.schemas.vocabulary import TermSlim

# ── Tag helpers ────────────────────────────────────────────────────────────────


async def _get_note_tags(db: AsyncSession, note_id: uuid.UUID) -> list[TermSlim]:
    result = await db.execute(
        select(Term)
        .join(NoteTag, Term.id == NoteTag.term_id)
        .where(NoteTag.note_id == note_id, Term.is_active.is_(True))
        .order_by(Term.name)
    )
    return [TermSlim.model_validate(t) for t in result.scalars().all()]


async def _set_note_tags(
    db: AsyncSession, note_id: uuid.UUID, tag_slugs: list[str]
) -> None:
    existing = await db.execute(select(NoteTag).where(NoteTag.note_id == note_id))
    for row in existing.scalars().all():
        await db.delete(row)
    for slug in tag_slugs:
        term_id = await resolve_term_slug(db, "note-tags", slug)
        db.add(NoteTag(note_id=note_id, term_id=term_id))


async def _build_note_public(db: AsyncSession, note: Note) -> NotePublicRead:
    tags = await _get_note_tags(db, note.id)
    return NotePublicRead(
        id=note.id,
        owner_id=note.owner_id,
        title=note.title,
        body=note.body,
        pinned=note.pinned,
        person_id=note.person_id,
        asset_id=note.asset_id,
        subscription_id=note.subscription_id,
        tags=tags,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


# ── CRUD ───────────────────────────────────────────────────────────────────────


async def create_note(
    db: AsyncSession, owner_id: uuid.UUID, data: NoteCreate
) -> NotePublicRead:
    raw = data.model_dump(exclude_unset=True)
    tag_slugs = raw.pop("tags", [])

    note = Note(owner_id=owner_id, **raw)
    db.add(note)
    await db.flush()

    for slug in tag_slugs:
        term_id = await resolve_term_slug(db, "note-tags", slug)
        db.add(NoteTag(note_id=note.id, term_id=term_id))

    await db.commit()
    await db.refresh(note)
    return await _build_note_public(db, note)


async def get_note(
    db: AsyncSession, note_id: uuid.UUID, owner_id: uuid.UUID
) -> Note | None:
    result = await db.execute(
        select(Note).where(
            Note.id == note_id,
            Note.owner_id == owner_id,
            Note.deleted_at.is_(None),
        )
    )
    return result.scalars().first()


async def get_note_public(
    db: AsyncSession, note_id: uuid.UUID, owner_id: uuid.UUID
) -> NotePublicRead | None:
    note = await get_note(db, note_id, owner_id)
    if not note:
        return None
    return await _build_note_public(db, note)


async def list_notes(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    pinned: bool | None = None,
    person_id: uuid.UUID | None = None,
    asset_id: uuid.UUID | None = None,
    subscription_id: uuid.UUID | None = None,
) -> tuple[list[NotePublicRead], int]:
    base = select(Note).where(Note.owner_id == owner_id, Note.deleted_at.is_(None))

    if pinned is not None:
        base = base.where(Note.pinned == pinned)
    if person_id is not None:
        base = base.where(Note.person_id == person_id)
    if asset_id is not None:
        base = base.where(Note.asset_id == asset_id)
    if subscription_id is not None:
        base = base.where(Note.subscription_id == subscription_id)

    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    result = await db.execute(
        base.order_by(Note.updated_at.desc()).offset(skip).limit(limit)
    )
    notes = result.scalars().all()
    return [await _build_note_public(db, n) for n in notes], total


async def update_note(
    db: AsyncSession,
    note_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: NoteUpdate,
) -> NotePublicRead | None:
    note = await get_note(db, note_id, owner_id)
    if not note:
        return None

    raw = data.model_dump(exclude_unset=True)
    tag_slugs = raw.pop("tags", None)

    for field, value in raw.items():
        setattr(note, field, value)
    note.updated_at = datetime.utcnow()
    db.add(note)

    if tag_slugs is not None:
        await _set_note_tags(db, note_id, tag_slugs)

    await db.commit()
    await db.refresh(note)
    return await _build_note_public(db, note)


async def soft_delete_note(
    db: AsyncSession, note_id: uuid.UUID, owner_id: uuid.UUID
) -> Note | None:
    note = await get_note(db, note_id, owner_id)
    if not note:
        return None
    note.deleted_at = datetime.utcnow()
    db.add(note)
    await db.commit()
    return note
