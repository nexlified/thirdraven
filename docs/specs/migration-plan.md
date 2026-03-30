# Migration Plan

> ThirdRaven Entity Redesign — Migration Strategy
> Created: 2026-03-30 | Status: Draft
> Depends on: [person-entity-spec.md](person-entity-spec.md), [asset-entity-spec.md](asset-entity-spec.md)

---

## 1. Overview

The migration follows a **three-phase strategy** to avoid breaking changes:

1. **Phase 1 — Additive**: Create all new tables and columns. No existing tables are dropped or modified destructively.
2. **Phase 2 — Data Migration**: Python scripts move data from old structures to new ones.
3. **Phase 3 — Cleanup**: Drop old tables and columns after the application layer is updated.

---

## 2. Phase 1 — Additive Changes (Alembic)

### 2.1 New Tables

| Table | Model File | Priority |
|---|---|---|
| `life_event` | `app/models/life_event.py` | High |
| `life_event_person` | `app/models/life_event.py` | High |
| `physical_asset` | `app/models/asset_extensions.py` | High |
| `document_asset` | `app/models/asset_extensions.py` | High |
| `financial_asset` | `app/models/asset_extensions.py` | Medium |
| `digital_asset` | `app/models/asset_extensions.py` | Medium |
| `asset_event` | `app/models/asset_event.py` | Medium |
| `loan` | `app/models/loan.py` | Medium |
| `reminder` | `app/models/reminder.py` | Medium |

### 2.2 Column Additions

| Table | Column | Type | Notes |
|---|---|---|---|
| `person_significant_date` | `date_type_term_id` | UUID \| None | FK → `term.id`, nullable |
| `asset` | `purchase_price_currency` | str \| None | New column (data copied from `purchase_currency` in Phase 2) |

### 2.3 Column Modifications

| Table | Column | Change |
|---|---|---|
| `person_significant_date` | `label` | Make nullable (was required) |

### 2.4 Vocabulary Seeds

Run seed script to create or update:

**New vocabularies:**

| `machine_name` | `is_hierarchical` | `is_locked` | Terms count |
|---|---|---|---|
| `life-event-types` | yes | no | ~30 (9 categories + ~21 types) |
| `life-event-emotions` | no | no | 11 |
| `significant-date-types` | no | no | 11 |
| `asset-conditions` | no | no | 9 |
| `document-asset-types` | no | no | 14 |
| `financial-account-types` | no | no | 12 |

**Updated vocabularies:**

| `machine_name` | Change |
|---|---|
| `asset-categories` | Set `is_hierarchical = true`, restructure terms with parent-child hierarchy |
| `asset-statuses` | Add `expired` and `pending` terms |
| `observation-tags` | Add 6 terms: `physical-trait`, `interests`, `food-preference`, `dietary-restriction`, `personality`, `communication-style` |

---

## 3. Phase 2 — Data Migration (Python Scripts)

These run as one-off Python scripts, not Alembic migrations, because they involve complex business logic (term resolution, conditional row creation).

### 3.1 `person_life_event` → `life_event` + `life_event_person`

```
For each row in person_life_event:
    1. INSERT into life_event:
       - Copy: id, owner_id, event_type_term_id, title, description,
               occurred_on, occurred_year, metadata_, created_at, updated_at
       - Set new fields to null: emotion_term_id, cost, currency,
                                  duration_minutes, place
    2. INSERT into life_event_person:
       - life_event_id = new row id
       - person_id = old row's person_id
       - role = "primary"
```

### 3.2 `asset` fields → `physical_asset`

```
For each asset row WHERE any of (serial_number, brand, model_number,
                                  color, condition, barcode) IS NOT NULL:
    1. INSERT into physical_asset:
       - asset_id = asset.id
       - brand = asset.brand
       - model_number = asset.model_number
       - serial_number = asset.serial_number
       - identifier_value = asset.barcode
       - identifier_type = null (user classifies later)
       - color = asset.color
       - condition_term_id = resolve_condition(asset.condition):
           "new" → term "new"
           "used" → term "fair"
           "refurbished" → term "refurbished"
           "damaged" → term "damaged"
           other → null
       - dimensions, weight_grams, manufactured_year = null

    2. Copy asset.purchase_currency → asset.purchase_price_currency
```

### 3.3 `person_physical` → `person_observation`

```
For each person_physical row with any non-null field:
    For each non-null field:
        1. INSERT into person_observation:
           - person_id = person_physical.person_id
           - owner_id = (SELECT owner_id FROM person WHERE id = person_id)
           - body = formatted string (e.g. "Height: 172 cm")
           - source = "migrated"
           - is_sensitive = false
           - observed_on = null
           - context = null
        2. INSERT into person_observation_tag:
           - observation_id = new observation id
           - term_id = resolve("observation-tags", "physical-trait")
```

### 3.4 `person_personality` → `person_observation`

```
For each person_personality row with any non-null field:
    For each non-null field:
        1. INSERT into person_observation:
           - person_id, owner_id = as above
           - body = field value directly (or "Communication style: {term.name}")
           - source = "migrated"
           - is_sensitive = false
        2. INSERT into person_observation_tag:
           - term_id = resolve tag by field:
               interests → "interests"
               food_preferences → "food-preference"
               dietary_restrictions → "dietary-restriction"
               personality_notes → "personality"
               communication_style → "communication-style"
```

### 3.5 `person_significant_date.label` → `date_type_term_id`

```
For each person_significant_date row:
    Normalize label to lowercase, strip whitespace
    Match patterns:
        "birthday", "bday", "birth day" → resolve("significant-date-types", "birthday")
        "anniversary", "wedding anniversary" → resolve("significant-date-types", "wedding-anniversary")
        "work anniversary" → resolve("significant-date-types", "work-anniversary")
        "graduation" → resolve("significant-date-types", "graduation")

    If matched:
        SET date_type_term_id = resolved term id
    Else:
        Leave date_type_term_id = null (label preserved as fallback)
```

---

## 4. Phase 3 — Cleanup (Alembic)

Run **after** the application layer is fully updated to use new tables.

### 4.1 Drop Tables

| Table | Precondition |
|---|---|
| `person_physical` | All data migrated to observations |
| `person_personality` | All data migrated to observations |
| `person_life_event` | All data migrated to `life_event` + `life_event_person` |

### 4.2 Drop Columns from `asset`

| Column | Reason |
|---|---|
| `serial_number` | Moved to `physical_asset` |
| `brand` | Moved to `physical_asset` |
| `model_number` | Moved to `physical_asset` |
| `color` | Moved to `physical_asset` |
| `condition` | Replaced by `physical_asset.condition_term_id` |
| `barcode` | Replaced by `physical_asset.identifier_value` + `identifier_type` |
| `purchase_currency` | Replaced by `purchase_price_currency` |

---

## 5. API Endpoint Changes

### 5.1 New Endpoints

```
# Life Events
POST   /api/v1/life-events/
GET    /api/v1/life-events/
GET    /api/v1/life-events/{id}
PATCH  /api/v1/life-events/{id}
DELETE /api/v1/life-events/{id}
POST   /api/v1/life-events/{id}/participants/
DELETE /api/v1/life-events/{id}/participants/{person_id}

# Loans
GET    /api/v1/loans/
POST   /api/v1/loans/
GET    /api/v1/loans/{id}
PATCH  /api/v1/loans/{id}
DELETE /api/v1/loans/{id}
GET    /api/v1/persons/{person_id}/loans/

# Reminders
GET    /api/v1/reminders/
POST   /api/v1/reminders/
GET    /api/v1/reminders/{id}
PATCH  /api/v1/reminders/{id}
DELETE /api/v1/reminders/{id}
GET    /api/v1/persons/{person_id}/reminders/
GET    /api/v1/assets/{asset_id}/reminders/
GET    /api/v1/subscriptions/{sub_id}/reminders/

# Asset Extensions
GET/POST/DELETE /api/v1/assets/{id}/physical/
GET/POST/DELETE /api/v1/assets/{id}/document/
GET/POST/DELETE /api/v1/assets/{id}/financial/
GET/POST/DELETE /api/v1/assets/{id}/digital/

# Asset Lifecycle Events
GET    /api/v1/assets/{asset_id}/events/
POST   /api/v1/assets/{asset_id}/events/
DELETE /api/v1/assets/{asset_id}/events/{event_id}
```

### 5.2 Modified Endpoints

| Endpoint | Change |
|---|---|
| `GET /persons/{id}?include=` | Remove `physical` and `personality` as valid sections |
| `POST/PATCH /persons/` | Remove fields: `height_cm`, `eye_color`, `hair_color`, `blood_type`, `interests`, `food_preferences`, `dietary_restrictions`, `personality_notes`, `communication_style` |
| `GET /persons/schema` | Remove `eye_colors`, `hair_colors`, `communication_styles` from field options |
| `GET /persons/{id}/life-events/` | Response now includes `participants` array; query joins through `life_event_person` |
| `POST /persons/{id}/life-events/` | Creates via `life_event` with `participants: [{person_id, role: "primary"}]` |
| `GET/PATCH /persons/{id}/significant-dates/` | Add `date_type` (slug input / TermSlim output); `label` now optional |
| `GET /assets/` and `GET /assets/{id}` | Core response loses `serial_number`, `brand`, etc.; gains `?include=physical,document,financial,digital` |
| `POST/PATCH /assets/` | Request body loses deprecated fields; optionally accepts inline extension data |

### 5.3 Backward Compatibility

| Route | Behavior |
|---|---|
| `GET /persons/{id}/life-events/` | Continues working — joins `life_event` via `life_event_person` |
| `POST /persons/{id}/life-events/` | Continues working — creates `life_event` + junction row with `role = "primary"` |
| Existing `?include=physical` on persons | Returns 422 with descriptive error after Phase 3 |

---

## 6. Schema Changes Summary

### 6.1 Person Domain

**Removed from `PersonCreate` / `PersonUpdate`:**
```
height_cm, eye_color, hair_color, blood_type,
interests, food_preferences, dietary_restrictions,
personality_notes, communication_style
```

**Removed from `PersonExtended`:**
```
physical: PersonPhysicalPublic | None  # section removed
personality: PersonPersonalityPublic | None  # section removed
```

**Modified `SignificantDateCreate`:**
```python
# Before
label: str  # required

# After
date_type: str | None = None  # slug from significant-date-types
label: str | None = None       # free-text override
# Validation: at least one must be non-null
```

**New schemas:** `LifeEventCreate`, `LifeEventUpdate`, `LifeEventPublic`, `LoanCreate`, `LoanUpdate`, `LoanPublic`, `ReminderCreate`, `ReminderUpdate`, `ReminderPublic`

### 6.2 Asset Domain

**Removed from `AssetCreate` / `AssetUpdate` / `AssetPublicRead`:**
```
serial_number, brand, model_number, color, condition, barcode
```

**Renamed in `AssetCreate` / `AssetUpdate`:**
```
purchase_currency → purchase_price_currency
```

**Added to `AssetPublicRead` (optional sections via `?include=`):**
```python
physical: PhysicalAssetPublic | None = None
document: DocumentAssetPublic | None = None
financial: FinancialAssetPublic | None = None
digital: DigitalAssetPublic | None = None
```

**New schemas:** `PhysicalAssetCreate/Update/Public`, `DocumentAssetCreate/Update/Public`, `FinancialAssetCreate/Update/Public`, `DigitalAssetCreate/Update/Public`, `AssetEventCreate/Public`

---

## 7. CRUD Impact

### 7.1 Files to Modify

| File | Changes |
|---|---|
| `app/crud/person.py` | Remove `_build_physical_section()`, `_build_personality_section()`, `_PHYSICAL_FIELDS`, `_PERSONALITY_FIELDS` from `_split_fields()`, related slug resolution helpers |
| `app/crud/context_package.py` | Update life event query to join through `life_event_person` instead of direct `person_life_event` |
| `app/crud/asset.py` | Remove deprecated field handling; add section builder pattern for asset extensions |
| `app/crud/person_life_event.py` | Replace with `app/crud/life_event.py` |
| `app/schemas/person.py` | Remove physical/personality fields and sections |
| `app/schemas/asset.py` | Restructure for extensions |

### 7.2 New Files

| File | Contains |
|---|---|
| `app/models/life_event.py` | `LifeEvent`, `LifeEventPerson` |
| `app/models/asset_extensions.py` | `PhysicalAsset`, `DocumentAsset`, `FinancialAsset`, `DigitalAsset` |
| `app/models/asset_event.py` | `AssetEvent` |
| `app/models/loan.py` | `Loan` |
| `app/models/reminder.py` | `Reminder` |
| `app/crud/life_event.py` | Life event CRUD with participant management |
| `app/crud/loan.py` | Loan CRUD |
| `app/crud/reminder.py` | Reminder CRUD |
| `app/crud/asset_extensions.py` | Asset extension CRUD (section builders) |
| `app/api/v1/life_events.py` | Life event router |
| `app/api/v1/loans.py` | Loan router |
| `app/api/v1/reminders.py` | Reminder router |
| `app/schemas/life_event.py` | Life event schemas |
| `app/schemas/loan.py` | Loan schemas |
| `app/schemas/reminder.py` | Reminder schemas |
| `app/schemas/asset_extensions.py` | Asset extension schemas |
| `scripts/migrate_phase2.py` | Data migration script |

---

## 8. Context Package Impact

`crud/context_package.py: get_context_package()` assembles all person knowledge into one prompt-ready payload.

### Changes needed:

1. **Life events query**: Change from `SELECT ... FROM person_life_event WHERE person_id = ?` to `SELECT ... FROM life_event JOIN life_event_person ON ... WHERE life_event_person.person_id = ?`. The response now includes `participants` list.

2. **Physical/personality data**: Previously loaded from extension tables. Now naturally included in the existing observation aggregation — tagged observations with `physical-trait`, `interests`, etc. will appear in the observations section without code changes.

3. **No schema change needed**: `ContextPackage` already has `observations: list[...]` and `life_events: list[...]`. The content changes but the shape does not.

---

## 9. Test Impact

### 9.1 Expected Test Failures After Phase 1

- Tests referencing `PersonPhysical` / `PersonPersonality` models
- Tests passing `height_cm`, `eye_color`, etc. to `PersonCreate`
- Tests asserting `?include=physical` or `?include=personality`
- Tests referencing `person_life_event` table directly
- Asset tests passing `serial_number`, `brand`, etc. in create/update

### 9.2 New Tests Needed

- Life event CRUD with participants
- Life event query via person (junction join)
- Loan CRUD (create, update status, filter by direction)
- Reminder CRUD (create, mark done, filter by entity type, recurrence)
- Asset extension CRUD (create/update/delete each type)
- Asset event lifecycle logging
- Significant date with `date_type` slug resolution
- Observation migration data integrity
- Context package with new life event structure

---

## 10. Verification Checklist

After full implementation:

- [ ] `pytest` passes (all existing tests updated + new tests)
- [ ] `ruff check . --fix` and `ruff format .` clean
- [ ] Alembic migration applies cleanly to fresh DB
- [ ] Alembic migration applies cleanly to DB with existing data
- [ ] Data migration script runs without errors on test data
- [ ] `/docs` (Swagger) shows all new endpoints
- [ ] `GET /persons/{id}?include=all` returns without physical/personality sections
- [ ] `GET /persons/{id}/life-events/` returns events with participants
- [ ] `POST /life-events/` creates event with multiple participants
- [ ] `GET /assets/{id}?include=physical` returns physical extension
- [ ] `POST /assets/{id}/document/` creates document extension
- [ ] `GET /assets/{id}/events/` returns lifecycle log
- [ ] `POST /loans/` creates a loan with person link
- [ ] `POST /reminders/` creates a standalone reminder
- [ ] `POST /reminders/` with `person_id` creates a person-linked reminder
- [ ] `GET /persons/{id}/context-package` assembles correctly with new structure
- [ ] Vocabulary API returns hierarchical `life-event-types` and `asset-categories`
