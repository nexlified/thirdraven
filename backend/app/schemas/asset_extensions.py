import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.iso_reference import CountrySlim
from app.schemas.vocabulary import TermSlim

# ── Physical Asset ────────────────────────────────────────────────────────────


class PhysicalAssetCreate(BaseModel):
    brand: str | None = None
    model_number: str | None = None
    serial_number: str | None = None
    identifier_value: str | None = None
    identifier_type: str | None = (
        None  # "imei"|"ean"|"upc"|"vin"|"isbn"|"barcode"|"other"
    )
    color: str | None = None
    condition: str | None = None  # slug from "asset-conditions" vocabulary
    dimensions: str | None = None
    weight_grams: float | None = None
    manufactured_year: int | None = None


class PhysicalAssetUpdate(BaseModel):
    brand: str | None = None
    model_number: str | None = None
    serial_number: str | None = None
    identifier_value: str | None = None
    identifier_type: str | None = None
    color: str | None = None
    condition: str | None = None
    dimensions: str | None = None
    weight_grams: float | None = None
    manufactured_year: int | None = None


class PhysicalAssetPublic(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    brand: str | None
    model_number: str | None
    serial_number: str | None
    identifier_value: str | None
    identifier_type: str | None
    color: str | None
    condition: TermSlim | None = None
    dimensions: str | None
    weight_grams: float | None
    manufactured_year: int | None
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Document Asset ────────────────────────────────────────────────────────────


class DocumentAssetCreate(BaseModel):
    document_type: str | None = None  # slug from "document-asset-types" vocabulary
    document_number: str | None = None
    issuer: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    country: str | None = None  # ISO alpha2 code
    is_primary: bool = False


class DocumentAssetUpdate(BaseModel):
    document_type: str | None = None
    document_number: str | None = None
    issuer: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    country: str | None = None
    is_primary: bool | None = None


class DocumentAssetPublic(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    document_type: TermSlim | None = None
    document_number: str | None
    issuer: str | None
    issue_date: date | None
    expiry_date: date | None
    country: CountrySlim | None = None
    is_primary: bool
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Financial Asset ───────────────────────────────────────────────────────────


class FinancialAssetCreate(BaseModel):
    institution: str | None = None
    account_number: str | None = None
    account_type: str | None = None  # slug from "financial-account-types" vocabulary
    current_balance: float | None = None
    currency: str | None = None  # ISO 4217
    interest_rate: float | None = None
    maturity_date: date | None = None
    nominee: str | None = None


class FinancialAssetUpdate(BaseModel):
    institution: str | None = None
    account_number: str | None = None
    account_type: str | None = None
    current_balance: float | None = None
    currency: str | None = None
    interest_rate: float | None = None
    maturity_date: date | None = None
    nominee: str | None = None


class FinancialAssetPublic(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    institution: str | None
    account_number: str | None
    account_type: TermSlim | None = None
    current_balance: float | None
    currency: str | None
    interest_rate: float | None
    maturity_date: date | None
    nominee: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Digital Asset ─────────────────────────────────────────────────────────────


class DigitalAssetCreate(BaseModel):
    platform: str | None = None
    license_key: str | None = None
    license_type: str | None = None  # "perpetual"|"subscription"|"open-source"|"trial"
    seat_count: int | None = None
    version: str | None = None
    download_url: str | None = None
    subscription_id: uuid.UUID | None = None


class DigitalAssetUpdate(BaseModel):
    platform: str | None = None
    license_key: str | None = None
    license_type: str | None = None
    seat_count: int | None = None
    version: str | None = None
    download_url: str | None = None
    subscription_id: uuid.UUID | None = None


class DigitalAssetPublic(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    platform: str | None
    license_key: str | None
    license_type: str | None
    seat_count: int | None
    version: str | None
    download_url: str | None
    subscription_id: uuid.UUID | None
    updated_at: datetime

    model_config = {"from_attributes": True}
