# ThirdRaven — Backend

FastAPI Python backend for ThirdRaven. Provides the REST API, data persistence, JWT authentication, and AI context-package assembly.

> Part of the [ThirdRaven monorepo](../README.md).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.14+ (`uuid.uuid7` from stdlib) |
| Framework | FastAPI (async-first) |
| ORM / Validation | SQLModel (SQLAlchemy 2.0 + Pydantic v2) |
| Database | PostgreSQL in production, SQLite for dev |
| Migrations | Alembic |
| Auth | JWT via python-jose + bcrypt |
| Linting | Ruff (`target-version = "py314"`, line-length 88) |
| Testing | pytest + pytest-asyncio |
| Package manager | [uv](https://docs.astral.sh/uv/) |

---

## Setup

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- Docker (for PostgreSQL)

### 1. Install dependencies

```bash
cd backend
uv sync --group dev
```

### 2. Configure environment

Copy the example and fill in your values:

```bash
cp .env.example .env
```

```env
DATABASE_URL=postgresql+asyncpg://thirdraven:secret@localhost:5432/thirdraven_db
SECRET_KEY=your-secret-key-here
```

### 3. Start PostgreSQL

From the repo root:

```bash
docker-compose up -d
```

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Seed reference data (optional)

```bash
uv run python seeds/seed_data.py
```

This populates ~250 countries, ~200 languages, ~600 IANA timezones, and all vocabulary terms.

### 6. Start the dev server

```bash
fastapi dev app/main.py
```

Interactive API docs: `http://localhost:8000/docs`

---

## Development Commands

| Task | Command |
|---|---|
| Install deps | `uv sync --group dev` |
| Start server | `fastapi dev app/main.py` |
| Run tests | `uv run pytest` |
| Run tests (verbose) | `uv run pytest -v` |
| Lint (auto-fix) | `uv run ruff check . --fix` |
| Format | `uv run ruff format .` |
| Create migration | `alembic revision --autogenerate -m "message"` |
| Apply migrations | `alembic upgrade head` |
| Rollback one step | `alembic downgrade -1` |

---

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # One router file per resource domain (~32 routers)
│   ├── core/            # config.py, database.py, deps.py, security.py
│   ├── crud/            # Business logic — one file per domain (~27 modules)
│   ├── models/          # SQLModel table definitions (~30+ tables)
│   ├── schemas/         # Pydantic DTOs (Create / Update / Public / Slim)
│   ├── etl/             # ETL pipeline and import handlers
│   ├── integrations/    # RavenPair AI integration
│   └── main.py
├── migrations/          # Alembic version history
├── seeds/               # Reference data seeder
├── tests/               # pytest test suite (262 tests)
├── .env.example
├── alembic.ini
└── pyproject.toml
```

---

## Key API Endpoints

All routes are under `/api/v1/`.

### Authentication
```
POST /auth/register
POST /auth/login          → returns JWT
```

### People
```
POST   /persons
GET    /persons
GET    /persons/relationship-health    ← proactive nudge engine
GET    /persons/{id}?include=profile,professional,social,location,context,physical,personality
PATCH  /persons/{id}
DELETE /persons/{id}
GET    /persons/{id}/context-package   ← full AI context payload
```

### Person Sub-resources
```
/persons/{id}/interactions
/persons/{id}/observations
/persons/{id}/follow-ups
/persons/{id}/goals
/persons/{id}/life-events
/persons/{id}/significant-dates
/persons/{id}/organizations
```

### Other Resources
```
/organizations     — companies and groups linked to people
/events            — multi-person shared events
/assets            — owned hardware and software
/subscriptions     — recurring costs
/notes             — general-purpose notes (optional person link)
/tasks             — todos (optional person link)
/vocabularies      — managed vocabulary terms (slugs used throughout)
/iso-reference     — countries, languages, timezones (read-only)
```

---

## Architecture Patterns

### Database
- **Primary keys**: UUID v7 (`uuid.uuid7()`) — time-ordered, no extra dependency
- **Soft deletes**: Core entities use `deleted_at: datetime | None`
- **Vocabulary slugs**: Typed fields resolve string slugs to `term_id` FKs via `resolve_optional_term_slug()`
- **Junction tables**: Many-to-many via explicit models (e.g. `PersonTag`, `EventPerson`)

### API Design
- All endpoints owner-scoped: `where(Model.owner_id == owner_id)`
- Never return raw SQLModels — always use `Public` Pydantic response schemas
- DI via `Annotated[AsyncSession, Depends(get_session)]` and `Annotated[User, Depends(get_current_user)]`

### Person Extensions
Person profiles are 1:1 tables loaded on demand via `?include=profile,social,...` or `?include=all`. Each section has a `_build_*_section(db, row)` async helper in `app/crud/person.py`.

### Context Package
`GET /persons/{id}/context-package` assembles all knowledge into one prompt-ready payload including profile, relationships, organizations, interactions, dates, events, observations, follow-ups, and goals.

### Relationship Health
Computes health status from `last_contacted_on` and `contact_frequency_days`:

| Status | Meaning |
|---|---|
| `on-track` | Contacted within the frequency window |
| `due-soon` | Within 7 days of being overdue |
| `overdue` | Past the contact frequency deadline |
| `no-data` | No contact date or frequency configured |

---

## Testing

Tests live in `tests/`. The project uses `pytest` with `pytest-asyncio`.

- `AsyncMock` — mock the `AsyncSession` at the CRUD layer
- `app.dependency_overrides` — inject mock DB sessions and mock auth users
- Patch CRUD functions at the **API router layer** (not at the SQLAlchemy layer)

```bash
uv run pytest              # run all 262 tests
uv run pytest -v           # verbose output
uv run pytest tests/test_persons.py -v   # single file
```

---

## Environment Variables

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://thirdraven:secret@localhost:5432/thirdraven_db` | Full async DSN |
| `SECRET_KEY` | `changeme` | JWT signing key — **change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | 24 hours |
| `ALGORITHM` | `HS256` | JWT algorithm |
