# ThirdRaven — Development Guide

## Prerequisites

- Python 3.14+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Docker (for PostgreSQL via `docker-compose.yml`)

---

## Setup

### 1. Install dependencies

```bash
uv sync
```

Or without `uv`:
```bash
pip install -e .
```

### 2. Start PostgreSQL

```bash
docker compose up -d
```

Default connection (configured in `app/core/config.py`):
```
postgresql+asyncpg://thirdraven:secret@localhost:5432/thirdraven_db
```

Override via environment variable:
```bash
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"
```

### 3. Apply migrations

```bash
alembic upgrade head
```

### 4. Seed reference data

```bash
python -m seeds.seed_data
```

This populates:
- ~250 countries (ISO 3166-1)
- ~200 languages (ISO 639-1 / 639-2)
- ~600 IANA timezones
- All pre-defined vocabularies and their terms

### 5. Start the dev server

```bash
fastapi dev app/main.py
```

API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

## Development Commands

| Task | Command |
|---|---|
| Install deps | `uv sync` |
| Start server | `fastapi dev app/main.py` |
| Run tests | `pytest` |
| Run tests (verbose) | `pytest -v` |
| Lint (auto-fix) | `ruff check . --fix` |
| Format | `ruff format .` |
| Lint + format | `ruff check . --fix && ruff format .` |

---

## Migration Workflow

### Create a migration

After modifying models in `app/models/`:

```bash
alembic revision --autogenerate -m "add subscription table"
```

### Review before applying

Always inspect the generated file in `migrations/versions/` before running. Autogenerate can miss:
- Custom index names
- `PRAGMA` settings
- Data migrations

### Apply

```bash
alembic upgrade head
```

### Rollback one step

```bash
alembic downgrade -1
```

---

## Testing Conventions

Tests live in `tests/`. The project uses `pytest` with `pytest-asyncio` and `httpx`.

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

### Running a specific test file

```bash
pytest tests/test_persons.py -v
```

### Running a specific test

```bash
pytest tests/test_persons.py::test_create_person -v
```

---

## Environment Variables

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://thirdraven:secret@localhost:5432/thirdraven_db` | Full async DSN |
| `SECRET_KEY` | `changeme` | JWT signing key — **change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | 24 hours |
| `ALGORITHM` | `HS256` | JWT algorithm |

Set via shell export or a `.env` file (loaded by `pydantic-settings`).

---

## Project Tooling

### Ruff (lint + format)

Configured in `pyproject.toml`:
- Target: Python 3.14
- Line length: 88
- Enabled rule sets: `E`, `F`, `I` (isort), `UP` (pyupgrade), `B` (bugbear), `SIM` (simplify)

Run before committing:
```bash
ruff check . --fix && ruff format .
```

### Alembic

Config file: `alembic.ini`. The `env.py` imports all models via `app.models` to enable autogenerate.

If you add a new model file, import it in `app/models/__init__.py` so Alembic detects the table.
