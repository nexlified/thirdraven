import uuid
from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.vocabulary import resolve_optional_term_slug
from app.models.communication import Communication
from app.models.interaction import Interaction
from app.models.person import Person
from app.models.person_extensions import (
    PersonContext,
    PersonProfessional,
    PersonSocial,
)
from app.schemas.communication import CommCreate, CommIngest, CommPublic, CommUpdate

# ── Channel → interaction-types vocab slug ─────────────────────────────────────

_CHANNEL_TO_INTERACTION_TYPE: dict[str, str] = {
    "email": "email",
    "whatsapp": "text-sms",
    "sms": "text-sms",
    "phone-call": "phone-call",
    "telegram": "text-sms",
    "twitter": "social-media",
    "x": "social-media",
    "instagram": "social-media",
    "linkedin": "social-media",
    "discord": "text-sms",
    "slack": "text-sms",
    "signal": "text-sms",
}

# ── Person matching ────────────────────────────────────────────────────────────


async def _match_person(
    db: AsyncSession,
    owner_id: uuid.UUID,
    channel: str,
    sender_identifier: str | None,
) -> uuid.UUID | None:
    if not sender_identifier:
        return None

    if channel == "email":
        r = await db.execute(
            select(Person).where(
                Person.owner_id == owner_id,
                Person.email == sender_identifier,
                Person.deleted_at.is_(None),
            )
        )
        person = r.scalars().first()
        return person.id if person else None

    if channel in ("whatsapp", "sms", "phone-call"):
        r = await db.execute(
            select(Person).where(
                Person.owner_id == owner_id,
                Person.phone == sender_identifier,
                Person.deleted_at.is_(None),
            )
        )
        person = r.scalars().first()
        return person.id if person else None

    if channel == "telegram":
        r = await db.execute(
            select(Person)
            .join(PersonSocial, PersonSocial.person_id == Person.id)
            .where(
                Person.owner_id == owner_id,
                PersonSocial.telegram_handle == sender_identifier,
                Person.deleted_at.is_(None),
            )
        )
        person = r.scalars().first()
        return person.id if person else None

    if channel in ("twitter", "x"):
        r = await db.execute(
            select(Person)
            .join(PersonSocial, PersonSocial.person_id == Person.id)
            .where(
                Person.owner_id == owner_id,
                PersonSocial.twitter_handle == sender_identifier,
                Person.deleted_at.is_(None),
            )
        )
        person = r.scalars().first()
        return person.id if person else None

    if channel == "discord":
        r = await db.execute(
            select(Person)
            .join(PersonSocial, PersonSocial.person_id == Person.id)
            .where(
                Person.owner_id == owner_id,
                PersonSocial.discord_handle == sender_identifier,
                Person.deleted_at.is_(None),
            )
        )
        person = r.scalars().first()
        return person.id if person else None

    if channel == "instagram":
        r = await db.execute(
            select(Person)
            .join(PersonSocial, PersonSocial.person_id == Person.id)
            .where(
                Person.owner_id == owner_id,
                PersonSocial.instagram_handle == sender_identifier,
                Person.deleted_at.is_(None),
            )
        )
        person = r.scalars().first()
        return person.id if person else None

    if channel == "linkedin":
        r = await db.execute(
            select(Person)
            .join(PersonProfessional, PersonProfessional.person_id == Person.id)
            .where(
                Person.owner_id == owner_id,
                PersonProfessional.linkedin_url == sender_identifier,
                Person.deleted_at.is_(None),
            )
        )
        person = r.scalars().first()
        return person.id if person else None

    return None


# ── PersonContext last_contacted_on upsert ────────────────────────────────────


async def _update_last_contacted(
    db: AsyncSession,
    person_id: uuid.UUID,
    communicated_at: datetime | None,
) -> None:
    contacted_date = (
        communicated_at.date() if communicated_at else date.today()
    )
    r = await db.execute(
        select(PersonContext).where(PersonContext.person_id == person_id)
    )
    ctx = r.scalars().first()
    if ctx:
        if ctx.last_contacted_on is None or contacted_date > ctx.last_contacted_on:
            ctx.last_contacted_on = contacted_date
            ctx.updated_at = datetime.utcnow()
            db.add(ctx)
    else:
        db.add(PersonContext(person_id=person_id, last_contacted_on=contacted_date))


# ── Auto-processing pipeline ───────────────────────────────────────────────────


async def _auto_process(
    db: AsyncSession,
    row: Communication,
    owner_id: uuid.UUID,
) -> None:
    person_id = await _match_person(
        db, owner_id, row.channel, row.sender_identifier
    )
    if not person_id:
        row.status = "unmatched"
        return

    # Resolve interaction type from channel
    type_slug = _CHANNEL_TO_INTERACTION_TYPE.get(row.channel, "other")
    interaction_type_id = await resolve_optional_term_slug(
        db, "interaction-types", type_slug
    )

    # Build interaction title
    if row.subject:
        title = row.subject
    else:
        sender = row.sender_identifier or "unknown"
        title = f"{row.channel} message from {sender}"

    occurred_on = row.communicated_at.date() if row.communicated_at else date.today()
    notes = (row.body[:2000] if row.body and len(row.body) > 2000 else row.body)

    interaction = Interaction(
        person_id=person_id,
        owner_id=owner_id,
        interaction_type_id=interaction_type_id,
        title=title,
        occurred_on=occurred_on,
        notes=notes,
    )
    db.add(interaction)
    await db.flush()

    row.person_id = person_id
    row.interaction_id = interaction.id
    row.status = "matched"
    row.processed_at = datetime.utcnow()

    await _update_last_contacted(db, person_id, row.communicated_at)


# ── CRUD ───────────────────────────────────────────────────────────────────────


async def ingest_communication(
    db: AsyncSession,
    owner_id: uuid.UUID,
    data: CommIngest,
) -> CommPublic:
    raw_payload = data.build_raw_payload()
    row = Communication(
        owner_id=owner_id,
        channel=data.channel,
        direction=data.direction,
        sender_identifier=data.sender,
        recipient_identifiers=data.recipients,
        source_app=data.source_app,
        external_id=data.external_id,
        thread_id=data.thread_id,
        subject=data.subject,
        body=data.body,
        communicated_at=data.communicated_at,
        raw_payload=raw_payload,
    )
    db.add(row)
    await db.flush()
    await _auto_process(db, row, owner_id)
    await db.commit()
    await db.refresh(row)
    return CommPublic.model_validate(row)


async def create_communication(
    db: AsyncSession,
    owner_id: uuid.UUID,
    data: CommCreate,
) -> CommPublic:
    row = Communication(
        owner_id=owner_id,
        **data.model_dump(exclude_unset=True),
    )
    db.add(row)
    await db.flush()
    await _auto_process(db, row, owner_id)
    await db.commit()
    await db.refresh(row)
    return CommPublic.model_validate(row)


async def get_communication(
    db: AsyncSession, comm_id: uuid.UUID, owner_id: uuid.UUID
) -> CommPublic | None:
    r = await db.execute(
        select(Communication).where(
            Communication.id == comm_id,
            Communication.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    return CommPublic.model_validate(row) if row else None


async def list_communications(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    channel: str | None = None,
    status: str | None = None,
    person_id: uuid.UUID | None = None,
) -> tuple[list[CommPublic], int]:
    base = select(Communication).where(Communication.owner_id == owner_id)
    if channel:
        base = base.where(Communication.channel == channel)
    if status:
        base = base.where(Communication.status == status)
    if person_id:
        base = base.where(Communication.person_id == person_id)
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    r = await db.execute(
        base.order_by(Communication.communicated_at.desc().nulls_last())
        .offset(skip)
        .limit(limit)
    )
    return [CommPublic.model_validate(row) for row in r.scalars().all()], total


async def update_communication(
    db: AsyncSession,
    comm_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: CommUpdate,
) -> CommPublic | None:
    r = await db.execute(
        select(Communication).where(
            Communication.id == comm_id,
            Communication.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    row.updated_at = datetime.utcnow()
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return CommPublic.model_validate(row)


async def delete_communication(
    db: AsyncSession, comm_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    r = await db.execute(
        select(Communication).where(
            Communication.id == comm_id,
            Communication.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True


async def match_communication(
    db: AsyncSession, comm_id: uuid.UUID, owner_id: uuid.UUID
) -> CommPublic | None:
    """Re-attempt auto-matching. If person_id is already set, use it directly."""
    r = await db.execute(
        select(Communication).where(
            Communication.id == comm_id,
            Communication.owner_id == owner_id,
        )
    )
    row = r.scalars().first()
    if not row:
        return None
    # Reset to raw so _auto_process can re-run cleanly
    row.status = "raw"
    row.processed_at = None
    row.interaction_id = None
    # If user manually set person_id, use it as the match target
    if row.person_id:
        # Manually linked — just create the interaction
        type_slug = _CHANNEL_TO_INTERACTION_TYPE.get(row.channel, "other")
        interaction_type_id = await resolve_optional_term_slug(
            db, "interaction-types", type_slug
        )
        sender = row.sender_identifier or "unknown"
        title = row.subject or f"{row.channel} message from {sender}"
        occurred_on = (
            row.communicated_at.date() if row.communicated_at else date.today()
        )
        notes = (row.body[:2000] if row.body and len(row.body) > 2000 else row.body)
        interaction = Interaction(
            person_id=row.person_id,
            owner_id=owner_id,
            interaction_type_id=interaction_type_id,
            title=title,
            occurred_on=occurred_on,
            notes=notes,
        )
        db.add(interaction)
        await db.flush()
        row.interaction_id = interaction.id
        row.status = "matched"
        row.processed_at = datetime.utcnow()
        await _update_last_contacted(db, row.person_id, row.communicated_at)
    else:
        await _auto_process(db, row, owner_id)
    await db.commit()
    await db.refresh(row)
    return CommPublic.model_validate(row)
