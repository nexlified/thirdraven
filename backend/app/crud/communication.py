import uuid
from datetime import UTC, date, datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.vocabulary import resolve_optional_term_slug
from app.models.communication import Communication
from app.models.interaction import Interaction
from app.models.person import Person
from app.models.person_extensions import (
    PersonChannel,
    PersonContext,
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
) -> Person | None:
    """Return the matching known Person, or None if not found."""
    if not sender_identifier:
        return None

    # Map incoming channel name to PersonChannel type values to check
    if channel == "email":
        channel_types = ["email"]
    elif channel in ("whatsapp", "sms", "phone-call"):
        channel_types = ["mobile", "phone"]
    else:
        # For all other channels (telegram, twitter, discord, instagram, linkedin, etc.)
        # the channel name matches the PersonChannel.type directly
        channel_types = [channel]

    r = await db.execute(
        select(Person)
        .join(PersonChannel, PersonChannel.person_id == Person.id)
        .where(
            Person.owner_id == owner_id,
            PersonChannel.type.in_(channel_types),
            PersonChannel.value == sender_identifier,
            Person.deleted_at.is_(None),
        )
    )
    return r.scalars().first()


def _derive_first_name(channel: str, sender_identifier: str) -> str:
    """Derive a human-readable first_name from a raw sender identifier."""
    if channel == "email" and "@" in sender_identifier:
        return sender_identifier.split("@")[0]
    return sender_identifier


# ── PersonContext last_contacted_on upsert ────────────────────────────────────


async def _update_last_contacted(
    db: AsyncSession,
    person_id: uuid.UUID,
    communicated_at: datetime | None,
) -> None:
    contacted_date = communicated_at.date() if communicated_at else date.today()
    r = await db.execute(
        select(PersonContext).where(PersonContext.person_id == person_id)
    )
    ctx = r.scalars().first()
    if ctx:
        if ctx.last_contacted_on is None or contacted_date > ctx.last_contacted_on:
            ctx.last_contacted_on = contacted_date
            ctx.updated_at = datetime.now(UTC)
            db.add(ctx)
    else:
        db.add(PersonContext(person_id=person_id, last_contacted_on=contacted_date))


# ── Auto-processing pipeline ───────────────────────────────────────────────────


async def _create_interaction_for_person(
    db: AsyncSession,
    row: Communication,
    owner_id: uuid.UUID,
    person_id: uuid.UUID,
) -> Interaction:
    """Create and flush an Interaction linked to the given person."""
    type_slug = _CHANNEL_TO_INTERACTION_TYPE.get(row.channel, "other")
    interaction_type_id = await resolve_optional_term_slug(
        db, "interaction-types", type_slug
    )
    sender = row.sender_identifier or "unknown"
    title = row.subject or f"{row.channel} message from {sender}"
    occurred_on = row.communicated_at.date() if row.communicated_at else date.today()
    notes = row.body[:2000] if row.body and len(row.body) > 2000 else row.body
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
    return interaction


async def _auto_process(
    db: AsyncSession,
    row: Communication,
    owner_id: uuid.UUID,
) -> None:
    person = await _match_person(db, owner_id, row.channel, row.sender_identifier)

    if person:
        # Known person matched
        if person.is_bot:
            row.is_bot = True
        interaction = await _create_interaction_for_person(db, row, owner_id, person.id)
        row.person_id = person.id
        row.interaction_id = interaction.id
        row.status = "matched"
        row.processed_at = datetime.now(UTC)
        await _update_last_contacted(db, person.id, row.communicated_at)
        return

    if row.sender_identifier:
        # Unknown sender — create a placeholder person
        first_name = _derive_first_name(row.channel, row.sender_identifier)
        placeholder = Person(
            owner_id=owner_id,
            first_name=first_name,
            is_placeholder=True,
        )
        db.add(placeholder)
        await db.flush()
        # Create channel entry for the sender identifier
        if row.channel == "email":
            ch_type = "email"
        elif row.channel in ("whatsapp", "sms", "phone-call"):
            ch_type = "mobile"
        else:
            ch_type = row.channel
        db.add(
            PersonChannel(
                person_id=placeholder.id,
                owner_id=owner_id,
                value=row.sender_identifier,
                type=ch_type,
                is_primary=True,
            )
        )
        interaction = await _create_interaction_for_person(
            db, row, owner_id, placeholder.id
        )
        row.person_id = placeholder.id
        row.interaction_id = interaction.id
        row.status = "placeholder"
        row.processed_at = datetime.now(UTC)
        await _update_last_contacted(db, placeholder.id, row.communicated_at)
        return

    # No sender identifier at all — cannot create a person
    row.status = "unmatched"


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
    is_bot: bool | None = None,
    context: str | None = None,
) -> tuple[list[CommPublic], int]:
    base = select(Communication).where(Communication.owner_id == owner_id)
    if channel:
        base = base.where(Communication.channel == channel)
    if status:
        base = base.where(Communication.status == status)
    if person_id:
        base = base.where(Communication.person_id == person_id)
    if is_bot is not None:
        base = base.where(Communication.is_bot == is_bot)
    if context is not None:
        base = base.where(Communication.context == context)
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
    row.updated_at = datetime.now(UTC)
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
        notes = row.body[:2000] if row.body and len(row.body) > 2000 else row.body
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
        row.processed_at = datetime.now(UTC)
        await _update_last_contacted(db, row.person_id, row.communicated_at)
    else:
        await _auto_process(db, row, owner_id)
    await db.commit()
    await db.refresh(row)
    return CommPublic.model_validate(row)
