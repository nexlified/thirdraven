import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import PaginationParams, get_current_user
from app.crud.document import (
    create_document,
    delete_document,
    get_document,
    list_documents,
    update_document,
)
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentPublic, DocumentUpdate
from app.schemas.paginated import Paginated

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", response_model=DocumentPublic, status_code=status.HTTP_201_CREATED)
async def create(
    data: DocumentCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_document(db, current_user.id, data)


@router.get("/", response_model=Paginated[DocumentPublic])
async def list_all(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
):
    items, total = await list_documents(
        db,
        current_user.id,
        skip=pagination.skip,
        limit=pagination.limit,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return Paginated(
        items=items, total=total, skip=pagination.skip, limit=pagination.limit
    )


@router.get("/{doc_id}", response_model=DocumentPublic)
async def get_one(
    doc_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    doc = await get_document(db, doc_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.patch("/{doc_id}", response_model=DocumentPublic)
async def patch(
    doc_id: uuid.UUID,
    data: DocumentUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    doc = await update_document(db, doc_id, current_user.id, data)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    doc_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await delete_document(db, doc_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
