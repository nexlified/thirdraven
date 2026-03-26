# ThirdRaven

A self-hosted personal relationship and knowledge management API — your private "Personal ERP" for tracking people, organizations, interactions, finances, and assets. Built to serve as the data backbone for an AI companion (RavenPair).

---

## What It Is

ThirdRaven stores everything you know about the people in your life: how you met, where they work, what they care about, what you've discussed, what you owe each other, and what follow-ups you've promised. It also tracks your assets, subscriptions, and recurring costs. All data stays local — no cloud, no third-party services required.

The API is designed to feed a personal AI companion with a rich, structured context package, enabling it to surface timely reminders, relationship health alerts, and conversational context.

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

- **Language**: Python 3.14+
- **Framework**: FastAPI (async-first)
- **ORM / Validation**: SQLModel (SQLAlchemy 2.0 + Pydantic v2)
- **Database**: PostgreSQL (via Docker) or SQLite for local dev
- **Migrations**: Alembic
- **Auth**: JWT (python-jose + bcrypt)
- **Linting**: Ruff

---

## Getting Started

### 1. Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Docker (for PostgreSQL)

### 2. Clone and install

```bash
git clone https://github.com/your-org/thirdraven.git
cd thirdraven
uv sync
```

### 3. Start the database

```bash
docker-compose up -d
```

### 4. Configure environment

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://thirdraven:secret@localhost:5432/thirdraven_db
SECRET_KEY=your-secret-key-here
```

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Seed reference data (optional)

```bash
python -m seeds.seed_data
```

### 7. Start the server

```bash
fastapi dev app/main.py
```

API docs available at `http://localhost:8000/docs`

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

```bash
# Format
uv run ruff format .

# Lint
uv run ruff check . --fix

# Test
uv run pytest

# Create a migration after model changes
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

---

## Project Structure

```
thirdraven/
├── app/
│   ├── api/v1/          # FastAPI routers (one file per resource)
│   ├── core/            # Config, database session, auth deps, security
│   ├── crud/            # Business logic and DB operations
│   ├── models/          # SQLModel table definitions (UUID v7 PKs)
│   ├── schemas/         # Pydantic request/response DTOs
│   └── main.py
├── migrations/          # Alembic version history
├── seeds/               # Reference data seeders
├── tests/               # pytest test suite
├── docs/                # Architecture and API reference docs
├── docker-compose.yml   # PostgreSQL for local dev
└── pyproject.toml
```

---

## Documentation

Additional docs in `/docs/`:
- `architecture.md` — system design and data flow
- `data-models.md` — full schema reference
- `api-reference.md` — endpoint details
- `development.md` — contributor guide
- `vocabulary-system.md` — how slugs and terms work

---

## License

Private / personal use.
