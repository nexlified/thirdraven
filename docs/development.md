# ThirdRaven — Development Guide

ThirdRaven is a monorepo with three sub-packages: `backend/` (FastAPI), `frontend/` (Vite + React), and `docs/` (VitePress). All common tasks are orchestrated from the root `Makefile`.

## Prerequisites

- Python 3.14+
- [uv](https://github.com/astral-sh/uv)
- Node.js 18+
- npm (or bun)
- Docker (for PostgreSQL via `docker-compose.yml`)

---

## Quick Start

### 1. Install all dependencies

```bash
make install
```

This installs backend Python deps, frontend npm deps, and docs npm deps in one step.

### 2. Start PostgreSQL

```bash
make db-up
```

### 3. Configure backend environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and set DATABASE_URL and SECRET_KEY
```

Default connection string (works with the Docker service):
```
postgresql+asyncpg://thirdraven:secret@localhost:5432/thirdraven_db
```

### 4. Apply migrations

```bash
make db-migrate
```

### 5. Seed reference data

```bash
make db-seed
```

This populates:
- ~250 countries (ISO 3166-1)
- ~200 languages (ISO 639-1 / 639-2)
- ~600 IANA timezones
- All pre-defined vocabularies and their terms

### 6. Start the dev servers

```bash
make dev-backend    # FastAPI on http://localhost:8000/docs
make dev-frontend   # Vite React on http://localhost:5173
make dev-docs       # VitePress on http://localhost:5173 (separate port)
```

---

## Root Makefile Reference

| Command | Description |
|---|---|
| `make install` | Install all deps (backend + frontend + docs) |
| `make dev-backend` | Start FastAPI dev server |
| `make dev-frontend` | Start Vite dev server |
| `make dev-docs` | Start VitePress dev server |
| `make db-up` | Start PostgreSQL (Docker) |
| `make db-down` | Stop PostgreSQL |
| `make db-migrate` | Run Alembic migrations |
| `make db-seed` | Seed reference data |
| `make test` | Run backend pytest suite |
| `make lint` | Ruff (backend) + ESLint (frontend) |
| `make format` | Ruff format (backend) |
| `make build` | Build frontend + docs for production |

---

## Backend Development

```bash
cd backend
uv sync --group dev

fastapi dev app/main.py      # Start dev server

uv run pytest                # Run all 262 tests
uv run pytest -v             # Verbose output
uv run pytest tests/test_persons.py::test_create_person -v  # Single test

uv run ruff check . --fix    # Lint with auto-fix
uv run ruff format .         # Format code
```

### Migration Workflow

After modifying models in `app/models/`:

```bash
alembic revision --autogenerate -m "add subscription table"
```

Always inspect the generated file in `migrations/versions/` before running. Autogenerate can miss custom index names and data migrations.

```bash
alembic upgrade head     # Apply all pending migrations
alembic downgrade -1     # Roll back one step
```

---

## Frontend Development

```bash
cd frontend
npm install
npm run dev      # Start Vite dev server on http://localhost:5173
npm run build    # Build for production
npm run lint     # ESLint check
```

---

## Docs Development

```bash
cd docs
npm install
npm run docs:dev      # Start VitePress dev server
npm run docs:build    # Build static site
npm run docs:preview  # Preview production build
```

To add a new documentation page, create a `.md` file in `docs/` and register it in `docs/.vitepress/config.ts`.

---

## Testing Conventions

Tests live in `backend/tests/`. The project uses `pytest` with `pytest-asyncio` and `httpx`.

### Stack

- `AsyncMock` — mock the `AsyncSession` at the CRUD layer
- `app.dependency_overrides` — inject mock DB sessions and mock auth users
- Patch CRUD functions at the **API router layer** (not at the SQLAlchemy layer)

### Example pattern

```python
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
import pytest

from app.main import app
from app.core.deps import get_current_user
from app.models.user import User

FAKE_USER = User(id=uuid4(), username="test", email="t@t.com", hashed_password="x", is_active=True)

@pytest.fixture
def auth_override():
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    yield
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_person(auth_override):
    with patch("app.api.v1.persons.crud_person.create_person", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = PersonSlim(...)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/persons/", json={...}, headers={"Authorization": "Bearer x"})
        assert resp.status_code == 201
```

Key rules:
- Patch at the **import location** used by the router, not at the definition location.
- Use `AsyncMock` for all async CRUD functions.
- Use `app.dependency_overrides` to bypass real auth and DB connections.
- Never mock `AsyncSession` at the SQLAlchemy level — mock at the CRUD boundary.

---

## Environment Variables

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://thirdraven:secret@localhost:5432/thirdraven_db` | Full async DSN |
| `SECRET_KEY` | `changeme` | JWT signing key — **change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | 24 hours |
| `ALGORITHM` | `HS256` | JWT algorithm |

Set via a `backend/.env` file (loaded by `pydantic-settings`).

---

## Project Tooling

### Ruff (lint + format)

Configured in `backend/pyproject.toml`:
- Target: Python 3.14
- Line length: 88
- Enabled rule sets: `E`, `F`, `I` (isort), `UP` (pyupgrade), `B` (bugbear), `SIM` (simplify)

Run before committing:
```bash
cd backend && uv run ruff check . --fix && uv run ruff format .
```

### Alembic

Config file: `backend/alembic.ini`. The `env.py` imports all models via `app.models` to enable autogenerate.

If you add a new model file, import it in `app/models/__init__.py` so Alembic detects the table.
