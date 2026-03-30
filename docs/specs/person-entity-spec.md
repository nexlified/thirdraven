# Person Entity Specification

> ThirdRaven Entity Redesign — Person Domain
> Created: 2026-03-30 | Status: Draft

---

## 1. Overview

This specification defines the target-state data model for the **Person** domain in ThirdRaven. It covers identity, contact information, relationships, life events, significant dates, observations, loans, and reminders.

**Design principles:**
- Composable over rigid — users define types via Vocabularies, not hardcoded enums
- Structured where it aids querying or computation; free-form where flexibility matters
- AI-optional — every feature works standalone; the context package is a read-only aggregation

---

## 2. Core `person` Table — No Changes

The core table is well-designed. All fields remain as-is.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK, `uuid7()` |
| `owner_id` | UUID | FK → `user.id`, indexed |
| `first_name` | str | required |
| `last_name` | str \| None | |
| `nickname` | str \| None | |
| `notes` | str \| None | free-text CRM notes |
| `closeness_level` | int \| None | 1–5 proximity score |
| `household_id` | UUID \| None | FK → `household.id` |
| `visibility` | str | `"private"` \| `"household"` |
| `is_placeholder` | bool | default `false` |
| `is_bot` | bool | default `false` |
| `created_at` | datetime | |
| `updated_at` | datetime | |
| `deleted_at` | datetime \| None | soft delete |

---

## 3. Extension Tables

### 3.1 Tables to Keep (unchanged)

**`person_profile`** — Structured identity data needed for age calculations, personalization, and regional logic.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id`, unique, indexed |
| `updated_at` | datetime | |
| `middle_name` | str \| None | |
| `prefix_term_id` | UUID \| None | FK → `term.id` (vocab: `name-prefixes`) |
| `date_of_birth` | date \| None | |
| `gender_term_id` | UUID \| None | FK → `term.id` (vocab: `genders`) |
| `nationality_country_id` | UUID \| None | FK → `country.id` |

**`person_professional`** — Company and job data queried for filtering and context.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id`, unique, indexed |
| `updated_at` | datetime | |
| `occupation_term_id` | UUID \| None | FK → `term.id` (vocab: `occupations`) |
| `company` | str \| None | |
| `job_title` | str \| None | |

**`person_location`** — Timezone for scheduling logic; addresses in separate table.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id`, unique, indexed |
| `updated_at` | datetime | |
| `timezone_id` | UUID \| None | FK → `timezone.id` |

**`person_context`** — Drives relationship health calculations and contact scheduling.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id`, unique, indexed |
| `updated_at` | datetime | |
| `how_we_met` | str \| None | |
| `first_met_on` | date \| None | |
| `last_contacted_on` | date \| None | auto-updated by interaction pipeline |
| `contact_frequency_days` | int \| None | target frequency for relationship health |
| `preferred_contact_term_id` | UUID \| None | FK → `term.id` (vocab: `contact-channels`) |
| `relationship_nature` | str \| None | `"personal"` \| `"professional"` \| `"mixed"` |

### 3.2 Tables to Remove

**`person_physical`** — DROP

Current fields: `height_cm`, `eye_color_term_id`, `hair_color_term_id`, `blood_type`

**Reason:** Niche fields that most contacts will never populate. No computed feature depends on them. They are better expressed as tagged observations, which are flexible and searchable.

**`person_personality`** — DROP

Current fields: `interests`, `food_preferences`, `dietary_restrictions`, `personality_notes`, `communication_style_term_id`

**Reason:** All free-text or open-ended descriptors with no structured queries against them. These are archetypal observation data — things you learn about a person over time.

### 3.3 Data Migration for Removed Tables

Before dropping, migrate existing data to `PersonObservation`:

**From `person_physical`:**

| Source field | Observation body | Tag (from `observation-tags` vocab) |
|---|---|---|
| `height_cm` | `"Height: {value} cm"` | `physical-trait` |
| `eye_color_term_id` | `"Eye colour: {term.name}"` | `physical-trait` |
| `hair_color_term_id` | `"Hair colour: {term.name}"` | `physical-trait` |
| `blood_type` | `"Blood type: {value}"` | `physical-trait` |

**From `person_personality`:**

| Source field | Observation body | Tag |
|---|---|---|
| `interests` | body = value directly | `interests` |
| `food_preferences` | body = value directly | `food-preference` |
| `dietary_restrictions` | body = value directly | `dietary-restriction` |
| `personality_notes` | body = value directly | `personality` |
| `communication_style_term_id` | `"Communication style: {term.name}"` | `communication-style` |

All migrated observations set `source = "migrated"` and `is_sensitive = false`.

### 3.4 Multi-value Tables (unchanged)

**`person_channel`** — Contact methods (email, phone, social handles). Already composable with free-form `type` field. No changes needed.

**`person_address`** — Physical/mailing addresses with country FK and geo coordinates. No changes needed.

---

## 4. Relationships — No Changes

**`person_relationship`** — Directed edges with vocabulary-typed labels and `inverse_id` for bidirectional pairing. Already uses hierarchical `relationship-types` vocabulary with `reverse_slug`. Well-designed, no changes needed.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `from_person_id` | UUID | FK → `person.id` |
| `to_person_id` | UUID | FK → `person.id` |
| `label_term_id` | UUID | FK → `term.id` (vocab: `relationship-types`) |
| `inverse_id` | UUID \| None | FK → `person_relationship.id` |
| `created_at` | datetime | |

---

## 5. Life Events — Redesigned

### 5.1 Problem

The current `person_life_event` table:
- Ties each event to a single person (no multi-person support)
- Has a flat taxonomy (single `event_type_term_id`)
- Lacks fields for cost, place, emotion, duration
- Relies on a JSON `metadata_` catch-all for structured data

### 5.2 New `life_event` Table

Replaces `person_life_event`. Becomes a standalone entity with multi-person support.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK, `uuid7()` |
| `owner_id` | UUID | FK → `user.id`, indexed |
| `event_type_term_id` | UUID \| None | FK → `term.id` (vocab: `life-event-types`, hierarchical) |
| `title` | str | required — short summary |
| `description` | str \| None | longer narrative |
| `occurred_on` | date \| None | specific date |
| `occurred_year` | int \| None | year-only precision fallback |
| `emotion_term_id` | UUID \| None | FK → `term.id` (vocab: `life-event-emotions`) |
| `cost` | float \| None | monetary cost/value |
| `currency` | str \| None | ISO 4217 |
| `duration_minutes` | int \| None | how long it lasted |
| `place` | str \| None | free-text location |
| `metadata_` | dict \| None | JSON for arbitrary structured data |
| `created_at` | datetime | |
| `updated_at` | datetime | |

### 5.3 New `life_event_person` Junction Table

| Column | Type | Notes |
|---|---|---|
| `life_event_id` | UUID | FK → `life_event.id`, PK component |
| `person_id` | UUID | FK → `person.id`, PK component |
| `role` | str \| None | `"primary"` \| `"participant"` \| custom |

Composite PK: `(life_event_id, person_id)`.

### 5.4 Vocabulary: `life-event-types` (hierarchical)

Uses the existing `Term.parent_id` hierarchy. Parent terms are categories, child terms are specific event types.

```
Work & Career (work-career)
  ├── Got a new job (new-job)
  ├── Promotion (promotion)
  ├── Changed careers (career-change)
  ├── Started a business (started-business)
  ├── Retired (retired)
  └── Lost a job (lost-job)

Education (education)
  ├── Started school (started-school)
  ├── Graduated (graduated)
  └── Completed certification (certification)

Relationships (relationships)
  ├── Got married (got-married)
  ├── Got engaged (got-engaged)
  ├── Started dating (started-dating)
  ├── Separated (separated)
  ├── Had a child (had-child)
  └── Met someone important (met-someone)

Housing (housing)
  ├── Moved (moved)
  ├── Bought a home (bought-home)
  └── Started renting (started-renting)

Health (health)
  ├── Illness or injury (illness-injury)
  ├── Surgery (surgery)
  └── Recovery (recovery)

Travel & Adventure (travel)
  ├── Trip / Vacation (trip)
  ├── Moved to a new country (moved-country)
  └── Backpacking (backpacking)

Loss & Grief (loss-grief)
  ├── Bereavement (bereavement)
  └── Pet loss (pet-loss)

Achievements (achievements)
  ├── Award / Recognition (award)
  ├── Published work (published)
  └── Personal milestone (personal-milestone)

Other (other-event)
```

### 5.5 Vocabulary: `life-event-emotions`

Flat vocabulary for tagging the emotional tone of a life event.

| Term | Slug |
|---|---|
| Happy | `happy` |
| Proud | `proud` |
| Excited | `excited` |
| Grateful | `grateful` |
| Nostalgic | `nostalgic` |
| Bittersweet | `bittersweet` |
| Sad | `sad` |
| Difficult | `difficult` |
| Anxious | `anxious` |
| Relieved | `relieved` |
| Neutral | `neutral` |

### 5.6 API Routes

```
POST   /api/v1/life-events/                              Create (with participants list)
GET    /api/v1/life-events/                              List owner's life events
GET    /api/v1/life-events/{id}                          Get one
PATCH  /api/v1/life-events/{id}                          Update
DELETE /api/v1/life-events/{id}                          Soft delete

POST   /api/v1/life-events/{id}/participants/            Add participant
DELETE /api/v1/life-events/{id}/participants/{person_id}  Remove participant

GET    /api/v1/persons/{person_id}/life-events/          List events for a person (backward compat)
```

### 5.7 Migration from `person_life_event`

For each existing row:
1. Insert into `life_event` with all fields except `person_id`
2. Insert into `life_event_person` with `person_id` from old row, `role = "primary"`

---

## 6. Significant Dates — Improved

### 6.1 Problem

`PersonSignificantDate.label` is free-text. No consistency (`"bday"` vs `"Birthday"`), no structured queries ("find all contacts with a birthday this month").

### 6.2 Updated `person_significant_date` Table

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK, `uuid7()` |
| `person_id` | UUID | FK → `person.id`, indexed |
| `date_type_term_id` | UUID \| None | FK → `term.id` (vocab: `significant-date-types`) — **NEW** |
| `label` | str \| None | Free-text override — **now nullable** |
| `month` | int | 1–12 |
| `day` | int | 1–31 |
| `year` | int \| None | |
| `recurs_annually` | bool | default `true` |
| `notes` | str \| None | |
| `created_at` | datetime | |
| `updated_at` | datetime | |

**Rule:** At least one of `date_type_term_id` or `label` must be non-null (enforced at application layer).

### 6.3 Vocabulary: `significant-date-types`

| Term | Slug |
|---|---|
| Birthday | `birthday` |
| Wedding Anniversary | `wedding-anniversary` |
| Work Anniversary | `work-anniversary` |
| Graduation | `graduation` |
| Memorial Day | `memorial-day` |
| Name Day | `name-day` |
| First Meeting | `first-meeting` |
| Moved In Together | `moved-in-together` |
| Engagement | `engagement` |
| Divorce / Separation | `separation` |
| Other | `other-date` |

### 6.4 Migration

Resolve existing `label` values to `date_type_term_id`:
- `"birthday"`, `"Birthday"`, `"bday"` → `birthday` term
- `"anniversary"`, `"Wedding Anniversary"` → `wedding-anniversary` term
- Unresolvable labels: keep `label` as-is, leave `date_type_term_id` null

---

## 7. Observations — Enhanced Tagging

No structural changes to `PersonObservation` or `PersonObservationTag`. The model already supports tagged free-text notes with `body`, `observed_on`, `source`, `context`, `is_sensitive`.

### 7.1 New Tags for `observation-tags` Vocabulary

These tags absorb the data previously stored in PersonPhysical and PersonPersonality:

| Term | Slug | Purpose |
|---|---|---|
| Physical Trait | `physical-trait` | Height, eye color, hair color, blood type |
| Interests | `interests` | Hobbies, interests |
| Food Preference | `food-preference` | Favorite foods, cuisines |
| Dietary Restriction | `dietary-restriction` | Allergies, dietary needs |
| Personality | `personality` | Personality notes, traits |
| Communication Style | `communication-style` | How they prefer to communicate |

---

## 8. Follow-Ups — No Changes

`PersonFollowUp` remains as-is. It carries richer relationship context (body, interaction linkage, cleared_at workflow) than the new Reminder model. Follow-ups are a person-scoped CRM concept; reminders are a broader time-based alerting system.

---

## 9. Goals — No Changes

`PersonGoal` remains as-is. Goal types (`aspiration`, `fear`, `current-focus`, `learning`) are a small fixed set appropriate for AI context assembly.

---

## 10. New: Loan Model

### 10.1 Purpose

Track informal loans between the owner and contacts: money lent/borrowed, items lent/borrowed.

### 10.2 `loan` Table

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK, `uuid7()` |
| `owner_id` | UUID | FK → `user.id`, indexed |
| `person_id` | UUID | FK → `person.id`, indexed |
| `direction` | str | `"lent"` (owner gave) \| `"borrowed"` (owner received) |
| `loan_type` | str | `"money"` \| `"item"` |
| `description` | str | What was lent/borrowed |
| `amount` | float \| None | For money loans |
| `currency` | str \| None | ISO 4217 |
| `item_name` | str \| None | For item loans |
| `loaned_on` | date \| None | When the loan started |
| `due_on` | date \| None | Expected return date |
| `returned_on` | date \| None | Actual return date — null = outstanding |
| `status` | str | `"outstanding"` \| `"returned"` \| `"forgiven"` \| `"disputed"` |
| `notes` | str \| None | |
| `created_at` | datetime | |
| `updated_at` | datetime | |
| `deleted_at` | datetime \| None | soft delete |

### 10.3 API Routes

```
GET    /api/v1/loans/                     List all loans (filterable by status, direction)
POST   /api/v1/loans/                     Create a loan
GET    /api/v1/loans/{id}                 Get one
PATCH  /api/v1/loans/{id}                 Update
DELETE /api/v1/loans/{id}                 Soft delete

GET    /api/v1/persons/{person_id}/loans/ Loans involving a specific person
```

### 10.4 Design Notes

- `direction`, `loan_type`, and `status` are fixed-domain strings validated at the application layer — not vocabulary terms. These are well-defined states that should not be user-extensible.
- A loan is always between the owner and one contact. For loans between contacts (not involving the owner), use observations or notes.

---

## 11. New: Reminder Model

### 11.1 Purpose

Centralized time-based reminder system. Can be linked to any entity or stand alone. Complements (not replaces) `PersonFollowUp`.

### 11.2 `reminder` Table

Uses nullable-FK polymorphism (same pattern as `Note` and `Task`).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK, `uuid7()` |
| `owner_id` | UUID | FK → `user.id`, indexed |
| `title` | str | Short description |
| `body` | str \| None | Additional detail |
| `due_at` | datetime | When the reminder fires |
| `remind_at` | datetime \| None | Notification time (if different from due_at) |
| `recurrence` | str \| None | `null` \| `"daily"` \| `"weekly"` \| `"monthly"` \| `"annual"` |
| `is_done` | bool | default `false` |
| `done_at` | datetime \| None | When marked done |
| `person_id` | UUID \| None | FK → `person.id` |
| `asset_id` | UUID \| None | FK → `asset.id` |
| `subscription_id` | UUID \| None | FK → `subscription.id` |
| `created_at` | datetime | |
| `updated_at` | datetime | |
| `deleted_at` | datetime \| None | soft delete |

### 11.3 Indexes

- `(owner_id, is_done)` — pending reminders query
- `(owner_id, due_at)` — upcoming reminders query
- `person_id`, `asset_id`, `subscription_id` — entity-scoped queries

### 11.4 API Routes

```
GET    /api/v1/reminders/                          List (filterable by is_done, entity type)
POST   /api/v1/reminders/                          Create
GET    /api/v1/reminders/{id}                      Get one
PATCH  /api/v1/reminders/{id}                      Update
DELETE /api/v1/reminders/{id}                      Soft delete

GET    /api/v1/persons/{person_id}/reminders/      Reminders linked to a person
GET    /api/v1/assets/{asset_id}/reminders/        Reminders linked to an asset
GET    /api/v1/subscriptions/{sub_id}/reminders/   Reminders linked to a subscription
```

### 11.5 Relationship with PersonFollowUp

Follow-ups remain separate — they have richer context (interaction linkage, cleared_at workflow, body text for relationship management). A follow-up with a `due_on` can optionally auto-create a Reminder at the application layer. The two systems coexist:

| | PersonFollowUp | Reminder |
|---|---|---|
| Scope | Person-only | Any entity or standalone |
| Use case | Relationship management | Time-based alerts |
| Rich fields | body, interaction_id, cleared_at | due_at, remind_at, recurrence |
| Recurrence | No | Yes |

---

## 12. Schema Impact Summary

### PersonCreate / PersonUpdate — Fields Removed

```
# Remove these fields from the flat create/update schemas:
height_cm, eye_color, hair_color, blood_type,
interests, food_preferences, dietary_restrictions,
personality_notes, communication_style
```

### PersonExtended — Sections Removed

Remove `physical` and `personality` from valid `?include=` values. Valid values become: `profile`, `professional`, `location`, `context`, `channels`.

### PersonFieldOptions — Options Removed

Remove from the schema endpoint: `eye_colors`, `hair_colors`, `communication_styles`.

### CRUD Impact

- Remove `_build_physical_section()` and `_build_personality_section()` from `crud/person.py`
- Remove `_PHYSICAL_FIELDS` and `_PERSONALITY_FIELDS` constant sets from `_split_fields()`
- Remove physical/personality slug resolution helpers

### Context Package Impact

`get_context_package()` in `crud/context_package.py`:
- Life events query changes from `person_life_event` direct join to `life_event` → `life_event_person` join
- Physical/personality data is now in observations — the existing observation aggregation will naturally include it
- No additional changes needed
