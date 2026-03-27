# ThirdRaven — Data Models Reference

All tables use UUID primary keys. Timestamps are `datetime` (UTC). Optional fields are `| None`.

---

## Core Entities

### `user`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `username` | str | unique, indexed |
| `email` | str | unique, indexed |
| `hashed_password` | str | bcrypt hash |
| `is_active` | bool | default: `True` |
| `created_at` | datetime | |

---

### `person`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK, `uuid7()` |
| `owner_id` | UUID | FK → `user.id`, indexed |
| `first_name` | str | required |
| `last_name` | str \| None | |
| `nickname` | str \| None | |
| `notes` | str \| None | free-text notes |
| `closeness_level` | int \| None | 1–5 proximity score |
| `household_id` | UUID \| None | FK → `household.id`; set when `visibility = household` |
| `visibility` | str | `"private"` (default) or `"household"` |
| `is_placeholder` | bool | auto-created from unknown sender, default `false` |
| `is_bot` | bool | automated sender flag, default `false` |
| `created_at` | datetime | |
| `updated_at` | datetime | |
| `deleted_at` | datetime \| None | soft delete — never hard-delete persons |

> `email` and `phone` are **not columns** — they are derived at query time from the person's primary `person_channel` entries.

---

### `asset`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `owner_id` | UUID | FK → `user.id`, indexed |
| `name` | str | |
| `category_term_id` | UUID | FK → `term.id` |
| `status_term_id` | UUID | FK → `term.id` |
| `description` | str \| None | |
| `serial_number` | str \| None | |
| `vendor` | str \| None | |
| `purchase_date` | date \| None | |
| `purchase_price` | float \| None | |
| `current_value` | float \| None | |
| `notes` | str \| None | |
| `created_at` | datetime | |
| `updated_at` | datetime | |
| `deleted_at` | datetime \| None | soft delete |

---

### `interaction`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id`, indexed |
| `owner_id` | UUID | FK → `user.id`, indexed |
| `interaction_type_id` | UUID \| None | FK → `term.id` |
| `term_id` | UUID \| None | FK → `term.id` (generic classifier) |
| `title` | str | |
| `occurred_on` | date \| None | |
| `notes` | str \| None | |
| `metadata_` | dict \| None | PostgreSQL JSON |
| `created_at` | datetime | |
| `updated_at` | datetime | |

> Interactions use **hard deletes** (no `deleted_at`).

---

## Person Extension Tables

All extension tables have a **unique, indexed** `person_id` FK. They are created lazily — only when data is provided — and loaded on-demand via `?include=`.

### `person_profile`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id`, unique |
| `middle_name` | str \| None | |
| `prefix_term_id` | UUID \| None | FK → `term.id` (vocab: `name-prefixes`) |
| `date_of_birth` | date \| None | |
| `gender_term_id` | UUID \| None | FK → `term.id` (vocab: `genders`) |
| `nationality_country_id` | UUID \| None | FK → `country.id` |
| `updated_at` | datetime | |

---

### `person_professional`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id`, unique |
| `occupation_term_id` | UUID \| None | FK → `term.id` (vocab: `occupations`) |
| `company` | str \| None | |
| `job_title` | str \| None | |
| `updated_at` | datetime | |

> LinkedIn URL and secondary phone are stored as `person_channel` rows, not here.

---

### `person_location`

Stores only the timezone. Addresses are in `person_address`.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id`, unique |
| `timezone_id` | UUID \| None | FK → `timezone.id` |
| `updated_at` | datetime | |

---

### `person_context`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id`, unique |
| `how_we_met` | str \| None | |
| `first_met_on` | date \| None | |
| `last_contacted_on` | date \| None | updated automatically on communication ingest |
| `contact_frequency_days` | int \| None | intended contact cadence in days |
| `preferred_contact_term_id` | UUID \| None | FK → `term.id` (vocab: `preferred-contact`) |
| `relationship_nature` | str \| None | `"personal"` \| `"professional"` \| `"mixed"` |
| `updated_at` | datetime | |

---

### `person_physical`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id`, unique |
| `height_cm` | float \| None | |
| `eye_color_term_id` | UUID \| None | FK → `term.id` (vocab: `eye-colors`) |
| `hair_color_term_id` | UUID \| None | FK → `term.id` (vocab: `hair-colors`) |
| `blood_type` | str \| None | free text, e.g. `"A+"` |
| `updated_at` | datetime | |

---

### `person_personality`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id`, unique |
| `interests` | str \| None | free text |
| `food_preferences` | str \| None | free text |
| `dietary_restrictions` | str \| None | free text |
| `personality_notes` | str \| None | free text |
| `communication_style_term_id` | UUID \| None | FK → `term.id` (vocab: `communication-styles`) |
| `updated_at` | datetime | |

---

## Many-per-Person Tables

Unlike the 1:1 extension tables above, these can have multiple rows per person.

### `person_channel`

Replaces the old `person_contact_method` and `person_social` tables. Any contact channel — email, phone, social handle, messaging app, website — is stored here with a free `type` string.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id`, indexed |
| `owner_id` | UUID | FK → `user.id` |
| `type` | str | `"email"` \| `"mobile"` \| `"phone"` \| `"whatsapp"` \| `"telegram"` \| `"discord"` \| `"twitter"` \| `"instagram"` \| `"github"` \| `"linkedin"` \| `"facebook"` \| `"website"` \| any custom string |
| `value` | str | The actual address, number, or handle |
| `label` | str \| None | Optional label: `"work"` \| `"personal"` \| etc. |
| `is_primary` | bool | Primary entry for its type — drives the `email`/`phone` shortcuts in the core response |
| `created_at` | datetime | |

---

### `person_address`

Replaces the old home/work address columns in `person_location`. Any number of addresses per person with a free `type` string.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id`, indexed |
| `owner_id` | UUID | FK → `user.id` |
| `type` | str | `"home"` \| `"work"` \| `"other"` \| any custom string |
| `street` | str \| None | |
| `city` | str \| None | |
| `postal_code` | str \| None | |
| `country_id` | UUID \| None | FK → `country.id` |
| `lat` | float \| None | Latitude |
| `lng` | float \| None | Longitude |
| `is_primary` | bool | Primary address for its type |
| `created_at` | datetime | |

---

## Relationships

### `person_relationship`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `from_person_id` | UUID | FK → `person.id`, indexed |
| `to_person_id` | UUID | FK → `person.id`, indexed |
| `label_term_id` | UUID | FK → `term.id` (vocab: `relationship-types`) |
| `created_at` | datetime | |

---

### `contact_relationship`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `from_contact_id` | UUID | FK → `contact.id`, indexed |
| `to_contact_id` | UUID | FK → `contact.id`, indexed |
| `label` | str | free-text (not term-resolved) |
| `created_at` | datetime | |

---

## Vocabulary System

### `vocabulary`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `name` | str | Human-readable display name |
| `machine_name` | str | URL-safe slug, unique, indexed |
| `description` | str \| None | |
| `is_hierarchical` | bool | default: `False` |
| `allows_new_terms` | bool | default: `True` |
| `is_locked` | bool | default: `False`; prevents deletion |
| `source_type` | str | default: `"internal"` |
| `external_provider` | str \| None | e.g., `"ravenbridge"` |
| `is_active` | bool | default: `True` |
| `created_at` | datetime | |

---

### `term`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `vocabulary_id` | UUID | FK → `vocabulary.id`, indexed |
| `name` | str | Human-readable display name |
| `slug` | str | URL-safe identifier; unique within vocabulary |
| `description` | str \| None | |
| `parent_id` | UUID \| None | FK → `term.id` (self-referential hierarchy) |
| `weight` | int | default: `0`; controls sort order |
| `external_id` | str \| None | ID from external provider |
| `metadata_` | dict \| None | PostgreSQL JSON; arbitrary key-value data |
| `is_active` | bool | default: `True` |
| `created_at` | datetime | |

---

## Junction Tables

### `person_tag`

| Column | Type | Notes |
|---|---|---|
| `person_id` | UUID | PK, FK → `person.id` |
| `term_id` | UUID | PK, FK → `term.id` (vocab: `person-tags`) |

---

### `person_language`

| Column | Type | Notes |
|---|---|---|
| `person_id` | UUID | PK, FK → `person.id` |
| `language_id` | UUID | PK, FK → `language.id` |

---

### `asset_tag`

| Column | Type | Notes |
|---|---|---|
| `asset_id` | UUID | PK, FK → `asset.id` |
| `term_id` | UUID | PK, FK → `term.id` (vocab: `asset-tags`) |

---

### `person_term`

Ad-hoc term associations for a person (e.g., interest tags, custom classifiers).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id` |
| `term_id` | UUID | FK → `term.id` |
| `context` | str \| None | Optional note about why this term applies |
| `created_at` | datetime | |

---

## ISO Reference Tables

These tables are **read-only at runtime** — populated once by the seed script, never modified via the API.

### `country`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `name` | str | Full English name |
| `alpha2` | str | ISO 3166-1 alpha-2, unique, indexed |
| `alpha3` | str | ISO 3166-1 alpha-3, unique, indexed |
| `numeric` | str | ISO numeric code |
| `calling_code` | str \| None | E.164 prefix (e.g., `"+1"`) |
| `region` | str \| None | e.g., `"Americas"` |
| `subregion` | str \| None | e.g., `"Northern America"` |
| `flag_emoji` | str \| None | Unicode flag emoji |
| `is_active` | bool | default: `True` |

---

### `language`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `name` | str | English name |
| `native_name` | str | Name in the language itself |
| `iso_639_1` | str | 2-letter code, unique, indexed |
| `iso_639_2` | str | 3-letter code, unique, indexed |
| `is_active` | bool | default: `True` |

---

### `timezone`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `name` | str | IANA tz name (e.g., `"America/New_York"`), unique, indexed |
| `utc_offset` | str | Standard offset (e.g., `"-05:00"`) |
| `utc_offset_dst` | str \| None | DST offset if applicable |
| `country_id` | UUID \| None | FK → `country.id` |
| `is_active` | bool | default: `True` |

---

## Entity Relationship Summary

```
user ──< person >─── person_profile          (1:1 extension — identity)
                 ├── person_professional     (1:1 extension — work)
                 ├── person_location         (1:1 extension — timezone only)
                 ├── person_context          (1:1 extension — relationship context)
                 ├── person_physical         (1:1 extension — physical traits)
                 ├── person_personality      (1:1 extension — personality & preferences)
                 ├── person_channel          (M — contact channels & social handles)
                 ├── person_address          (M — addresses by type)
                 ├── person_tag ──> term     (M:M — labels)
                 ├── person_language ──> language  (M:M — spoken languages)
                 ├── person_relationship (self-referential M:M)
                 ├── interaction
                 ├── person_observation
                 ├── person_follow_up
                 └── person_goal

user ──< asset >── asset_tag >── term

vocabulary ──< term (self-referential via parent_id)

country <── timezone
country <── person_profile (nationality_country_id)
country <── person_address (country_id)
language <── person_language
```

### 1:1 vs. many-per-person

| Table | Cardinality | Created |
|---|---|---|
| `person_profile` | 1:1 | lazily — only when profile data is provided |
| `person_professional` | 1:1 | lazily |
| `person_location` | 1:1 | lazily — holds only `timezone_id` |
| `person_context` | 1:1 | lazily; also auto-created on first communication |
| `person_physical` | 1:1 | lazily |
| `person_personality` | 1:1 | lazily |
| `person_channel` | many | one row per email/phone/handle/social |
| `person_address` | many | one row per address |
