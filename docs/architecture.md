# ThirdRaven — Architecture Reference

## Project Purpose

ThirdRaven is a self-hosted **Personal Entity & Relationship Manager (PERM)** — a "Personal ERP" that acts as a central source of truth for relationships, asset ownership, and recurring costs. It is designed to function fully offline without any external AI or cloud dependency.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.14+ |
| Framework | FastAPI (async-first) |
| ORM / Schemas | SQLModel (SQLAlchemy 2.0 + Pydantic v2) |
| Database | PostgreSQL (via `asyncpg`) |
| Migrations | Alembic |
| Linting / Formatting | Ruff |
| Auth | OAuth2 Password Bearer + JWT (python-jose) |
| Password Hashing | bcrypt |

---

## Folder Structure

```text
.
├── app/
│   ├── main.py                  # App factory, lifespan, health endpoint
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py      # Aggregates all routers
│   │       ├── auth.py          # Register, login
│   │       ├── persons.py       # Person CRUD + relationships + terms
│   │       ├── contacts.py      # Contact CRUD + relationships
│   │       ├── assets.py        # Asset CRUD
│   │       ├── interactions.py  # Interaction log (nested under persons)
│   │       ├── vocabularies.py  # Vocabulary + Term management
│   │       └── iso_reference.py # Countries, Languages, Timezones (read-only)
│   ├── core/
│   │   ├── config.py            # Pydantic Settings (DB URL, JWT secrets)
│   │   ├── database.py          # AsyncSession factory, get_db dependency
│   │   ├── security.py          # JWT creation/verification, password hashing
│   │   └── deps.py              # get_current_user dependency
│   ├── crud/
│   │   ├── user.py              # User lookup and creation
│   │   ├── person.py            # Complex: splits data across 6 tables
│   │   ├── contact.py           # Simple: single-table CRUD
│   │   ├── asset.py             # Asset + tag junction management
│   │   ├── interaction.py       # Interaction log (hard deletes)
│   │   ├── vocabulary.py        # Vocabulary + Term CRUD
│   │   ├── iso_reference.py     # ISO resolver functions
│   │   └── reference.py         # PersonTerm junction helpers
│   ├── models/
│   │   ├── user.py
│   │   ├── person.py
│   │   ├── contact.py
│   │   ├── asset.py
│   │   ├── interaction.py
│   │   ├── person_relationship.py
│   │   ├── relationship.py      # ContactRelationship
│   │   ├── person_extensions.py # PersonProfile, PersonProfessional, PersonSocial,
│   │   │                        # PersonLocation, PersonContext
│   │   ├── vocabulary.py        # Vocabulary, Term, PersonTag, PersonLanguage, AssetTag
│   │   ├── iso_reference.py     # Country, Language, Timezone
│   │   └── reference.py         # PersonTerm
│   └── schemas/
│       ├── user.py
│       ├── person.py
│       ├── contact.py
│       ├── asset.py
│       ├── interaction.py
│       ├── vocabulary.py
│       ├── iso_reference.py
│       └── reference.py
├── migrations/
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
├── seeds/
│   └── seed_data.py             # ISO tables + pre-defined vocabularies
├── tests/                       # Pytest async functional and unit tests
├── CLAUDE.md                    # Development standards
├── pyproject.toml
├── alembic.ini
└── docker-compose.yml           # PostgreSQL service
```

---

## Core Architectural Patterns

### 1. Async-First

All database operations use `AsyncSession` (SQLAlchemy async). The `get_db` dependency yields a session per request. Every CRUD function is `async def` and uses `await db.execute(...)`.

### 2. Soft Deletes

`Person`, `Contact`, and `Asset` have a `deleted_at: datetime | None` column. Deletion sets this timestamp rather than removing the row. All queries filter `deleted_at IS NULL` by default.

### 3. Never Return Raw SQLModels

All endpoints return Pydantic **PublicRead** or **Slim** schemas. Raw ORM objects are never returned directly. This prevents leaking internal IDs, hashed passwords, or structural metadata.

### 4. Dependency Injection

The `Annotated` pattern is used throughout:

```python
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
```

### 5. Schema Convention: Slugs In, Slim Objects Out

Request schemas accept human-readable strings — slugs for terms (e.g., `"friend"`), alpha-2 codes for countries (e.g., `"US"`), ISO codes for languages (e.g., `"en"`). The CRUD layer resolves these to UUIDs before writing.

Response schemas return slim nested objects instead of raw IDs:

| ID Field | Resolved Type |
|---|---|
| `category_term_id` | `TermSlim { id, name, slug }` |
| `nationality_country_id` | `CountrySlim { id, name, alpha2 }` |
| `language_id` | `LanguageSlim { id, name, iso_639_1 }` |

### 6. Person Extension Tables (Loaded On-Demand)

Person data is split across six tables: `person` (core), `person_profile`, `person_professional`, `person_social`, `person_location`, `person_context`. Extensions are only queried when explicitly requested via `?include=profile,professional,...`.

### 7. Junction Tables for Many-to-Many

| Relationship | Junction Table |
|---|---|
| Person ↔ Term (tags) | `person_tag` |
| Person ↔ Language | `person_language` |
| Asset ↔ Term (tags) | `asset_tag` |
| Person ↔ Term (ad-hoc) | `person_term` |

### 8. Slug Resolution Pattern

Before writing any FK that points to a `term`, `country`, `language`, or `timezone`, the CRUD layer calls a resolver:

```python
term_id = await resolve_term_slug(db, machine_name="relationship-types", slug="friend")
country_id = await resolve_country_alpha2(db, "US")
language_id = await resolve_language_code(db, "en")
timezone_id = await resolve_timezone_name(db, "America/New_York")
```

Resolvers raise HTTP 422 if the value is not found.

### 9. Versioned API Routes

All endpoints are prefixed with `/api/v1/`. The router aggregation lives in `app/api/v1/__init__.py`.

### 10. Integration Architecture (Raven-Bridge)

The system is designed to work 100% offline. Optional AI enrichment (RavenPair) can be enabled as a provider via the `Integrations` layer. Async background tasks handle external calls so the core API remains fast.
