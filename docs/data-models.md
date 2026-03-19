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
| `id` | UUID | PK |
| `owner_id` | UUID | FK → `user.id`, indexed |
| `first_name` | str | |
| `last_name` | str \| None | |
| `nickname` | str \| None | |
| `email` | str \| None | |
| `phone` | str \| None | |
| `notes` | str \| None | |
| `closeness_level` | int \| None | 1–10 proximity score |
| `created_at` | datetime | |
| `updated_at` | datetime | |
| `deleted_at` | datetime \| None | soft delete |

---

### `contact`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `owner_id` | UUID | FK → `user.id`, indexed |
| `first_name` | str | |
| `last_name` | str \| None | |
| `email` | str \| None | |
| `phone` | str \| None | |
| `notes` | str \| None | |
| `tags` | list[str] | PostgreSQL ARRAY |
| `created_at` | datetime | |
| `updated_at` | datetime | |
| `deleted_at` | datetime \| None | soft delete |

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
| `linkedin_url` | str \| None | |
| `phone_secondary` | str \| None | |
| `updated_at` | datetime | |

---

### `person_social`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id`, unique |
| `twitter_handle` | str \| None | |
| `instagram_handle` | str \| None | |
| `website_url` | str \| None | |
| `updated_at` | datetime | |

---

### `person_location`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `person_id` | UUID | FK → `person.id`, unique |
| `address_home` | str \| None | |
| `address_work` | str \| None | |
| `city` | str \| None | |
| `country_id` | UUID \| None | FK → `country.id` |
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
| `updated_at` | datetime | |

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
user ──< person >── person_profile
                 >── person_professional
                 >── person_social
                 >── person_location
                 >── person_context
                 >── person_tag >── term
                 >── person_language >── language
                 >── person_term >── term
                 >── person_relationship (self)
                 >── interaction

user ──< contact >── contact_relationship (self)

user ──< asset >── asset_tag >── term

vocabulary ──< term (self-referential via parent_id)

country <── timezone
country <── person_profile (nationality)
country <── person_location
language <── person_language
```
