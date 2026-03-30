# AGENTS.md - ThirdRaven

## Mission and Scope
- ThirdRaven is a local-first personal ERP + AI knowledge base backend; AI integration is optional, not required for core behavior.
- Monorepo: `backend/` (FastAPI API), `frontend/` (Vite React app), `docs/` (VitePress).
- Most contributor changes happen in `backend/app/{api,crud,models,schemas}` plus `backend/tests`.

## Architecture That Matters
- App entry: `backend/app/main.py` wires CORS, lifespan DB ping, `/health`, and mounts `api_router` at `/api/v1`.
- Service boundary pattern: routers in `backend/app/api/v1/*.py` call domain CRUD in `backend/app/crud/*.py`; CRUD owns query/build logic.
- Router aggregation is centralized in `backend/app/api/v1/__init__.py`.
- Integrations (Raven/Ollama) are behind provider-style deps (`backend/app/core/deps.py` + `backend/app/integrations/`).

## Non-Negotiable Conventions
- Owner scope every query (or visibility scope for household sharing): see `_visibility_clause` in `backend/app/crud/person.py`.
- Never return raw SQLModel objects from endpoints; return schema DTOs (`Create`/`Update`/`Public`/`Slim`).
- Dependency injection uses `Annotated[..., Depends(...)]` with `get_session` and `get_current_user`.
- IDs use UUID v7 across models; preserve this when adding new tables.
- Soft delete core entities (e.g., person) via `deleted_at`, not hard delete (`soft_delete_person` in `backend/app/crud/person.py`).

## Domain Patterns You Should Reuse
- Person is split into core + extension tables; CRUD routes flat payload fields with `_split_fields` and `_build_*_section` helpers (`backend/app/crud/person.py`).
- Section loading is opt-in via `?include=...` and `all`; keep this behavior when extending person reads.
- Typed inputs use slugs/codes and are resolved to FK IDs in CRUD (`resolve_term_slug`, `resolve_optional_term_slug`, ISO resolvers).
- Many-to-many links use explicit junction models (examples: `PersonTag`, `PersonLanguage`, `EventPerson`, `PersonObservationTag`).
- Context package and relationship health live in `backend/app/crud/context_package.py` and power AI-facing summaries.

## Routing and API Gotchas
- Keep `/persons/relationship-health` declared before `/persons/{person_id}` in `backend/app/api/v1/persons.py`.
- Keep all new endpoints under `/api/v1/` and tag/group per domain router file.

## Daily Workflow
- Preferred root commands (see `Makefile`): `make install`, `make db-up`, `make dev-backend`, `make test`, `make lint`, `make format`.
- Backend direct commands: `cd backend && uv sync --group dev`, `fastapi dev app/main.py`, `alembic upgrade head`, `uv run pytest`.
- After model edits: generate + review migration in `backend/migrations/versions/`, then apply.
- Seed reference vocab/ISO data with `cd backend && uv run python seeds/seed_data.py`.

## Testing Reality in This Repo
- API tests mock at the router import boundary using `AsyncMock` + `patch` (example: `backend/tests/test_persons.py`).
- Use `app.dependency_overrides` for auth/session deps; avoid real DB in router tests.
- Test files mirror router domains (`backend/tests/test_persons.py`, `backend/tests/test_interactions.py`, etc.).

## Safe Change Checklist
- Update in this order: `models` -> migration -> `schemas` -> `crud` -> `api/v1` router -> tests -> docs.
- If adding a model, ensure it is imported so Alembic autogenerate sees it.
- When adding vocabulary-backed fields, add/confirm terms in `backend/seeds/seed_data.py` and resolve via CRUD helpers.

