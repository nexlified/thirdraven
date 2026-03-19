from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.crud.vocabulary import (
    create_term,
    create_vocabulary,
    delete_term,
    delete_vocabulary,
    get_term_by_slug,
    get_vocabulary_by_machine_name,
    list_terms,
    list_vocabularies,
    update_term,
    update_vocabulary,
)
from app.models.user import User
from app.schemas.vocabulary import (
    TermCreate,
    TermPublic,
    TermUpdate,
    VocabularyCreate,
    VocabularyPublic,
    VocabularyUpdate,
)

router = APIRouter(prefix="/vocabularies", tags=["vocabularies"])


# ── Vocabulary endpoints ────────────────────────────────────────────────────────


@router.get("/", response_model=list[VocabularyPublic])
async def list_all_vocabularies(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
):
    return await list_vocabularies(db, skip=skip, limit=limit)


@router.post("/", response_model=VocabularyPublic, status_code=status.HTTP_201_CREATED)
async def create_vocab(
    data: VocabularyCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_vocabulary(db, data)


@router.get("/{machine_name}", response_model=VocabularyPublic)
async def get_vocab(
    machine_name: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    vocab = await get_vocabulary_by_machine_name(db, machine_name)
    if not vocab:
        raise HTTPException(status_code=404, detail="Vocabulary not found")
    return vocab


@router.patch("/{machine_name}", response_model=VocabularyPublic)
async def patch_vocab(
    machine_name: str,
    data: VocabularyUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    vocab = await update_vocabulary(db, machine_name, data)
    if not vocab:
        raise HTTPException(status_code=404, detail="Vocabulary not found")
    return vocab


@router.delete("/{machine_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vocab(
    machine_name: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await delete_vocabulary(db, machine_name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Vocabulary not found")


# ── Term endpoints ──────────────────────────────────────────────────────────────


@router.get("/{machine_name}/terms", response_model=list[TermPublic])
async def list_vocab_terms(
    machine_name: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    parent: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 200,
):
    return await list_terms(
        db, machine_name, skip=skip, limit=limit, parent_slug=parent, search=search
    )


@router.post(
    "/{machine_name}/terms",
    response_model=TermPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_vocab_term(
    machine_name: str,
    data: TermCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await create_term(db, machine_name, data)


@router.get("/{machine_name}/terms/{slug}", response_model=TermPublic)
async def get_vocab_term(
    machine_name: str,
    slug: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    term = await get_term_by_slug(db, machine_name, slug)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    return term


@router.patch("/{machine_name}/terms/{slug}", response_model=TermPublic)
async def patch_vocab_term(
    machine_name: str,
    slug: str,
    data: TermUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    term = await update_term(db, machine_name, slug, data)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    return term


@router.delete("/{machine_name}/terms/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vocab_term(
    machine_name: str,
    slug: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await delete_term(db, machine_name, slug)
    if not deleted:
        raise HTTPException(status_code=404, detail="Term not found")
