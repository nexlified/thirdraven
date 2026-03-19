import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.vocabulary import resolve_optional_term_slug, resolve_term_slug
from app.models.subscription import BillPayment, Subscription, SubscriptionTag
from app.models.vocabulary import Term
from app.schemas.subscription import (
    BillPaymentCreate,
    BillPaymentPublicRead,
    BillPaymentUpdate,
    CategorySpend,
    SubscriptionCreate,
    SubscriptionPublicRead,
    SubscriptionSummary,
    SubscriptionUpdate,
    UpcomingRenewal,
)
from app.schemas.vocabulary import TermSlim

# Monthly cost multipliers per billing cycle
_CYCLE_TO_MONTHLY: dict[str, float] = {
    "daily": 30.0,
    "weekly": 30.0 / 7,
    "monthly": 1.0,
    "quarterly": 1.0 / 3,
    "semi_annual": 1.0 / 6,
    "annual": 1.0 / 12,
}


# ── Tag helpers ─────────────────────────────────────────────────────────────────


async def _get_subscription_tags(
    db: AsyncSession, subscription_id: uuid.UUID
) -> list[TermSlim]:
    result = await db.execute(
        select(Term)
        .join(SubscriptionTag, Term.id == SubscriptionTag.term_id)
        .where(
            SubscriptionTag.subscription_id == subscription_id,
            Term.is_active.is_(True),
        )
        .order_by(Term.name)
    )
    return [TermSlim.model_validate(t) for t in result.scalars().all()]


async def _set_subscription_tags(
    db: AsyncSession, subscription_id: uuid.UUID, tag_slugs: list[str]
) -> None:
    existing = await db.execute(
        select(SubscriptionTag).where(
            SubscriptionTag.subscription_id == subscription_id
        )
    )
    for row in existing.scalars().all():
        await db.delete(row)
    for slug in tag_slugs:
        term_id = await resolve_term_slug(db, "subscription-tags", slug)
        db.add(SubscriptionTag(subscription_id=subscription_id, term_id=term_id))


async def _get_term(db: AsyncSession, term_id: uuid.UUID | None) -> TermSlim | None:
    if term_id is None:
        return None
    result = await db.execute(select(Term).where(Term.id == term_id))
    t = result.scalars().first()
    return TermSlim.model_validate(t) if t else None


async def _build_public(db: AsyncSession, sub: Subscription) -> SubscriptionPublicRead:
    category = await _get_term(db, sub.category_term_id)
    tags = await _get_subscription_tags(db, sub.id)
    return SubscriptionPublicRead(
        id=sub.id,
        owner_id=sub.owner_id,
        name=sub.name,
        provider=sub.provider,
        category=category,
        status=sub.status,
        cost=sub.cost,
        currency=sub.currency,
        payment_mode=sub.payment_mode,
        billing_cycle=sub.billing_cycle,
        billing_cycle_days=sub.billing_cycle_days,
        started_on=sub.started_on,
        next_billing_date=sub.next_billing_date,
        trial_ends_on=sub.trial_ends_on,
        cancelled_on=sub.cancelled_on,
        auto_renews=sub.auto_renews,
        url=sub.url,
        notes=sub.notes,
        asset_id=sub.asset_id,
        tags=tags,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
    )


def _monthly_cost(sub: Subscription) -> float:
    if sub.billing_cycle == "custom":
        days = sub.billing_cycle_days or 30
        return sub.cost / days * 30
    multiplier = _CYCLE_TO_MONTHLY.get(sub.billing_cycle, 1.0)
    return sub.cost * multiplier


# ── CRUD ────────────────────────────────────────────────────────────────────────


async def create_subscription(
    db: AsyncSession, owner_id: uuid.UUID, data: SubscriptionCreate
) -> SubscriptionPublicRead:
    raw = data.model_dump(exclude_unset=True)
    tag_slugs = raw.pop("tags", [])
    category_slug = raw.pop("category", None)

    category_term_id = await resolve_optional_term_slug(
        db, "subscription-categories", category_slug
    )

    sub = Subscription(owner_id=owner_id, category_term_id=category_term_id, **raw)
    db.add(sub)
    await db.flush()

    for slug in tag_slugs:
        term_id = await resolve_term_slug(db, "subscription-tags", slug)
        db.add(SubscriptionTag(subscription_id=sub.id, term_id=term_id))

    await db.commit()
    await db.refresh(sub)
    return await _build_public(db, sub)


async def get_subscription(
    db: AsyncSession, subscription_id: uuid.UUID, owner_id: uuid.UUID
) -> Subscription | None:
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.owner_id == owner_id,
            Subscription.deleted_at.is_(None),
        )
    )
    return result.scalars().first()


async def get_subscription_public(
    db: AsyncSession, subscription_id: uuid.UUID, owner_id: uuid.UUID
) -> SubscriptionPublicRead | None:
    sub = await get_subscription(db, subscription_id, owner_id)
    if not sub:
        return None
    return await _build_public(db, sub)


async def list_subscriptions(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    category: str | None = None,
    billing_cycle: str | None = None,
) -> list[SubscriptionPublicRead]:
    query = select(Subscription).where(
        Subscription.owner_id == owner_id,
        Subscription.deleted_at.is_(None),
    )

    if status is not None:
        query = query.where(Subscription.status == status)
    if billing_cycle is not None:
        query = query.where(Subscription.billing_cycle == billing_cycle)
    if category is not None:
        cat_id = await resolve_optional_term_slug(
            db, "subscription-categories", category
        )
        query = query.where(Subscription.category_term_id == cat_id)

    result = await db.execute(query.offset(skip).limit(limit))
    return [await _build_public(db, s) for s in result.scalars().all()]


async def update_subscription(
    db: AsyncSession,
    subscription_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: SubscriptionUpdate,
) -> SubscriptionPublicRead | None:
    sub = await get_subscription(db, subscription_id, owner_id)
    if not sub:
        return None

    raw = data.model_dump(exclude_unset=True)
    tag_slugs = raw.pop("tags", None)

    if "category" in raw:
        sub.category_term_id = await resolve_optional_term_slug(
            db, "subscription-categories", raw.pop("category")
        )

    for field, value in raw.items():
        setattr(sub, field, value)
    sub.updated_at = datetime.utcnow()
    db.add(sub)

    if tag_slugs is not None:
        await _set_subscription_tags(db, subscription_id, tag_slugs)

    await db.commit()
    await db.refresh(sub)
    return await _build_public(db, sub)


async def soft_delete_subscription(
    db: AsyncSession, subscription_id: uuid.UUID, owner_id: uuid.UUID
) -> Subscription | None:
    sub = await get_subscription(db, subscription_id, owner_id)
    if not sub:
        return None
    sub.deleted_at = datetime.utcnow()
    db.add(sub)
    await db.commit()
    return sub


# ── Summary ─────────────────────────────────────────────────────────────────────


async def get_summary(db: AsyncSession, owner_id: uuid.UUID) -> SubscriptionSummary:
    result = await db.execute(
        select(Subscription).where(
            Subscription.owner_id == owner_id,
            Subscription.deleted_at.is_(None),
            Subscription.status == "active",
        )
    )
    active_subs = result.scalars().all()

    monthly_by_currency: dict[str, float] = defaultdict(float)
    for s in active_subs:
        monthly_by_currency[s.currency] += _monthly_cost(s)
    monthly_by_currency = {k: round(v, 2) for k, v in monthly_by_currency.items()}

    today = date.today()
    cutoff = today + timedelta(days=30)
    upcoming = [
        UpcomingRenewal(
            id=s.id,
            name=s.name,
            cost=s.cost,
            currency=s.currency,
            next_billing_date=s.next_billing_date,
        )
        for s in active_subs
        if s.next_billing_date and today <= s.next_billing_date <= cutoff
    ]
    upcoming.sort(key=lambda r: r.next_billing_date)

    # Group monthly cost by category term name
    category_spend: dict[str, float] = defaultdict(float)
    for s in active_subs:
        term = await _get_term(db, s.category_term_id)
        label = term.name if term else "Uncategorized"
        category_spend[label] += _monthly_cost(s)

    return SubscriptionSummary(
        total_active=len(active_subs),
        monthly_cost_by_currency=monthly_by_currency,
        upcoming_renewals=upcoming,
        cost_by_category=[
            CategorySpend(category=k, monthly_cost=round(v, 2))
            for k, v in sorted(category_spend.items())
        ],
    )


# ── Bill Payments ────────────────────────────────────────────────────────────────


async def create_payment(
    db: AsyncSession,
    subscription_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: BillPaymentCreate,
) -> BillPaymentPublicRead:
    payment_data = data.model_dump()
    if payment_data.get("payment_mode") is None:
        sub = await get_subscription(db, subscription_id, owner_id)
        payment_data["payment_mode"] = sub.payment_mode if sub else "manual"
    payment = BillPayment(
        subscription_id=subscription_id,
        owner_id=owner_id,
        **payment_data,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return BillPaymentPublicRead.model_validate(payment)


async def list_payments(
    db: AsyncSession,
    subscription_id: uuid.UUID,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> list[BillPaymentPublicRead]:
    result = await db.execute(
        select(BillPayment)
        .where(
            BillPayment.subscription_id == subscription_id,
            BillPayment.owner_id == owner_id,
        )
        .order_by(BillPayment.billing_date.desc())
        .offset(skip)
        .limit(limit)
    )
    return [BillPaymentPublicRead.model_validate(p) for p in result.scalars().all()]


async def get_payment(
    db: AsyncSession,
    subscription_id: uuid.UUID,
    payment_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> BillPayment | None:
    result = await db.execute(
        select(BillPayment).where(
            BillPayment.id == payment_id,
            BillPayment.subscription_id == subscription_id,
            BillPayment.owner_id == owner_id,
        )
    )
    return result.scalars().first()


async def update_payment(
    db: AsyncSession,
    subscription_id: uuid.UUID,
    payment_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: BillPaymentUpdate,
) -> BillPaymentPublicRead | None:
    payment = await get_payment(db, subscription_id, payment_id, owner_id)
    if not payment:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(payment, field, value)
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return BillPaymentPublicRead.model_validate(payment)


async def delete_payment(
    db: AsyncSession,
    subscription_id: uuid.UUID,
    payment_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> bool:
    payment = await get_payment(db, subscription_id, payment_id, owner_id)
    if not payment:
        return False
    await db.delete(payment)
    await db.commit()
    return True
