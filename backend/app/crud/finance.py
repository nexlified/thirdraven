import uuid
from collections import defaultdict
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.subscription import get_summary as get_subscription_summary
from app.crud.transaction import get_transaction_summary
from app.models.asset import Asset
from app.models.asset_extensions import FinancialAsset
from app.models.loan import Loan
from app.models.person import Person
from app.models.vocabulary import Term
from app.schemas.finance import AssetSummaryItem, FinanceOverview, LoanSummaryItem


async def _resolve_term_name(
    db: AsyncSession, term_id: uuid.UUID | None
) -> str | None:
    if term_id is None:
        return None
    result = await db.execute(select(Term).where(Term.id == term_id))
    t = result.scalars().first()
    return t.name if t else None


def _person_display_name(person: Person) -> str:
    parts = [person.first_name]
    if person.last_name:
        parts.append(person.last_name)
    return " ".join(parts)


async def get_finance_overview(
    db: AsyncSession,
    owner_id: uuid.UUID,
    primary_currency: str = "INR",
) -> FinanceOverview:
    # ── Step 1: Financial assets ────────────────────────────���─────────────────
    fa_result = await db.execute(
        select(FinancialAsset, Asset)
        .join(Asset, FinancialAsset.asset_id == Asset.id)
        .where(
            Asset.owner_id == owner_id,
            Asset.deleted_at.is_(None),
        )
    )
    financial_assets: list[AssetSummaryItem] = []
    asset_value_by_currency: dict[str, float] = defaultdict(float)

    for fa, asset in fa_result.all():
        account_type = await _resolve_term_name(db, fa.account_type_term_id)
        financial_assets.append(
            AssetSummaryItem(
                asset_id=asset.id,
                name=asset.name,
                account_type=account_type,
                institution=fa.institution,
                current_balance=fa.current_balance,
                currency=fa.currency,
            )
        )
        if fa.current_balance is not None and fa.currency:
            asset_value_by_currency[fa.currency] += fa.current_balance

    total_asset_value_by_currency = {
        k: round(v, 2) for k, v in asset_value_by_currency.items()
    }

    # ── Step 2: Outstanding loans ─────────────────────────────────────────────
    loan_result = await db.execute(
        select(Loan, Person)
        .join(Person, Loan.person_id == Person.id)
        .where(
            Loan.owner_id == owner_id,
            Loan.status == "outstanding",
            Loan.deleted_at.is_(None),
        )
    )
    outstanding_loans: list[LoanSummaryItem] = []
    lent_by_currency: dict[str, float] = defaultdict(float)
    borrowed_by_currency: dict[str, float] = defaultdict(float)

    for loan, person in loan_result.all():
        outstanding_loans.append(
            LoanSummaryItem(
                loan_id=loan.id,
                direction=loan.direction,
                person_name=_person_display_name(person),
                amount=loan.amount,
                currency=loan.currency,
                status=loan.status,
                due_on=loan.due_on,
            )
        )
        if loan.amount is not None and loan.currency:
            if loan.direction == "lent":
                lent_by_currency[loan.currency] += loan.amount
            else:
                borrowed_by_currency[loan.currency] += loan.amount

    total_lent_by_currency = {k: round(v, 2) for k, v in lent_by_currency.items()}
    total_borrowed_by_currency = {
        k: round(v, 2) for k, v in borrowed_by_currency.items()
    }

    # ── Step 3: Current month transactions ────────────────────────────────────
    today = date.today()
    first_day = today.replace(day=1)
    tx_summary = await get_transaction_summary(
        db, owner_id, first_day, today, primary_currency
    )

    # ── Step 4: Subscription burn rate ────────────────────────────────────────
    sub_summary = await get_subscription_summary(db, owner_id)

    return FinanceOverview(
        financial_assets=financial_assets,
        total_asset_value_by_currency=total_asset_value_by_currency,
        outstanding_loans=outstanding_loans,
        total_lent_by_currency=total_lent_by_currency,
        total_borrowed_by_currency=total_borrowed_by_currency,
        current_month_income=tx_summary.total_income,
        current_month_expenses=tx_summary.total_expense,
        current_month_net=tx_summary.net,
        current_month_savings_rate=tx_summary.savings_rate,
        current_month_currency=primary_currency,
        top_expense_categories=tx_summary.expense_by_category[:5],
        monthly_subscription_cost_by_currency=sub_summary.monthly_cost_by_currency,
        as_of=datetime.now(UTC),
    )
