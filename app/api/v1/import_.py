"""Import job endpoints."""

import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import AsyncSessionLocal, get_session
from app.core.deps import get_current_user, get_raven
from app.etl.pipeline import run_import_job
from app.etl.registry import HANDLER_REGISTRY
from app.integrations.raven import RavenProvider
from app.models.import_job import ImportJob
from app.models.import_row import ImportRow
from app.models.raven_question import RavenQuestion
from app.models.user import User
from app.schemas.import_ import ImportJobDetail, ImportJobPublic, ImportRowPublic

router = APIRouter(prefix="/import", tags=["import"])


@router.post(
    "/jobs",
    response_model=ImportJobPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_import_job(
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    raven: Annotated[RavenProvider, Depends(get_raven)],
    file: Annotated[UploadFile, File()],
    data_type: Annotated[str, Form()],
    source_format: Annotated[str, Form()] = "csv",
):
    if data_type not in HANDLER_REGISTRY:
        valid = list(HANDLER_REGISTRY)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported data_type '{data_type}'. Valid options: {valid}",
        )

    raw_data = (await file.read()).decode("utf-8")

    job = ImportJob(
        owner_id=current_user.id,
        data_type=data_type,
        source_format=source_format,
        raw_data=raw_data,
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(run_import_job, job.id, AsyncSessionLocal, raven)

    return ImportJobPublic(
        id=job.id,
        data_type=job.data_type,
        status=job.status,
        total_rows=job.total_rows,
        processed_rows=job.processed_rows,
        pending_questions=0,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.get("/jobs", response_model=list[ImportJobPublic])
async def list_import_jobs(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 50,
):
    result = await db.execute(
        select(ImportJob)
        .where(ImportJob.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(ImportJob.created_at.desc())
    )
    jobs = result.scalars().all()
    out = []
    for job in jobs:
        pq = await _count_pending_questions(db, job.id)
        out.append(_job_to_public(job, pq))
    return out


@router.get("/jobs/{job_id}", response_model=ImportJobDetail)
async def get_import_job(
    job_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    job = await db.get(ImportJob, job_id)
    if not job or job.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Import job not found")

    rows_result = await db.execute(
        select(ImportRow)
        .where(ImportRow.job_id == job_id)
        .order_by(ImportRow.row_index)
    )
    rows = [ImportRowPublic.model_validate(r) for r in rows_result.scalars().all()]
    pq = await _count_pending_questions(db, job_id)

    return ImportJobDetail(**_job_to_public(job, pq).model_dump(), rows=rows)


# ── Helpers ────────────────────────────────────────────────────────────────────


async def _count_pending_questions(db: AsyncSession, job_id: uuid.UUID) -> int:
    result = await db.execute(
        select(RavenQuestion).where(
            RavenQuestion.job_id == job_id,
            RavenQuestion.status == "pending",
        )
    )
    return len(result.scalars().all())


def _job_to_public(job: ImportJob, pending_questions: int) -> ImportJobPublic:
    return ImportJobPublic(
        id=job.id,
        data_type=job.data_type,
        status=job.status,
        total_rows=job.total_rows,
        processed_rows=job.processed_rows,
        pending_questions=pending_questions,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )
