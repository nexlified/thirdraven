"""Raven question (human-in-the-loop) endpoints."""

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import AsyncSessionLocal, get_session
from app.core.deps import get_current_user, get_raven
from app.etl.pipeline import resolve_question
from app.integrations.raven import RavenProvider
from app.models.raven_question import RavenQuestion
from app.models.user import User
from app.schemas.raven_question import RavenAnswerRequest, RavenQuestionPublic

router = APIRouter(prefix="/raven", tags=["raven"])


@router.get("/questions", response_model=list[RavenQuestionPublic])
async def list_questions(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 50,
):
    stmt = (
        select(RavenQuestion)
        .where(RavenQuestion.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(RavenQuestion.created_at.desc())
    )
    if status_filter:
        stmt = stmt.where(RavenQuestion.status == status_filter)

    result = await db.execute(stmt)
    return [RavenQuestionPublic.model_validate(q) for q in result.scalars().all()]


@router.get("/questions/{question_id}", response_model=RavenQuestionPublic)
async def get_question(
    question_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    q = await db.get(RavenQuestion, question_id)
    if not q or q.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Question not found")
    return RavenQuestionPublic.model_validate(q)


@router.post(
    "/questions/{question_id}/answer",
    status_code=status.HTTP_202_ACCEPTED,
)
async def answer_question(
    question_id: uuid.UUID,
    body: RavenAnswerRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    raven: Annotated[RavenProvider, Depends(get_raven)],
):
    q = await db.get(RavenQuestion, question_id)
    if not q or q.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Question not found")
    if q.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Question already answered",
        )

    q.answer = body.answer
    q.status = "answered"
    q.answered_at = datetime.now(UTC)
    db.add(q)
    await db.commit()

    background_tasks.add_task(resolve_question, question_id, AsyncSessionLocal, raven)

    return {"detail": "Answer accepted, processing in background."}
