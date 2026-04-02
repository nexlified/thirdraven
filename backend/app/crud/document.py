import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.vocabulary import resolve_term_slug
from app.models.document import Document
from app.models.vocabulary import Term
from app.schemas.document import DocumentCreate, DocumentPublic, DocumentUpdate
from app.schemas.vocabulary import TermSlim


async def _build(db: AsyncSession, row: Document) -> DocumentPublic:
    r = await db.execute(select(Term).where(Term.id == row.doc_type_id))
    term = r.scalars().first()
    doc_type = (
        TermSlim.model_validate(term)
        if term
        else TermSlim(id=row.doc_type_id, name="", slug="")
    )

    return DocumentPublic(
        id=row.id,
        owner_id=row.owner_id,
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        doc_type=doc_type,
        title=row.title,
        file_path=row.file_path,
        file_name=row.file_name,
        file_size=row.file_size,
        mime_type=row.mime_type,
        issued_on=row.issued_on,
        expires_on=row.expires_on,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _resolve_fields(db: AsyncSession, raw: dict) -> dict:
    result = {}
    for k, v in raw.items():
        if k == "doc_type":
            result["doc_type_id"] = await resolve_term_slug(db, "document-types", v)
        else:
            result[k] = v
    return result


async def create_document(
    db: AsyncSession, owner_id: uuid.UUID, data: DocumentCreate
) -> DocumentPublic:
    db_fields = await _resolve_fields(db, data.model_dump(exclude_unset=True))
    row = Document(owner_id=owner_id, **db_fields)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build(db, row)


async def get_document(
    db: AsyncSession, doc_id: uuid.UUID, owner_id: uuid.UUID
) -> DocumentPublic | None:
    r = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    return await _build(db, row) if row else None


async def list_documents(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
) -> tuple[list[DocumentPublic], int]:
    base = select(Document).where(Document.owner_id == owner_id)
    if entity_type is not None:
        base = base.where(Document.entity_type == entity_type)
    if entity_id is not None:
        base = base.where(Document.entity_id == entity_id)
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    r = await db.execute(
        base.order_by(Document.created_at.desc()).offset(skip).limit(limit)
    )
    return [await _build(db, row) for row in r.scalars().all()], total


async def update_document(
    db: AsyncSession,
    doc_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: DocumentUpdate,
) -> DocumentPublic | None:
    r = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return None
    db_fields = await _resolve_fields(db, data.model_dump(exclude_unset=True))
    for field, value in db_fields.items():
        setattr(row, field, value)
    row.updated_at = datetime.utcnow()
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build(db, row)


async def delete_document(
    db: AsyncSession, doc_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    r = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True
