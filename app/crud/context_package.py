import uuid
from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.followup import list_followups
from app.crud.goal import list_goals
from app.crud.life_event import list_life_events_for_person, list_significant_dates
from app.crud.observation import list_observations
from app.crud.organization import list_person_orgs
from app.crud.person import _build_person_slim, get_person
from app.crud.person_relationship import list_relationships_for_person
from app.models.interaction import Interaction
from app.models.person import Person
from app.models.person_extensions import PersonContext
from app.schemas.context_package import ContextPackage, RelationshipHealthEntry
from app.schemas.interaction import InteractionPublicRead


async def get_context_package(
    db: AsyncSession,
    person_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> ContextPackage | None:
    person = await get_person(db, person_id, owner_id, include=["all"])
    if not person:
        return None

    relationships, _ = await list_relationships_for_person(db, person_id, owner_id)

    organizations = await list_person_orgs(db, person_id)

    interactions_result = await db.execute(
        select(Interaction)
        .where(
            Interaction.person_id == person_id,
            Interaction.owner_id == owner_id,
        )
        .order_by(Interaction.occurred_on.desc().nulls_last())
        .limit(10)
    )
    recent_interactions = [
        InteractionPublicRead.model_validate(row)
        for row in interactions_result.scalars().all()
    ]

    today = date.today()
    cutoff = today + timedelta(days=90)
    all_dates = await list_significant_dates(db, person_id)
    upcoming_dates = [
        d
        for d in all_dates
        if d.month is not None
        and d.day is not None
        and _next_occurrence(d.month, d.day, today) <= cutoff
    ]

    life_events_list, _ = await list_life_events_for_person(
        db, person_id, owner_id, limit=10
    )
    life_events = life_events_list

    observations = await list_observations(
        db, person_id, owner_id, include_sensitive=True, limit=20
    )

    pending_follow_ups = await list_followups(
        db, person_id, owner_id, pending_only=True
    )

    goals = await list_goals(db, person_id, owner_id, active_only=True)

    return ContextPackage(
        person=person,
        relationships=relationships,
        organizations=organizations,
        recent_interactions=recent_interactions,
        upcoming_dates=upcoming_dates,
        life_events=life_events,
        observations=observations,
        pending_follow_ups=pending_follow_ups,
        goals=goals,
        generated_at=datetime.utcnow(),
    )


def _next_occurrence(month: int, day: int, today: date) -> date:
    """Return the next calendar occurrence of (month, day) on or after today."""
    try:
        candidate = date(today.year, month, day)
    except ValueError:
        # e.g. Feb 29 in non-leap year — push to Mar 1
        candidate = date(today.year, month + 1, 1)
    if candidate < today:
        try:
            candidate = date(today.year + 1, month, day)
        except ValueError:
            candidate = date(today.year + 1, month + 1, 1)
    return candidate


# ── Relationship Health ────────────────────────────────────────────────────────


async def get_relationship_health(
    db: AsyncSession, owner_id: uuid.UUID
) -> list[RelationshipHealthEntry]:
    persons_result = await db.execute(
        select(Person).where(
            Person.owner_id == owner_id,
            Person.deleted_at.is_(None),
        )
    )
    persons = persons_result.scalars().all()

    today = date.today()
    entries: list[RelationshipHealthEntry] = []

    for person in persons:
        ctx_result = await db.execute(
            select(PersonContext).where(PersonContext.person_id == person.id)
        )
        ctx = ctx_result.scalars().first()

        last_contacted_on: date | None = ctx.last_contacted_on if ctx else None
        contact_frequency_days: int | None = ctx.contact_frequency_days if ctx else None

        days_since_contact: int | None = None
        if last_contacted_on:
            days_since_contact = (today - last_contacted_on).days

        days_overdue: int | None = None
        if contact_frequency_days and days_since_contact is not None:
            days_overdue = days_since_contact - contact_frequency_days

        if (
            last_contacted_on is None
            or contact_frequency_days is None
            or days_overdue is None
        ):
            health_status = "no-data"
        elif days_overdue > 0:
            health_status = "overdue"
        elif days_overdue > -7:
            health_status = "due-soon"
        else:
            health_status = "on-track"

        person_slim = await _build_person_slim(db, person)
        entries.append(
            RelationshipHealthEntry(
                person=person_slim,
                last_contacted_on=last_contacted_on,
                contact_frequency_days=contact_frequency_days,
                days_since_contact=days_since_contact,
                days_overdue=days_overdue,
                health_status=health_status,
            )
        )

    return entries
