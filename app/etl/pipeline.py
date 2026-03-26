"""ETL pipeline — two entry points: run_import_job and resolve_question."""

import json
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.registry import HANDLER_REGISTRY
from app.integrations.raven import RavenProvider
from app.models.import_job import ImportJob
from app.models.import_row import ImportRow
from app.models.raven_log import RavenLog
from app.models.raven_question import RavenQuestion


async def run_import_job(
    job_id: uuid.UUID,
    db_factory,
    raven: RavenProvider,
) -> None:
    """Process all rows of an ImportJob (called as a BackgroundTask)."""
    async with db_factory() as db:
        job = await db.get(ImportJob, job_id)
        if not job:
            return

        job.status = "processing"
        db.add(job)
        await db.commit()

        handler_cls = HANDLER_REGISTRY.get(job.data_type)
        if handler_cls is None:
            job.status = "failed"
            job.error = f"Unknown data_type: {job.data_type}"
            db.add(job)
            await db.commit()
            return

        handler = handler_cls()
        try:
            rows = await handler.parse(job.raw_data, job.source_format)
        except Exception as exc:
            job.status = "failed"
            job.error = f"Parse error: {exc}"
            db.add(job)
            await db.commit()
            return

        job.total_rows = len(rows)
        db.add(job)
        await db.commit()

        for idx, row in enumerate(rows):
            await _process_row(db, job, handler, raven, row, idx)

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.add(job)
        await db.commit()


async def resolve_question(
    question_id: uuid.UUID,
    db_factory,
    raven: RavenProvider,
) -> None:
    """Re-run a deferred row with the user's answer (called as a BackgroundTask)."""
    async with db_factory() as db:
        question = await db.get(RavenQuestion, question_id)
        if not question or question.status != "answered":
            return

        import_row = await db.get(ImportRow, question.import_row_id)
        if not import_row:
            return

        job = await db.get(ImportJob, import_row.job_id)
        if not job:
            return

        handler_cls = HANDLER_REGISTRY.get(job.data_type)
        if handler_cls is None:
            return

        handler = handler_cls()
        row = json.loads(import_row.raw_snapshot)
        candidates = await handler.find_candidates(db, job.owner_id, row)

        decision = await raven.check_merge(row, candidates, user_answer=question.answer)

        log = RavenLog(
            owner_id=job.owner_id,
            operation="import_recheck",
            input_snapshot=import_row.raw_snapshot,
            candidates_snapshot=json.dumps(candidates, default=str),
            user_answer=question.answer,
            decision=decision.decision,
            reasoning=decision.reasoning,
            target_id=decision.candidate_id,
        )
        db.add(log)
        await db.flush()

        target_id: uuid.UUID | None = None
        if decision.decision == "created":
            target_id = await handler.execute_create(db, job.owner_id, row)
        elif decision.decision == "merged" and decision.candidate_id:
            target_id = await handler.execute_merge(
                db, job.owner_id, decision.candidate_id, row
            )

        final_status = (
            decision.decision
            if decision.decision != "needs_clarification"
            else "flagged"
        )
        import_row.status = final_status
        import_row.target_id = target_id
        import_row.raven_log_id = log.id
        db.add(import_row)

        job.processed_rows = (job.processed_rows or 0) + 1
        db.add(job)
        await db.commit()


# ── Internal helpers ───────────────────────────────────────────────────────────


async def _process_row(
    db: AsyncSession,
    job: ImportJob,
    handler,
    raven: RavenProvider,
    row: dict,
    idx: int,
) -> None:
    raw_snapshot = json.dumps(row, default=str)

    import_row = ImportRow(
        job_id=job.id,
        row_index=idx,
        raw_snapshot=raw_snapshot,
        status="processing",
    )
    db.add(import_row)
    await db.flush()

    try:
        candidates = await handler.find_candidates(db, job.owner_id, row)
        decision = await raven.check_merge(row, candidates)

        if decision.decision == "needs_clarification":
            context_snapshot = json.dumps(
                {"row": row, "candidates": candidates}, default=str
            )
            question = RavenQuestion(
                owner_id=job.owner_id,
                job_id=job.id,
                import_row_id=import_row.id,
                question=decision.question or "Please clarify this record.",
                context_snapshot=context_snapshot,
                status="pending",
            )
            db.add(question)
            import_row.status = "awaiting_answer"
            db.add(import_row)
            await db.commit()
            return

        log = RavenLog(
            owner_id=job.owner_id,
            operation="import_check",
            input_snapshot=raw_snapshot,
            candidates_snapshot=json.dumps(candidates, default=str),
            decision=decision.decision,
            reasoning=decision.reasoning,
            target_id=decision.candidate_id,
        )
        db.add(log)
        await db.flush()

        target_id: uuid.UUID | None = None
        if decision.decision == "created":
            target_id = await handler.execute_create(db, job.owner_id, row)
        elif decision.decision == "merged" and decision.candidate_id:
            target_id = await handler.execute_merge(
                db, job.owner_id, decision.candidate_id, row
            )

        import_row.status = decision.decision
        import_row.target_id = target_id
        import_row.raven_log_id = log.id

    except Exception as exc:
        import_row.status = "error"
        import_row.error_msg = str(exc)

    db.add(import_row)
    job.processed_rows = (job.processed_rows or 0) + 1
    db.add(job)
    await db.commit()
