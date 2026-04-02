# ThirdRaven

[![Backend](https://github.com/nexlified/thirdraven/actions/workflows/backend.yml/badge.svg)](https://github.com/nexlified/thirdraven/actions/workflows/backend.yml)
[![Frontend](https://github.com/nexlified/thirdraven/actions/workflows/frontend.yml/badge.svg)](https://github.com/nexlified/thirdraven/actions/workflows/frontend.yml)
[![Docs](https://github.com/nexlified/thirdraven/actions/workflows/docs.yml/badge.svg)](https://github.com/nexlified/thirdraven/actions/workflows/docs.yml)

A self-hosted personal relationship and knowledge management system — your private "Personal ERP" for tracking people, organizations, interactions, finances, and assets. Built to serve as the data backbone for an AI companion (RavenPair).

This is a **monorepo** containing three sub-packages:

| Directory | Description |
|---|---|
| [`backend/`](./backend) | FastAPI Python API (the core data engine) |
| [`frontend/`](./frontend) | Vite + React + TypeScript SPA |
| [`docs/`](./docs) | VitePress documentation site |

---

## What It Is

ThirdRaven stores everything you know about the people in your life: how you met, where they work, what they care about, what you've discussed, what you owe each other, and what follow-ups you've promised. It also tracks your assets, subscriptions, and recurring costs. All data stays local — no cloud, no third-party services required.

The API is designed to feed a personal AI companion with a rich, structured context package, enabling it to surface timely reminders, relationship health alerts, and conversational context.

---

## Repository Structure

```
thirdraven/
├── backend/     ← FastAPI Python API (core data engine)
├── frontend/    ← Vite + React + TypeScript SPA
├── docs/        ← VitePress documentation site
├── docker-compose.yml
└── Makefile     ← root orchestration (install, test, lint, etc.)
```

---

## Core Domains

| Domain | What it tracks |
|---|---|
| **People** | Profiles, relationships, personality, physical attributes, contact intelligence |
| **Organizations** | Companies, groups — linked to people with roles and tenure |
| **Interactions** | Every conversation, meeting, or touchpoint logged against a person |
| **Observations** | Freeform episodic notes (episodic memory for the AI) |
| **Follow-ups** | Pending actions and commitments tied to a person |
| **Goals** | Aspirations, fears, current focus areas, and learning goals per person |
| **Life Events** | Milestones and significant dates (birthdays, anniversaries) |
| **Multi-person Events** | Shared events with multiple attendees |
| **Notes & Tasks** | General-purpose notes and tasks (optionally linked to a person) |
| **Assets** | Physical and digital goods you own |
| **Subscriptions** | Recurring costs with billing cycle tracking |
| **Financial Ledger** | Debts, gifts, and shared expenses between people |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.14+ |
| Framework | FastAPI (async-first) |
| ORM / Validation | SQLModel (SQLAlchemy 2.0 + Pydantic v2) |
| Database | PostgreSQL (via Docker) or SQLite for local dev |
| Migrations | Alembic |
| Auth | JWT (python-jose + bcrypt) |
| Linting | Ruff |
| Frontend | Vite + React 19 + TypeScript |
| Docs | VitePress |

---

## Getting Started

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Node.js 18+ (for frontend and docs)
- Docker (for PostgreSQL)

### 1. Clone and install all dependencies

```bash
git clone https://github.com/nexlified/thirdraven.git
cd thirdraven
make install
```

### 2. Start the database

```bash
make db-up
```

### 3. Configure environment

Create a `.env` file in the `backend/` directory (copy from `.env.example`):

```env
DATABASE_URL=postgresql+asyncpg://thirdraven:secret@localhost:5432/thirdraven_db
SECRET_KEY=your-secret-key-here
```

### 4. Run migrations

```bash
make db-migrate
```

### 5. Seed reference data (optional)

```bash
make db-seed
```

### 6. Start the development servers

```bash
make dev-backend    # FastAPI on http://localhost:8000/docs
make dev-frontend   # React on http://localhost:5173
make dev-docs       # VitePress on http://localhost:5173 (separate port)
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

### Person Sub-resources (all follow the same CRUD pattern)
```
/persons/{id}/interactions
/persons/{id}/observations
/persons/{id}/follow-ups
/persons/{id}/goals
/persons/{id}/life-events
/persons/{id}/significant-dates
/persons/{id}/organizations
```

### Organizations
```
POST/GET/PATCH/DELETE  /organizations
```

### Events
```
POST/GET/PATCH/DELETE  /events
POST/GET/DELETE        /events/{id}/persons
```

### Other Resources
```
/assets          — owned hardware and software
/subscriptions   — recurring costs
/notes           — general-purpose notes (optional person link)
/tasks           — todos (optional person link)
/vocabularies    — managed vocabulary terms (slugs used throughout)
/iso-reference   — countries, languages, timezones (read-only)
```

---

## Context Package

`GET /persons/{id}/context-package` returns a single structured payload ready for an AI prompt:

```json
{
  "person": { "...all profile sections..." },
  "relationships": [...],
  "organizations": [...],
  "recent_interactions": [...],
  "upcoming_dates": [...],
  "life_events": [...],
  "observations": [...],
  "pending_follow_ups": [...],
  "goals": [...],
  "generated_at": "2026-03-26T..."
}
```

## Relationship Health

`GET /persons/relationship-health` computes health status for every person based on `last_contacted_on` and `contact_frequency_days`:

| Status | Meaning |
|---|---|
| `on-track` | Contacted within the frequency window |
| `due-soon` | Within 7 days of being overdue |
| `overdue` | Past the contact frequency deadline |
| `no-data` | No contact date or frequency configured |

---

## Development

All common tasks are orchestrated from the root `Makefile`:

```bash
make install        # Install all deps (backend + frontend + docs)
make test           # Run backend pytest suite
make lint           # Ruff (backend) + ESLint (frontend)
make format         # Ruff format (backend)
make build          # Build frontend + docs for production

make db-up          # Start PostgreSQL via Docker
make db-down        # Stop PostgreSQL
make db-migrate     # Run Alembic migrations
make db-seed        # Seed reference data
```

See the individual sub-package READMEs for more detail:
- [backend/README.md](./backend/README.md)
- [frontend/README.md](./frontend/README.md)
- [docs/README.md](./docs/README.md)

---

## Project Structure

```
thirdraven/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI routers (one file per resource)
│   │   ├── core/            # Config, database session, auth deps, security
│   │   ├── crud/            # Business logic and DB operations
│   │   ├── models/          # SQLModel table definitions (UUID v7 PKs)
│   │   ├── schemas/         # Pydantic request/response DTOs
│   │   ├── etl/             # ETL pipeline and import handlers
│   │   ├── integrations/    # RavenPair AI integration
│   │   └── main.py
│   ├── migrations/          # Alembic version history
│   ├── seeds/               # Reference data seeders
│   ├── tests/               # pytest test suite (262 tests)
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/             # HTTP client modules
│   │   ├── components/      # Reusable React components
│   │   ├── pages/           # Page components
│   │   ├── context/         # React context (auth)
│   │   └── hooks/           # Custom hooks
│   └── package.json
├── docs/
│   ├── .vitepress/          # VitePress config
│   ├── specs/               # Technical specifications
│   └── *.md                 # Architecture, API reference, data models, etc.
├── docker-compose.yml       # PostgreSQL for local dev
└── Makefile                 # Root task orchestration
```

---

## Documentation

The full documentation site lives in `docs/` and is built with [VitePress](https://vitepress.dev). Run `make dev-docs` to serve it locally.

Included pages:
- `architecture.md` — system design and data flow
- `data-models.md` — full schema reference
- `api-reference.md` — endpoint details
- `development.md` — contributor guide
- `vocabulary-system.md` — how slugs and terms work

---

## License

Private / personal use.
