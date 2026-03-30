# Asset Entity Specification

> ThirdRaven Entity Redesign — Asset Domain
> Created: 2026-03-30 | Status: Draft

---

## 1. Overview

The Asset domain becomes a **universal registry** for anything the user owns, holds, or needs to track — physical items, identity documents, financial accounts, digital licenses, and more.

**Design principles:**
- Lean core table with only fields universal to every asset type
- Category-specific details in 1:1 extension tables (same pattern as person extensions)
- Category hierarchy in vocabulary drives which extension applies
- Lifecycle events tracked in a dedicated log table

---

## 2. Revised Core `asset` Table

The core table is slimmed to fields that apply universally across all asset types.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK, `uuid7()` |
| `owner_id` | UUID | FK → `user.id`, indexed |
| `name` | str | required |
| `category_term_id` | UUID | FK → `term.id` (vocab: `asset-categories`) |
| `status_term_id` | UUID | FK → `term.id` (vocab: `asset-statuses`) |
| `description` | str \| None | |
| `vendor` | str \| None | Seller, issuer, or provider |
| `purchase_date` | date \| None | Acquisition date |
| `purchase_price` | float \| None | Cost at acquisition |
| `purchase_price_currency` | str \| None | ISO 4217 (renamed from `purchase_currency`) |
| `current_value` | float \| None | Estimated present value |
| `location_note` | str \| None | Where the asset is stored/kept |
| `image_url` | str \| None | Photo or thumbnail |
| `purchase_url` | str \| None | Product page or receipt link |
| `notes` | str \| None | Free-text notes |
| `created_at` | datetime | |
| `updated_at` | datetime | |
| `deleted_at` | datetime \| None | soft delete |

### Fields Removed from Core

| Removed Field | Moved To | Reason |
|---|---|---|
| `serial_number` | `physical_asset` | Only applies to physical items |
| `brand` | `physical_asset` | Only applies to physical items |
| `model_number` | `physical_asset` | Only applies to physical items |
| `color` | `physical_asset` | Only applies to physical items |
| `condition` | `physical_asset.condition_term_id` | Was hardcoded string; now vocab-driven |
| `barcode` | `physical_asset.identifier_value` + `identifier_type` | Renamed and typed |

### Field Renamed

| Old Name | New Name | Reason |
|---|---|---|
| `purchase_currency` | `purchase_price_currency` | Clarity: it describes the currency of `purchase_price`, not `current_value` |

### Existing Features Retained

- `asset_tag` junction table (M:N with `term.id` from `asset-tags` vocab) — no changes
- Soft delete via `deleted_at` — no changes
- Tags, notes, tasks can still link to assets via their `asset_id` FK — no changes

---

## 3. Extension Tables

All extension tables follow the person extension pattern: 1:1 relationship via unique `asset_id` FK, created lazily, loaded via `?include=` query parameter.

### 3.1 `physical_asset` — Tangible Items

For electronics, vehicles, appliances, tools, instruments, furniture, clothing, artwork.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK, `uuid7()` |
| `asset_id` | UUID | FK → `asset.id`, unique, indexed |
| `updated_at` | datetime | |
| `brand` | str \| None | Manufacturer or brand name |
| `model_number` | str \| None | Model number or name |
| `serial_number` | str \| None | Device serial number |
| `identifier_value` | str \| None | Barcode, IMEI, EAN, UPC, VIN, ISBN, etc. |
| `identifier_type` | str \| None | `"imei"` \| `"ean"` \| `"upc"` \| `"vin"` \| `"isbn"` \| `"barcode"` \| `"other"` |
| `color` | str \| None | Free text |
| `condition_term_id` | UUID \| None | FK → `term.id` (vocab: `asset-conditions`) |
| `dimensions` | str \| None | Free text, e.g. `"30 x 20 x 10 cm"` |
| `weight_grams` | float \| None | Weight in grams |
| `manufactured_year` | int \| None | Year of manufacture |

### 3.2 `document_asset` — Identity Documents, Certificates, Permits

For passports, IDs, licenses, visas, permits, registrations, certificates.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK, `uuid7()` |
| `asset_id` | UUID | FK → `asset.id`, unique, indexed |
| `updated_at` | datetime | |
| `document_type_term_id` | UUID \| None | FK → `term.id` (vocab: `document-asset-types`) |
| `document_number` | str \| None | Passport number, license number, etc. |
| `issuer` | str \| None | Issuing authority or organization |
| `issue_date` | date \| None | |
| `expiry_date` | date \| None | |
| `country_id` | UUID \| None | FK → `country.id` — issuing country |
| `is_primary` | bool | default `false` — primary document of its type |

### 3.3 `financial_asset` — Bank Accounts, Investments, Financial Instruments

For savings, checking, fixed deposits, mutual funds, stocks, retirement funds, crypto, property as investment.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK, `uuid7()` |
| `asset_id` | UUID | FK → `asset.id`, unique, indexed |
| `updated_at` | datetime | |
| `institution` | str \| None | Bank, broker, or fund house |
| `account_number` | str \| None | Masked or full account number |
| `account_type_term_id` | UUID \| None | FK → `term.id` (vocab: `financial-account-types`) |
| `current_balance` | float \| None | Current balance or holdings value |
| `currency` | str \| None | ISO 4217 |
| `interest_rate` | float \| None | Annual rate as decimal (0.065 = 6.5%) |
| `maturity_date` | date \| None | For fixed deposits, bonds |
| `nominee` | str \| None | Free-text nominee name |

### 3.4 `digital_asset` — Software Licenses, Digital Subscriptions, Online Accounts

For software licenses, domain names, digital tools, platform accounts.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK, `uuid7()` |
| `asset_id` | UUID | FK → `asset.id`, unique, indexed |
| `updated_at` | datetime | |
| `platform` | str \| None | Service name (e.g. `"GitHub"`, `"Adobe"`) |
| `license_key` | str \| None | License key or activation code |
| `license_type` | str \| None | `"perpetual"` \| `"subscription"` \| `"open-source"` \| `"trial"` |
| `seat_count` | int \| None | Number of licensed seats/devices |
| `version` | str \| None | Software version |
| `download_url` | str \| None | Source or download URL |
| `subscription_id` | UUID \| None | FK → `subscription.id` — links to subscription if managed there |

---

## 4. Asset Lifecycle Events

### 4.1 `asset_event` Table

A lightweight audit/lifecycle log for assets. Each event records a significant change in the asset's life.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK, `uuid7()` |
| `asset_id` | UUID | FK → `asset.id`, indexed |
| `owner_id` | UUID | FK → `user.id`, indexed |
| `event_type` | str | See event types below |
| `occurred_on` | date \| None | When the event happened |
| `description` | str \| None | Details |
| `cost` | float \| None | Cost of the event (repair cost, sale price, appraisal) |
| `currency` | str \| None | ISO 4217 |
| `vendor` | str \| None | Who performed the service / buyer |
| `created_at` | datetime | |

### 4.2 Event Types (fixed-domain)

| Value | Description |
|---|---|
| `acquired` | Item was purchased, received, or found |
| `repaired` | Sent for repair or maintenance |
| `upgraded` | Upgraded or modified |
| `valued` | Appraised or revalued |
| `insured` | Insurance policy obtained or renewed |
| `lent` | Lent to someone |
| `returned` | Returned after lending |
| `sold` | Sold or transferred |
| `lost` | Lost or stolen |
| `disposed` | Discarded, recycled, or donated |
| `other` | Catch-all |

These are fixed-domain strings (not vocabulary terms) because lifecycle stages are well-defined and consistent across all asset types.

### 4.3 API Routes

```
GET    /api/v1/assets/{asset_id}/events/              List events for an asset
POST   /api/v1/assets/{asset_id}/events/              Log a new event
DELETE /api/v1/assets/{asset_id}/events/{event_id}    Delete an event
```

---

## 5. Vocabulary Restructuring

### 5.1 `asset-categories` — Make Hierarchical

Current: Flat list of categories.
New: Hierarchical vocabulary with top-level categories mapping to extension tables.

```
Physical (physical)
  ├── Electronics (electronics)
  ├── Vehicle (vehicle)
  ├── Appliance (appliance)
  ├── Tool & Equipment (tool)
  ├── Furniture (furniture)
  ├── Clothing & Accessories (clothing)
  ├── Musical Instrument (musical-instrument)
  ├── Sports Equipment (sports-equipment)
  ├── Book & Media (book)
  ├── Artwork & Collectible (artwork)
  └── Other Physical (other-physical)

Document (document)
  ├── Identity Document (identity)
  ├── Permit & License (permit)
  ├── Certificate (certificate)
  └── Other Document (other-document)

Financial (financial)
  ├── Bank Account (bank-account)
  ├── Investment (investment)
  ├── Property (property-financial)
  └── Other Financial (other-financial-cat)

Digital (digital)
  ├── Software License (software-license)
  ├── Domain & Hosting (domain-hosting)
  ├── Digital Account (digital-account)
  └── Other Digital (other-digital)

Other (other)
```

**Category → Extension Table Mapping:**

The application layer uses the top-level parent term to determine which extension table is relevant:

| Parent Category Slug | Extension Table |
|---|---|
| `physical` | `physical_asset` |
| `document` | `document_asset` |
| `financial` | `financial_asset` |
| `digital` | `digital_asset` |
| `other` | None (core fields only) |

This mapping is advisory — an asset can exist without its extension row, and the extension can be loaded regardless of category.

### 5.2 `asset-statuses` — Minor Update

Current terms are adequate. Consider adding:

| Term | Slug | New? |
|---|---|---|
| Active | `active` | existing |
| Sold | `sold` | existing |
| Retired | `retired` | existing |
| Lost | `lost` | existing |
| Lent | `lent` | existing |
| Donated | `donated` | existing |
| Broken | `broken` | existing |
| In Storage | `in-storage` | existing |
| Gifted | `gifted` | existing |
| Expired | `expired` | **new** — for documents, licenses, subscriptions |
| Pending | `pending` | **new** — for items on order / in transit |

### 5.3 New Vocabulary: `asset-conditions`

Replaces the hardcoded `condition: str` field.

| Term | Slug |
|---|---|
| New | `new` |
| Like New | `like-new` |
| Good | `good` |
| Fair | `fair` |
| Poor | `poor` |
| Damaged | `damaged` |
| Broken | `broken` |
| Refurbished | `refurbished` |
| For Parts Only | `for-parts` |

### 5.4 New Vocabulary: `document-asset-types`

| Term | Slug |
|---|---|
| Passport | `passport` |
| National ID | `national-id` |
| Driver's License | `drivers-license` |
| Visa | `visa` |
| Work Permit | `work-permit` |
| Residence Permit | `residence-permit` |
| Professional License | `professional-license` |
| Vehicle Registration | `vehicle-registration` |
| Property Deed | `property-deed` |
| Birth Certificate | `birth-certificate` |
| Marriage Certificate | `marriage-certificate` |
| Tax ID / PAN | `tax-id` |
| Health Card | `health-card` |
| Other | `other-document-asset` |

### 5.5 New Vocabulary: `financial-account-types`

| Term | Slug |
|---|---|
| Savings Account | `savings-account` |
| Current / Checking | `checking-account` |
| Fixed Deposit | `fixed-deposit` |
| Recurring Deposit | `recurring-deposit` |
| Mutual Fund | `mutual-fund` |
| Stocks / Equities | `equities` |
| Retirement Fund | `retirement-fund` |
| Provident Fund | `provident-fund` |
| Credit Card | `credit-card` |
| Loan Account | `loan-account` |
| Cryptocurrency | `cryptocurrency` |
| Other | `other-financial-type` |

---

## 6. Warranty & Insurance Linking

The existing `TrackedRecord` model (if present) already handles warranties and insurance with an `asset_id` FK. The vocabularies `record-types` and `document-types` are already seeded with warranty and insurance terms.

For asset-level reminders about expiry dates:
- `document_asset.expiry_date` → the Reminder system can create auto-reminders
- Warranty and insurance tracking → continue using existing `TrackedRecord` or `Note` with tags

No new tables needed for this linkage.

---

## 7. API Changes

### 7.1 Asset Core Endpoints — Modified

```
GET    /api/v1/assets/                   List assets (unchanged route, modified response)
POST   /api/v1/assets/                   Create (modified request body)
GET    /api/v1/assets/{id}               Get one (supports ?include=physical,document,financial,digital)
PATCH  /api/v1/assets/{id}               Update (modified request body)
DELETE /api/v1/assets/{id}               Soft delete (unchanged)
```

### 7.2 Extension Endpoints — New

```
GET    /api/v1/assets/{id}/physical/     Get physical extension
POST   /api/v1/assets/{id}/physical/     Create or update physical extension
DELETE /api/v1/assets/{id}/physical/     Remove physical extension

GET    /api/v1/assets/{id}/document/     Get document extension
POST   /api/v1/assets/{id}/document/     Create or update document extension
DELETE /api/v1/assets/{id}/document/     Remove document extension

GET    /api/v1/assets/{id}/financial/    Get financial extension
POST   /api/v1/assets/{id}/financial/    Create or update financial extension
DELETE /api/v1/assets/{id}/financial/    Remove financial extension

GET    /api/v1/assets/{id}/digital/      Get digital extension
POST   /api/v1/assets/{id}/digital/      Create or update digital extension
DELETE /api/v1/assets/{id}/digital/      Remove digital extension
```

### 7.3 Schema Changes

**`AssetCreate`** — Remove: `serial_number`, `brand`, `model_number`, `color`, `condition`, `barcode`. Rename: `purchase_currency` → `purchase_price_currency`. Optionally accept inline extension data.

**`AssetUpdate`** — Same removals. Optionally accept inline extension updates.

**`AssetPublicRead`** — Remove deprecated fields from core. Add optional extension sections (loaded via `?include=`):
```python
class AssetPublicRead(BaseModel):
    # core fields...
    physical: PhysicalAssetPublic | None = None
    document: DocumentAssetPublic | None = None
    financial: FinancialAssetPublic | None = None
    digital: DigitalAssetPublic | None = None
```

---

## 8. Data Migration

### 8.1 Core Fields → Physical Extension

For each existing `asset` row where any of `serial_number`, `brand`, `model_number`, `color`, `condition`, `barcode` is non-null:

1. Create a `physical_asset` row linked to the asset
2. Copy: `serial_number`, `brand`, `model_number`, `color` directly
3. Map `barcode` → `identifier_value = barcode`, `identifier_type = null`
4. Map `condition` string → `condition_term_id`:

| Old `condition` value | New `asset-conditions` slug |
|---|---|
| `"new"` | `new` |
| `"used"` | `fair` |
| `"refurbished"` | `refurbished` |
| `"damaged"` | `damaged` |
| Other / null | null |

### 8.2 After Migration

Drop columns from `asset`: `serial_number`, `brand`, `model_number`, `color`, `condition`, `barcode`, `purchase_currency` (replaced by `purchase_price_currency`).

---

## 9. Comparison with Current Implementation

| Aspect | Current | Target |
|---|---|---|
| Core fields | 20 columns (many physical-only) | 14 universal columns |
| Physical details | In core table | `physical_asset` extension |
| Document details | Not supported | `document_asset` extension |
| Financial details | Not supported | `financial_asset` extension |
| Digital details | Not supported | `digital_asset` extension |
| Condition | Hardcoded string | Vocabulary-driven |
| Barcode | Single untyped field | Typed identifier (value + type) |
| Categories | Flat vocabulary | Hierarchical (maps to extensions) |
| Lifecycle tracking | Not supported | `asset_event` log |
| Extension loading | N/A | Opt-in via `?include=` |
