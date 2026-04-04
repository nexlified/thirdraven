import uuid
from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel


class PhysicalAsset(SQLModel, table=True):
    __tablename__ = "physical_asset"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    asset_id: uuid.UUID = Field(foreign_key="asset.id", unique=True, index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))

    brand: str | None = None
    model_number: str | None = None
    serial_number: str | None = None
    identifier_value: str | None = None  # barcode, IMEI, EAN, UPC, VIN, ISBN
    # imei|ean|upc|vin|isbn|barcode|other
    identifier_type: str | None = None
    color: str | None = None
    condition_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    dimensions: str | None = None  # free text, e.g. "30 x 20 x 10 cm"
    weight_grams: float | None = None
    manufactured_year: int | None = None


class DocumentAsset(SQLModel, table=True):
    __tablename__ = "document_asset"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    asset_id: uuid.UUID = Field(foreign_key="asset.id", unique=True, index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))

    document_type_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    document_number: str | None = None
    issuer: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    country_id: uuid.UUID | None = Field(default=None, foreign_key="country.id")
    is_primary: bool = Field(default=False)


class FinancialAsset(SQLModel, table=True):
    __tablename__ = "financial_asset"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    asset_id: uuid.UUID = Field(foreign_key="asset.id", unique=True, index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))

    institution: str | None = None
    account_number: str | None = None
    account_type_term_id: uuid.UUID | None = Field(default=None, foreign_key="term.id")
    current_balance: float | None = None
    currency: str | None = None  # ISO 4217
    interest_rate: float | None = None  # annual rate as decimal (0.065 = 6.5%)
    maturity_date: date | None = None
    nominee: str | None = None


class DigitalAsset(SQLModel, table=True):
    __tablename__ = "digital_asset"

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    asset_id: uuid.UUID = Field(foreign_key="asset.id", unique=True, index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))

    platform: str | None = None  # e.g. "GitHub", "Adobe"
    license_key: str | None = None
    license_type: str | None = None  # "perpetual"|"subscription"|"open-source"|"trial"
    seat_count: int | None = None
    version: str | None = None
    download_url: str | None = None
    subscription_id: uuid.UUID | None = Field(
        default=None, foreign_key="subscription.id"
    )
