import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.iso_reference import resolve_country_alpha2
from app.crud.vocabulary import resolve_optional_term_slug
from app.models.asset_extensions import (
    DigitalAsset,
    DocumentAsset,
    FinancialAsset,
    PhysicalAsset,
)
from app.models.iso_reference import Country
from app.models.vocabulary import Term
from app.schemas.asset_extensions import (
    DigitalAssetCreate,
    DigitalAssetPublic,
    DigitalAssetUpdate,
    DocumentAssetCreate,
    DocumentAssetPublic,
    DocumentAssetUpdate,
    FinancialAssetCreate,
    FinancialAssetPublic,
    FinancialAssetUpdate,
    PhysicalAssetCreate,
    PhysicalAssetPublic,
    PhysicalAssetUpdate,
)
from app.schemas.iso_reference import CountrySlim
from app.schemas.vocabulary import TermSlim


async def _resolve_term(db: AsyncSession, term_id: uuid.UUID | None) -> TermSlim | None:
    if not term_id:
        return None
    r = await db.execute(select(Term).where(Term.id == term_id))
    t = r.scalars().first()
    return TermSlim.model_validate(t) if t else None


# ── Physical Asset ────────────────────────────────────────────────────────────


async def _build_physical_public(
    db: AsyncSession, row: PhysicalAsset
) -> PhysicalAssetPublic:
    condition = await _resolve_term(db, row.condition_term_id)
    return PhysicalAssetPublic(
        id=row.id,
        asset_id=row.asset_id,
        brand=row.brand,
        model_number=row.model_number,
        serial_number=row.serial_number,
        identifier_value=row.identifier_value,
        identifier_type=row.identifier_type,
        color=row.color,
        condition=condition,
        dimensions=row.dimensions,
        weight_grams=row.weight_grams,
        manufactured_year=row.manufactured_year,
        updated_at=row.updated_at,
    )


async def get_physical_asset(
    db: AsyncSession, asset_id: uuid.UUID
) -> PhysicalAssetPublic | None:
    r = await db.execute(
        select(PhysicalAsset).where(PhysicalAsset.asset_id == asset_id)
    )
    row = r.scalars().first()
    if not row:
        return None
    return await _build_physical_public(db, row)


async def upsert_physical_asset(
    db: AsyncSession,
    asset_id: uuid.UUID,
    data: PhysicalAssetCreate | PhysicalAssetUpdate,
) -> PhysicalAssetPublic:
    r = await db.execute(
        select(PhysicalAsset).where(PhysicalAsset.asset_id == asset_id)
    )
    row = r.scalars().first()

    raw = data.model_dump(exclude_unset=True)
    condition_term_id = None
    if "condition" in raw:
        slug = raw.pop("condition")
        if slug:
            condition_term_id = await resolve_optional_term_slug(
                db, "asset-conditions", slug
            )

    if row:
        for field, value in raw.items():
            setattr(row, field, value)
        if condition_term_id is not None or "condition" in data.model_dump(
            exclude_unset=True
        ):
            row.condition_term_id = condition_term_id
        row.updated_at = datetime.now(UTC)
    else:
        row = PhysicalAsset(
            asset_id=asset_id, condition_term_id=condition_term_id, **raw
        )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_physical_public(db, row)


async def delete_physical_asset(db: AsyncSession, asset_id: uuid.UUID) -> bool:
    r = await db.execute(
        select(PhysicalAsset).where(PhysicalAsset.asset_id == asset_id)
    )
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True


# ── Document Asset ────────────────────────────────────────────────────────────


async def _build_document_public(
    db: AsyncSession, row: DocumentAsset
) -> DocumentAssetPublic:
    document_type = await _resolve_term(db, row.document_type_term_id)
    country = None
    if row.country_id:
        r = await db.execute(select(Country).where(Country.id == row.country_id))
        c = r.scalars().first()
        if c:
            country = CountrySlim.model_validate(c)
    return DocumentAssetPublic(
        id=row.id,
        asset_id=row.asset_id,
        document_type=document_type,
        document_number=row.document_number,
        issuer=row.issuer,
        issue_date=row.issue_date,
        expiry_date=row.expiry_date,
        country=country,
        is_primary=row.is_primary,
        updated_at=row.updated_at,
    )


async def get_document_asset(
    db: AsyncSession, asset_id: uuid.UUID
) -> DocumentAssetPublic | None:
    r = await db.execute(
        select(DocumentAsset).where(DocumentAsset.asset_id == asset_id)
    )
    row = r.scalars().first()
    if not row:
        return None
    return await _build_document_public(db, row)


async def upsert_document_asset(
    db: AsyncSession,
    asset_id: uuid.UUID,
    data: DocumentAssetCreate | DocumentAssetUpdate,
) -> DocumentAssetPublic:
    r = await db.execute(
        select(DocumentAsset).where(DocumentAsset.asset_id == asset_id)
    )
    row = r.scalars().first()

    raw = data.model_dump(exclude_unset=True)
    document_type_term_id = None
    if "document_type" in raw:
        slug = raw.pop("document_type")
        if slug:
            document_type_term_id = await resolve_optional_term_slug(
                db, "document-asset-types", slug
            )
    country_id = None
    if "country" in raw:
        code = raw.pop("country")
        if code:
            country_id = await resolve_country_alpha2(db, code)

    if row:
        for field, value in raw.items():
            setattr(row, field, value)
        if "document_type" in data.model_dump(exclude_unset=True):
            row.document_type_term_id = document_type_term_id
        if "country" in data.model_dump(exclude_unset=True):
            row.country_id = country_id
        row.updated_at = datetime.now(UTC)
    else:
        row = DocumentAsset(
            asset_id=asset_id,
            document_type_term_id=document_type_term_id,
            country_id=country_id,
            **raw,
        )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_document_public(db, row)


async def delete_document_asset(db: AsyncSession, asset_id: uuid.UUID) -> bool:
    r = await db.execute(
        select(DocumentAsset).where(DocumentAsset.asset_id == asset_id)
    )
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True


# ── Financial Asset ───────────────────────────────────────────────────────────


async def _build_financial_public(
    db: AsyncSession, row: FinancialAsset
) -> FinancialAssetPublic:
    account_type = await _resolve_term(db, row.account_type_term_id)
    return FinancialAssetPublic(
        id=row.id,
        asset_id=row.asset_id,
        institution=row.institution,
        account_number=row.account_number,
        account_type=account_type,
        current_balance=row.current_balance,
        currency=row.currency,
        interest_rate=row.interest_rate,
        maturity_date=row.maturity_date,
        nominee=row.nominee,
        updated_at=row.updated_at,
    )


async def get_financial_asset(
    db: AsyncSession, asset_id: uuid.UUID
) -> FinancialAssetPublic | None:
    r = await db.execute(
        select(FinancialAsset).where(FinancialAsset.asset_id == asset_id)
    )
    row = r.scalars().first()
    if not row:
        return None
    return await _build_financial_public(db, row)


async def upsert_financial_asset(
    db: AsyncSession,
    asset_id: uuid.UUID,
    data: FinancialAssetCreate | FinancialAssetUpdate,
) -> FinancialAssetPublic:
    r = await db.execute(
        select(FinancialAsset).where(FinancialAsset.asset_id == asset_id)
    )
    row = r.scalars().first()

    raw = data.model_dump(exclude_unset=True)
    account_type_term_id = None
    if "account_type" in raw:
        slug = raw.pop("account_type")
        if slug:
            account_type_term_id = await resolve_optional_term_slug(
                db, "financial-account-types", slug
            )

    if row:
        for field, value in raw.items():
            setattr(row, field, value)
        if "account_type" in data.model_dump(exclude_unset=True):
            row.account_type_term_id = account_type_term_id
        row.updated_at = datetime.now(UTC)
    else:
        row = FinancialAsset(
            asset_id=asset_id, account_type_term_id=account_type_term_id, **raw
        )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _build_financial_public(db, row)


async def delete_financial_asset(db: AsyncSession, asset_id: uuid.UUID) -> bool:
    r = await db.execute(
        select(FinancialAsset).where(FinancialAsset.asset_id == asset_id)
    )
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True


# ── Digital Asset ─────────────────────────────────────────────────────────────


async def get_digital_asset(
    db: AsyncSession, asset_id: uuid.UUID
) -> DigitalAssetPublic | None:
    r = await db.execute(select(DigitalAsset).where(DigitalAsset.asset_id == asset_id))
    row = r.scalars().first()
    if not row:
        return None
    return DigitalAssetPublic.model_validate(row)


async def upsert_digital_asset(
    db: AsyncSession, asset_id: uuid.UUID, data: DigitalAssetCreate | DigitalAssetUpdate
) -> DigitalAssetPublic:
    r = await db.execute(select(DigitalAsset).where(DigitalAsset.asset_id == asset_id))
    row = r.scalars().first()

    raw = data.model_dump(exclude_unset=True)

    if row:
        for field, value in raw.items():
            setattr(row, field, value)
        row.updated_at = datetime.now(UTC)
    else:
        row = DigitalAsset(asset_id=asset_id, **raw)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return DigitalAssetPublic.model_validate(row)


async def delete_digital_asset(db: AsyncSession, asset_id: uuid.UUID) -> bool:
    r = await db.execute(select(DigitalAsset).where(DigitalAsset.asset_id == asset_id))
    row = r.scalars().first()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True
