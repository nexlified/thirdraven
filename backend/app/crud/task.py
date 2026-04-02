import uuid
from datetime import UTC, date, datetime

from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.vocabulary import resolve_term_slug
from app.models.task import Task, TaskTag
from app.models.vocabulary import Term
from app.schemas.task import TaskCreate, TaskPublicRead, TaskSummary, TaskUpdate
from app.schemas.vocabulary import TermSlim

_DONE_STATUSES = {"done", "cancelled"}

# ── Tag helpers ────────────────────────────────────────────────────────────────


async def _get_task_tags(db: AsyncSession, task_id: uuid.UUID) -> list[TermSlim]:
    result = await db.execute(
        select(Term)
        .join(TaskTag, Term.id == TaskTag.term_id)
        .where(TaskTag.task_id == task_id, Term.is_active.is_(True))
        .order_by(Term.name)
    )
    return [TermSlim.model_validate(t) for t in result.scalars().all()]


async def _set_task_tags(
    db: AsyncSession, task_id: uuid.UUID, tag_slugs: list[str]
) -> None:
    existing = await db.execute(select(TaskTag).where(TaskTag.task_id == task_id))
    for row in existing.scalars().all():
        await db.delete(row)
    for slug in tag_slugs:
        term_id = await resolve_term_slug(db, "task-tags", slug)
        db.add(TaskTag(task_id=task_id, term_id=term_id))


async def _build_task_public(db: AsyncSession, task: Task) -> TaskPublicRead:
    tags = await _get_task_tags(db, task.id)
    return TaskPublicRead(
        id=task.id,
        owner_id=task.owner_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        completed_at=task.completed_at,
        person_id=task.person_id,
        asset_id=task.asset_id,
        subscription_id=task.subscription_id,
        event_id=task.event_id,
        tags=tags,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


# ── CRUD ───────────────────────────────────────────────────────────────────────


async def create_task(
    db: AsyncSession, owner_id: uuid.UUID, data: TaskCreate
) -> TaskPublicRead:
    raw = data.model_dump(exclude_unset=True)
    tag_slugs = raw.pop("tags", [])

    task = Task(owner_id=owner_id, **raw)
    db.add(task)
    await db.flush()

    for slug in tag_slugs:
        term_id = await resolve_term_slug(db, "task-tags", slug)
        db.add(TaskTag(task_id=task.id, term_id=term_id))

    await db.commit()
    await db.refresh(task)
    return await _build_task_public(db, task)


async def get_task(
    db: AsyncSession, task_id: uuid.UUID, owner_id: uuid.UUID
) -> Task | None:
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.owner_id == owner_id,
            Task.deleted_at.is_(None),
        )
    )
    return result.scalars().first()


async def get_task_public(
    db: AsyncSession, task_id: uuid.UUID, owner_id: uuid.UUID
) -> TaskPublicRead | None:
    task = await get_task(db, task_id, owner_id)
    if not task:
        return None
    return await _build_task_public(db, task)


async def list_tasks(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    priority: str | None = None,
    person_id: uuid.UUID | None = None,
    asset_id: uuid.UUID | None = None,
    subscription_id: uuid.UUID | None = None,
    event_id: uuid.UUID | None = None,
    due_before: date | None = None,
    due_after: date | None = None,
    overdue: bool | None = None,
) -> tuple[list[TaskPublicRead], int]:
    base = select(Task).where(Task.owner_id == owner_id, Task.deleted_at.is_(None))

    if status is not None:
        base = base.where(Task.status == status)
    if priority is not None:
        base = base.where(Task.priority == priority)
    if person_id is not None:
        base = base.where(Task.person_id == person_id)
    if asset_id is not None:
        base = base.where(Task.asset_id == asset_id)
    if subscription_id is not None:
        base = base.where(Task.subscription_id == subscription_id)
    if event_id is not None:
        base = base.where(Task.event_id == event_id)
    if due_before is not None:
        base = base.where(Task.due_date <= due_before)
    if due_after is not None:
        base = base.where(Task.due_date >= due_after)
    if overdue is True:
        today = date.today()
        base = base.where(
            Task.due_date < today,
            Task.status.notin_(list(_DONE_STATUSES)),
        )
    elif overdue is False:
        today = date.today()
        base = base.where(
            or_(
                Task.due_date.is_(None),
                Task.due_date >= today,
                Task.status.in_(list(_DONE_STATUSES)),
            )
        )

    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    result = await db.execute(
        base.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    tasks = result.scalars().all()
    return [await _build_task_public(db, t) for t in tasks], total


async def update_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: TaskUpdate,
) -> TaskPublicRead | None:
    task = await get_task(db, task_id, owner_id)
    if not task:
        return None

    raw = data.model_dump(exclude_unset=True)
    tag_slugs = raw.pop("tags", None)

    new_status = raw.get("status")
    if new_status == "done" and task.status != "done":
        task.completed_at = datetime.now(UTC)
    elif new_status is not None and new_status != "done" and task.status == "done":
        task.completed_at = None

    for field, value in raw.items():
        setattr(task, field, value)
    task.updated_at = datetime.now(UTC)
    db.add(task)

    if tag_slugs is not None:
        await _set_task_tags(db, task_id, tag_slugs)

    await db.commit()
    await db.refresh(task)
    return await _build_task_public(db, task)


async def soft_delete_task(
    db: AsyncSession, task_id: uuid.UUID, owner_id: uuid.UUID
) -> Task | None:
    task = await get_task(db, task_id, owner_id)
    if not task:
        return None
    task.deleted_at = datetime.now(UTC)
    db.add(task)
    await db.commit()
    return task


async def get_task_summary(db: AsyncSession, owner_id: uuid.UUID) -> TaskSummary:
    result = await db.execute(
        select(Task).where(Task.owner_id == owner_id, Task.deleted_at.is_(None))
    )
    tasks = result.scalars().all()

    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    overdue = 0
    due_today = 0
    today = date.today()

    for task in tasks:
        by_status[task.status] = by_status.get(task.status, 0) + 1
        by_priority[task.priority] = by_priority.get(task.priority, 0) + 1
        if task.due_date and task.status not in _DONE_STATUSES:
            if task.due_date < today:
                overdue += 1
            elif task.due_date == today:
                due_today += 1

    return TaskSummary(
        total=len(tasks),
        by_status=by_status,
        overdue=overdue,
        due_today=due_today,
        by_priority=by_priority,
    )
