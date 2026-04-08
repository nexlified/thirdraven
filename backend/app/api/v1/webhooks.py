"""PriceRaven webhook receiver.

Authentication uses HMAC-SHA256 signature verification (shared secret).
All endpoints return 503 when the secret is not configured and 401 when
the signature is invalid or the owner_api_key cannot be resolved.
"""

import hashlib
import hmac
import logging
import uuid
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import get_settings
from app.core.database import get_session
from app.crud.user import get_user_by_api_key
from app.models.product import Product
from app.models.reminder import Reminder
from app.models.transaction import Transaction
from app.models.transaction_item import TransactionItem
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ── HMAC helper ───────────────────────────────────────────────────────────────


def verify_priceraven_signature(
    body: bytes, signature_header: str, secret: str
) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


# ── Request / response schemas ────────────────────────────────────────────────


class PriceRavenBillItem(BaseModel):
    raw_name: str
    quantity: float
    unit: str | None = None
    unit_price: float
    total_price: float
    discount: float = 0
    priceraven_product_id: str | None = None


class PriceRavenBillParsedPayload(BaseModel):
    batch_id: str
    transaction_date: date
    store_name: str | None = None
    items: list[PriceRavenBillItem]
    owner_api_key: str


class BillParsedResponse(BaseModel):
    transaction_id: str
    items_created: int
    products_matched: int
    reorders_triggered: int


class PriceRavenPriceAlertPayload(BaseModel):
    priceraven_product_id: str
    platform: str
    old_price: float
    new_price: float
    direction: str  # "up" | "down"
    currency: str = "INR"
    url: str | None = None
    owner_api_key: str


class PriceAlertResponse(BaseModel):
    reminder_id: str | None


# ── Internal CRUD helpers (called from endpoints, mockable in tests) ──────────


async def process_bill_parsed(
    db: AsyncSession,
    owner_id: uuid.UUID,
    payload: PriceRavenBillParsedPayload,
) -> dict:
    """Create Transaction + TransactionItems atomically and trigger inventory.

    Returns a dict with transaction_id, items_created, products_matched,
    reorders_triggered.  If a Transaction with the same import_batch_id already
    exists for this owner the operation is idempotent: the existing transaction
    is returned with zero counts.
    """
    from app.crud.inventory import update_inventory_on_purchase
    from app.crud.vocabulary import resolve_optional_term_slug

    # Idempotency check
    existing_result = await db.execute(
        select(Transaction).where(
            Transaction.owner_id == owner_id,
            Transaction.import_batch_id == payload.batch_id,
            Transaction.deleted_at.is_(None),
        )
    )
    existing_tx = existing_result.scalars().first()
    if existing_tx:
        return {
            "transaction_id": str(existing_tx.id),
            "items_created": 0,
            "products_matched": 0,
            "reorders_triggered": 0,
        }

    # Resolve "groceries" category slug
    category_term_id = await resolve_optional_term_slug(
        db, "expense-categories", "groceries"
    )

    total_amount = sum(item.total_price for item in payload.items)
    tx = Transaction(
        owner_id=owner_id,
        transaction_type="expense",
        description=payload.store_name or "Bill Import",
        transacted_on=payload.transaction_date,
        import_batch_id=payload.batch_id,
        amount=total_amount,
        category_term_id=category_term_id,
    )
    db.add(tx)
    await db.flush()

    products_matched = 0
    reorders_triggered = 0
    for item in payload.items:
        product_id: uuid.UUID | None = None
        if item.priceraven_product_id is not None:
            prod_result = await db.execute(
                select(Product).where(
                    Product.owner_id == owner_id,
                    Product.priceraven_product_id == item.priceraven_product_id,
                    Product.deleted_at.is_(None),
                )
            )
            matched = prod_result.scalars().first()
            if matched:
                product_id = matched.id
                products_matched += 1

        tx_item = TransactionItem(
            owner_id=owner_id,
            transaction_id=tx.id,
            product_id=product_id,
            raw_name=item.raw_name,
            quantity=item.quantity,
            unit=item.unit,
            unit_price=item.unit_price,
            total_price=item.total_price,
            discount=item.discount,
            store_name=payload.store_name,
            import_batch_id=payload.batch_id,
        )
        db.add(tx_item)
        await db.flush()

        if product_id is not None:
            from app.models.inventory import InventoryProfile

            profile_result = await db.execute(
                select(InventoryProfile).where(
                    InventoryProfile.owner_id == owner_id,
                    InventoryProfile.product_id == product_id,
                )
            )
            profile = profile_result.scalars().first()
            if profile:
                # Compute projected stock before calling the helper so the
                # comparison is deterministic and doesn't depend on whether
                # SQLAlchemy's identity map returns the same object instance.
                projected_stock = profile.current_stock + item.quantity
                await update_inventory_on_purchase(
                    db, owner_id, product_id, item.quantity, payload.transaction_date
                )
                # Count products where stock is still at/below reorder
                # threshold even after restocking (triggers a reorder reminder).
                if projected_stock <= profile.reorder_threshold:
                    reorders_triggered += 1

    await db.commit()

    return {
        "transaction_id": str(tx.id),
        "items_created": len(payload.items),
        "products_matched": products_matched,
        "reorders_triggered": reorders_triggered,
    }


async def process_price_alert(
    db: AsyncSession,
    owner_id: uuid.UUID,
    payload: PriceRavenPriceAlertPayload,
) -> dict:
    """Create a price-alert Reminder for a matched product.

    If no Product with the given priceraven_product_id exists for this owner,
    the function logs a warning and returns ``{"reminder_id": None}``.
    """
    prod_result = await db.execute(
        select(Product).where(
            Product.owner_id == owner_id,
            Product.priceraven_product_id == payload.priceraven_product_id,
            Product.deleted_at.is_(None),
        )
    )
    product = prod_result.scalars().first()
    if not product:
        logger.warning(
            "price-alert: priceraven_product_id=%s not found for owner=%s; skipping",
            payload.priceraven_product_id,
            owner_id,
        )
        return {"reminder_id": None}

    if payload.direction == "down":
        title = (
            f"Price drop! {product.name} on {payload.platform}: "
            f"₹{payload.old_price} → ₹{payload.new_price}"
        )
    else:
        title = (
            f"Price increase: {product.name} on {payload.platform}: "
            f"₹{payload.old_price} → ₹{payload.new_price}"
        )

    remind_dt = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=None)
    reminder = Reminder(
        owner_id=owner_id,
        title=title,
        url=payload.url,
        due_at=remind_dt,
        remind_at=remind_dt,
        product_id=product.id,
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)

    return {"reminder_id": str(reminder.id)}


# ── Auth guard ────────────────────────────────────────────────────────────────


def _require_priceraven_enabled() -> None:
    settings = get_settings()
    if not settings.priceraven_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PriceRaven integration not configured",
        )


async def _verify_and_resolve(
    request: Request,
    db: AsyncSession,
    owner_api_key: str,
) -> User:
    """Verify HMAC signature and resolve owner_api_key to a User."""
    settings = get_settings()
    body = await request.body()
    sig = request.headers.get("X-PriceRaven-Signature", "")
    if not verify_priceraven_signature(body, sig, settings.priceraven_webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )
    owner = await get_user_by_api_key(db, owner_api_key)
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid owner_api_key",
        )
    return owner


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/priceraven/bill-parsed",
    response_model=BillParsedResponse,
    status_code=status.HTTP_200_OK,
)
async def bill_parsed(
    request: Request,
    payload: PriceRavenBillParsedPayload,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    _require_priceraven_enabled()
    owner = await _verify_and_resolve(request, db, payload.owner_api_key)
    result = await process_bill_parsed(db, owner.id, payload)
    return result


@router.post(
    "/priceraven/price-alert",
    response_model=PriceAlertResponse,
    status_code=status.HTTP_200_OK,
)
async def price_alert(
    request: Request,
    payload: PriceRavenPriceAlertPayload,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    _require_priceraven_enabled()
    owner = await _verify_and_resolve(request, db, payload.owner_api_key)
    result = await process_price_alert(db, owner.id, payload)
    return result
