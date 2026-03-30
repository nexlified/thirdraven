# CLAUDE.md — ThirdRaven

## Project Overview

A self-hosted personal relationship and knowledge management API. Serves as the data backbone for a personal AI companion (RavenPair). All data is local-first — no cloud dependencies required.

**Two primary roles:**
1. **Personal ERP** — people, organizations, assets, subscriptions, financial ledger
2. **AI Knowledge Base** — episodic memory (observations), goals, follow-ups, context packages, relationship health

---

## Monorepo Layout

```
thirdraven/
├── backend/        ← FastAPI Python backend
├── frontend/       ← Vite + React + TypeScript SPA
├── docs/           ← VitePress documentation site
├── docker-compose.yml
└── Makefile        ← root orchestration (make install, make test, etc.)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.14+ (`uuid.uuid7` from stdlib) |
| Framework | FastAPI (async-first) |
| ORM / Validation | SQLModel (SQLAlchemy 2.0 + Pydantic v2) |
| Database | PostgreSQL in prod, SQLite for dev |
| Migrations | Alembic |
| Auth | JWT via python-jose + bcrypt |
| Linting | Ruff (`target-version = "py314"`, line-length 88) |
| Testing | pytest + pytest-asyncio (AsyncMock for all API tests) |
| Frontend | Vite + React + TypeScript |
| Docs | VitePress |

---

## Development Commands

```bash
# From repo root
make install        # install all deps (backend + frontend + docs)
make db-up          # start PostgreSQL
make dev-backend    # FastAPI on http://localhost:8000/docs
make dev-frontend   # Vite on http://localhost:5173
make dev-docs       # VitePress docs
make test           # run backend pytest
make lint           # ruff + eslint
make format         # ruff format

# Backend (cd backend first)
cd backend
uv sync --group dev
fastapi dev app/main.py
alembic revision --autogenerate -m "message"
alembic upgrade head
uv run ruff format .
uv run ruff check . --fix
uv run pytest                                   # 262 tests
```

---

## Code Style & Architecture

### 1. API Design
- All endpoints under `/api/v1/`
- Never return raw SQLModels — always use `Public` Pydantic response schemas
- Use `Annotated[AsyncSession, Depends(get_session)]` and `Annotated[User, Depends(get_current_user)]` for DI
- All queries are owner-scoped: `where(Model.owner_id == owner_id)`

### 2. Database Patterns
- **UUIDs**: All primary keys use `uuid.uuid7()` (time-ordered, no extra dependency)
- **Soft deletes**: Core entities use `deleted_at: datetime | None` — never hard-delete persons/orgs
- **Vocabulary system**: Typed fields resolve slugs to `term_id` FKs via `resolve_optional_term_slug(db, "vocab-name", slug)` — no hardcoded enums in DB
- **Junction tables**: Many-to-many via explicit models (e.g. `PersonTag`, `PersonObservationTag`, `EventPerson`)
- **FK resolution helpers**: `resolve_term_slug`, `resolve_optional_term_slug` (crud/vocabulary.py), `resolve_country_alpha2` (crud/iso_reference.py)

### 3. Folder Structure

```
backend/
├── app/
│   ├── api/v1/          # One router file per resource domain
│   ├── core/            # config.py, database.py, deps.py, security.py
│   ├── crud/            # Business logic — one file per domain
│   ├── models/          # SQLModel table definitions
│   ├── schemas/         # Pydantic DTOs (Create / Update / Public / Slim)
│   └── main.py
├── migrations/
├── seeds/
└── tests/
```

### 4. Naming Conventions

| Schema type | Suffix | Purpose |
|---|---|---|
| Input (create) | `Create` | POST body |
| Input (update) | `Update` | PATCH body, all fields optional |
| Response (full) | `Public` | Full detail response |
| Response (minimal) | `Slim` | Used inside nested objects |

---

## Domain Map

### People & Relationships
- `backend/app/models/person.py` — core `Person` model
- `backend/app/models/person_extensions.py` — 1:1 extension tables: `PersonProfile`, `PersonProfessional`, `PersonSocial`, `PersonLocation`, `PersonContext`
- `backend/app/models/person_relationship.py` — `PersonRelationship` (M:M self-referential)
- `backend/app/models/person_life_event.py` — `PersonLifeEvent`, `PersonSignificantDate`
- `backend/app/crud/person.py` — section builder pattern (`_build_*_section`), opt-in `?include=` param

### Knowledge Base (AI Companion Layer)
- `backend/app/models/observation.py` — `PersonObservation`, `PersonObservationTag`
- `backend/app/models/followup.py` — `PersonFollowUp`
- `backend/app/models/goal.py` — `PersonGoal` (types: aspiration / fear / current-focus / learning)
- `backend/app/models/organization.py` — `Organization`, `PersonOrganization`
- `backend/app/models/event.py` — `Event`, `EventPerson`
- `backend/app/crud/context_package.py` — `get_context_package` + `get_relationship_health`

### Other Domains
- `backend/app/models/interaction.py` — `Interaction`
- `backend/app/models/note.py` — `Note` (optional person link)
- `backend/app/models/task.py` — `Task` (optional person link)
- `backend/app/models/asset.py` — `Asset`
- `backend/app/models/asset_extensions.py` — `AssetWarranty`, `AssetInsurance`, `AssetService`
- `backend/app/models/loan.py` — `Loan`
- `backend/app/models/reminder.py` — `Reminder` (polymorphic FK to person/asset/subscription)
- `backend/app/models/subscription.py` — `Subscription`, `BillPayment`

---

## Key Patterns

### Section builder (person extensions)
Person extensions are 1:1 tables loaded on demand via `?include=profile,social,...` or `?include=all`.
Each section has a `_build_*_section(db, row)` async helper in `backend/app/crud/person.py`.

### Context Package
`GET /persons/{id}/context-package` assembles all knowledge into one prompt-ready payload.
Implemented in `backend/app/crud/context_package.py: get_context_package()`.

### Relationship Health
`GET /persons/relationship-health` computes status from `PersonContext.last_contacted_on` and `contact_frequency_days`.
**Must be defined before `GET /persons/{person_id}` in the router** to avoid FastAPI parsing "relationship-health" as a UUID.

### Vocabulary Slugs
All typed/categorized fields accept a string slug in Create/Update schemas and resolve to a `term_id` FK in the DB. Vocabulary groups used: `person-tags`, `org-types`, `industries`, `event-types`, `observation-tags`, `name-prefixes`, `genders`, `occupations`, `relationship-types`, `preferred-contact`, `life-event-types`, `life-event-emotions`, `significant-date-types`, `asset-categories`, `asset-statuses`, `asset-conditions`, `document-asset-types`, `financial-account-types`.

---

## Integration Architecture (Raven-Bridge)

- **Agnostic core**: ThirdRaven works 100% offline — no AI dependency
- **Provider pattern**: RavenPair plugs in as an optional `Integrations` provider
- **Async enrichment**: AI requests handled via FastAPI background tasks

---

## Testing

- All API tests use `AsyncMock` / `unittest.mock.patch` — no real DB in tests
- Test files mirror router files: `backend/tests/test_persons.py`, `backend/tests/test_interactions.py`, etc.
- Run: `cd backend && uv run pytest` (262 tests)
