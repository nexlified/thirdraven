# ThirdRaven Development Skill

## Purpose
This skill defines the required development practices for ThirdRaven contributors and coding agents.
Follow these rules for all backend, frontend, and migration changes.

## Repo Scope
- Monorepo structure: `backend/` (FastAPI + SQLModel), `frontend/` (Vite + React + TS), `docs/` (VitePress).
- All API routes must live under `/api/v1/`.
- Core API entrypoint: `backend/app/main.py`.

## Architecture Rules (Must Follow)
- Routers in `backend/app/api/v1/*.py` only orchestrate; query/build logic belongs in `backend/app/crud/*.py`.
- Never return raw SQLModel entities from endpoints; always return schema DTOs.
- Use dependency injection with `Annotated[..., Depends(...)]`.
- Scope data by owner (or household visibility clause where supported).
- Keep special route ordering constraints intact (example: `/persons/relationship-health` before `/persons/{person_id}`).

## Data and Modeling Rules
- Primary keys must use UUID v7.
- Core entities use soft delete (`deleted_at`) rather than hard delete.
- For typed fields, accept slugs/codes in API payloads and resolve to FKs in CRUD.
- Many-to-many relationships must use explicit junction tables.
- After model changes: add Alembic migration and review generated SQL before applying.

## Backend Change Order (Required)
- Update in this order: `models` -> migration -> `schemas` -> `crud` -> `api/v1 router` -> tests -> docs.
- Ensure new models are imported so Alembic can detect them.
- If vocabulary-backed fields are added, seed/verify terms in `backend/seeds/seed_data.py`.

## Frontend Rules
- Keep API contracts in `frontend/src/api/*.ts` with typed request/response models.
- Pages should call API modules; avoid direct `fetch` in page components.
- Keep forms aligned with backend payload shape (slug/code inputs where required).
- Settings must persist to backend preferences when authenticated (`/auth/me/preferences`), not only local storage.
- Auth flows must remain functional for login/register/forgot-password/reset-password.

## Testing and Validation Rules
- Backend API tests mock at router import boundary using `AsyncMock` + `patch`.
- Use `app.dependency_overrides` in router tests; avoid real DB for router-level tests.
- Frontend unit tests use **Vitest** + `@testing-library/react`; config is in `frontend/vite.config.ts` (import `defineConfig` from `'vitest/config'`, not `'vite'`).
- Frontend API client tests live at `frontend/src/api/*.test.ts`; use `vi.mock('./client')` and `vi.mocked(api.get).mockResolvedValue(...)`.
- Frontend changes must pass TypeScript build (`npm run build`) and lint (`npm run lint`) before merge.
- When adding major user flows, add or update Playwright coverage in `frontend/e2e/`.

## Environment Notes (Read Before Running Any Command)

`uv` is **not on the system PATH**. It lives inside the virtualenv at `backend/.venv/bin/uv`.
- Never run bare `uv`, `pytest`, `alembic`, or `ruff` — they will not be found.
- Always prefix backend commands with `backend/.venv/bin/uv run <cmd>` (from the repo root) or `../.venv/bin/uv run <cmd>` (from inside `backend/`).
- The system `python`/`python3` binaries cannot import app modules — they are not in the venv.
- Do **not** activate the venv manually; just use the full path prefix.

## Standard Commands
```bash
# repo root — orchestration (these work as-is via Makefile)
make install
make db-up
make test
make lint
make format

# backend — run from repo root using full uv path
backend/.venv/bin/uv run pytest                          # run all tests
backend/.venv/bin/uv run pytest tests/test_persons.py    # run single test file
backend/.venv/bin/uv run ruff check . --fix              # lint
backend/.venv/bin/uv run ruff format .                   # format
backend/.venv/bin/uv run alembic upgrade head            # apply migrations
backend/.venv/bin/uv run alembic revision --autogenerate -m "message"

# backend — if already inside backend/ directory
../.venv/bin/uv run pytest
../.venv/bin/uv run ruff check . --fix
../.venv/bin/uv run alembic upgrade head

# frontend — unit tests (Vitest)
cd frontend && npm run test:unit          # run once
cd frontend && npm run test:unit:watch    # watch mode

# frontend — E2E tests (Playwright)
cd frontend && npm test

# frontend — build / lint
cd frontend && npm run lint
cd frontend && npm run build
```

## Definition of Done
- Code follows service boundaries and DTO rules.
- Migrations are present and reviewed for model changes.
- Backend/frontend validation commands pass locally.
- Tests are added or updated for behavior changes.
- Docs and skill guidance are updated when conventions change.

