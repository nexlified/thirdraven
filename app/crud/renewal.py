import uuid
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.subscription import Subscription
from app.models.tracked_record import TrackedRecord
from app.models.vocabulary import Term
from app.schemas.renewal import RenewalEntry


async def get_upcoming_renewals(
    db: AsyncSession,
    owner_id: uuid.UUID,
    days: int = 30,
) -> list[RenewalEntry]:
    today = date.today()
    cutoff = today + timedelta(days=days)
    entries: list[RenewalEntry] = []

    # ── Tracked records with expires_on in window ──────────────────────────────
    tr_result = await db.execute(
        select(TrackedRecord).where(
            TrackedRecord.owner_id == owner_id,
            TrackedRecord.deleted_at.is_(None),
            TrackedRecord.expires_on.is_not(None),
            TrackedRecord.expires_on >= today,
            TrackedRecord.expires_on <= cutoff,
        )
    )
    for row in tr_result.scalars().all():
        # Resolve record_type slug for display
        term_result = await db.execute(
            select(Term).where(Term.id == row.record_type_id)
        )
        term = term_result.scalars().first()
        record_type_slug = term.slug if term else None

        entries.append(
            RenewalEntry(
                entity_type="tracked_record",
                entity_id=row.id,
                title=row.title,
                record_type=record_type_slug,
                expires_on=row.expires_on,
                days_remaining=(row.expires_on - today).days,
                auto_renews=row.auto_renews,
                cost=row.cost,
                currency=row.currency,
                asset_id=row.asset_id,
                person_id=row.person_id,
            )
        )

    # ── Subscriptions with next_billing_date in window ─────────────────────────
    sub_result = await db.execute(
        select(Subscription).where(
            Subscription.owner_id == owner_id,
            Subscription.deleted_at.is_(None),
            Subscription.next_billing_date.is_not(None),
            Subscription.next_billing_date >= today,
            Subscription.next_billing_date <= cutoff,
        )
    )
    for row in sub_result.scalars().all():
        entries.append(
            RenewalEntry(
                entity_type="subscription",
                entity_id=row.id,
                title=row.name,
                record_type=None,
                expires_on=row.next_billing_date,
                days_remaining=(row.next_billing_date - today).days,
                auto_renews=row.auto_renews,
                cost=row.cost,
                currency=row.currency,
                asset_id=row.asset_id,
                person_id=None,
            )
        )

    entries.sort(key=lambda e: e.expires_on)
    return entries
