# ThirdRaven — Vocabulary System

## Why Vocabulary / Term?

Early designs used Python `StrEnum` for fixed categories (asset status, gender, relationship type) and plain string arrays for tags. This approach had two problems:

1. **Rigidity** — Adding a new category required a code change, migration, and redeploy.
2. **No metadata** — Enums cannot carry descriptions, sort weights, hierarchy, or external provider IDs.

The vocabulary/term system replaces all of those patterns with a flexible, database-driven taxonomy. A **vocabulary** is a named set; a **term** is a member of that set. New terms can be added at runtime via the API — no code change required.

---

## Vocabulary Fields

| Field | Type | Purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `name` | str | Human-readable label (e.g., `"Relationship Types"`) |
| `machine_name` | str | URL-safe slug used in API paths (e.g., `"relationship-types"`) |
| `description` | str \| None | Optional explanation |
| `is_hierarchical` | bool | If `true`, terms may have `parent_id` set |
| `allows_new_terms` | bool | If `false`, only seed terms may be used (effectively read-only at runtime) |
| `is_locked` | bool | If `true`, the vocabulary cannot be deleted via the API |
| `source_type` | str | `"internal"` (default) or `"external"` |
| `external_provider` | str \| None | Name of the provider if `source_type = "external"` |
| `is_active` | bool | Soft visibility flag |
| `created_at` | datetime | |

---

## Term Fields

| Field | Type | Purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `vocabulary_id` | UUID | FK → vocabulary |
| `name` | str | Human-readable label (e.g., `"Best Friend"`) |
| `slug` | str | URL-safe identifier, unique **within** its vocabulary (e.g., `"best-friend"`) |
| `description` | str \| None | Optional explanation |
| `parent_id` | UUID \| None | FK → term (self-referential); used in hierarchical vocabs |
| `weight` | int | Sort weight; lower numbers sort first (default: `0`) |
| `external_id` | str \| None | ID from an external taxonomy provider |
| `metadata_` | dict \| None | Arbitrary JSON key-value data |
| `is_active` | bool | Soft visibility flag |
| `created_at` | datetime | |

The `(vocabulary_id, slug)` pair is unique — the same slug can exist in different vocabularies.

---

## The `resolve_term_slug()` Pattern

Any write operation that stores a term FK (e.g., `category_term_id`, `label_term_id`, `gender_term_id`) accepts a **slug string** in the request payload rather than a UUID. The CRUD layer resolves the slug to a UUID before writing:

```python
# app/crud/vocabulary.py
async def resolve_term_slug(
    db: AsyncSession,
    machine_name: str,
    slug: str,
) -> uuid.UUID:
    result = await db.execute(
        select(Term.id)
        .join(Vocabulary, Term.vocabulary_id == Vocabulary.id)
        .where(Vocabulary.machine_name == machine_name)
        .where(Term.slug == slug)
        .where(Term.is_active == True)
    )
    term_id = result.scalar_one_or_none()
    if not term_id:
        raise HTTPException(
            status_code=422,
            detail=f"Term '{slug}' not found in vocabulary '{machine_name}'"
        )
    return term_id
```

Usage example in `crud/asset.py`:
```python
category_term_id = await resolve_term_slug(db, "asset-categories", data.category)
status_term_id   = await resolve_term_slug(db, "asset-statuses", data.status)
```

---

## ISO Resolver Pattern

The ISO reference tables (Country, Language, Timezone) use the same principle but resolve standard codes instead of slugs:

```python
# Resolve by ISO 3166-1 alpha-2
country_id = await resolve_country_alpha2(db, "US")

# Resolve by ISO 639-1
language_id = await resolve_language_code(db, "en")

# Resolve by IANA timezone name
timezone_id = await resolve_timezone_name(db, "America/New_York")
```

All resolvers raise HTTP 422 if the code is not found.

---

## Seeded Vocabularies

The following vocabularies are created by `python -m seeds.seed_data`. All are `is_locked = true` to prevent accidental deletion.

| `machine_name` | Locked | Hierarchical | Example Terms |
|---|---|---|---|
| `person-tags` | yes | no | `friend`, `vip`, `mentor`, `colleague` |
| `relationship-types` | yes | no | `friend`, `family`, `colleague`, `acquaintance`, `mentor`, `mentee` |
| `name-prefixes` | yes | no | `mr`, `ms`, `mrs`, `dr`, `prof` |
| `genders` | yes | no | `male`, `female`, `non-binary`, `prefer-not-to-say` |
| `occupations` | yes | no | `software-engineer`, `designer`, `doctor`, `teacher` (100+ entries) |
| `asset-categories` | yes | no | `hardware`, `software`, `tool`, `vehicle`, `appliance` |
| `asset-statuses` | yes | no | `active`, `inactive`, `retired`, `lost`, `sold` |
| `asset-tags` | yes | no | `work`, `personal`, `shared`, `borrowed` |
| `interaction-types` | yes | no | `call`, `email`, `coffee`, `meeting`, `message`, `event` |

---

## How to Add New Terms at Runtime

No code change or migration required. Use the API:

```http
POST /api/v1/vocabularies/person-tags/terms
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Investor",
  "slug": "investor",
  "description": "People who have invested in my projects",
  "weight": 10
}
```

If the vocabulary has `allows_new_terms = false`, this operation is blocked.

---

## Hierarchical Terms

Set `is_hierarchical = true` on the vocabulary, then provide `parent_id` when creating child terms:

```http
POST /api/v1/vocabularies/occupations/terms
{
  "name": "Frontend Engineer",
  "slug": "frontend-engineer",
  "parent_id": "<uuid of software-engineer term>"
}
```

Filter terms by parent when listing:
```
GET /api/v1/vocabularies/occupations/terms?parent=software-engineer
```

---

## ISO Reference Tables vs. Vocabulary Terms

| Feature | Vocabulary / Term | ISO Tables |
|---|---|---|
| Managed by | API (runtime) | Seed script only |
| Identified by | `machine_name` + `slug` | Standard codes (`alpha2`, `iso_639_1`, IANA name) |
| Mutable | Yes (if `allows_new_terms`) | No |
| Use case | Custom taxonomies, tags, categories | Countries, languages, timezones |
| Resolver | `resolve_term_slug()` | `resolve_country_alpha2()`, etc. |
