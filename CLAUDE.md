# CLAUDE.md — ThirdRaven: Personal Entity & Relationship Manager (PERM)

## Project Overview
A high-performance, self-hosted API for managing personal networks, financial ledgers, and asset lifecycles. Designed to be a "Personal ERP" that acts as a central source of truth for relationships, ownership, and recurring costs.

## Core Features
1. **Entity Management**: Comprehensive tracking of people and organizations with deep relationship mapping.
2. **Financial Ledger**: A contextual double-entry inspired ledger for tracking debts, gifts, and shared expenses.
3. **Asset & Product Catalog**: Inventory management for physical and digital goods (hardware, software, tools).
4. **Subscription Engine**: Tracking recurring costs, billing cycles, and automated renewal alerts.
5. **Event-Sourced History**: Every change to an entity or asset is logged to provide a chronological "Life Timeline."

## Tech Stack
- **Language**: Python 3.12+
- **Framework**: FastAPI (Async-first)
- **Data Layer**: SQLModel (SQLAlchemy 2.0 + Pydantic v2)
- **Migrations**: Alembic
- **Formatting/Linting**: Ruff (The Rust-based Python linter)

## Development Commands
- **Environment Setup**: `uv sync` (Recommended) or `pip install -e .`
- **Start Server**: `fastapi dev app/main.py`
- **Database Migrations**: 
    - Create: `alembic revision --autogenerate -m "message"`
    - Apply: `alembic upgrade head`
- **Quality Control**:
    - Format: `ruff format .`
    - Lint: `ruff check . --fix`
    - Test: `pytest`

## Integration Architecture (The Raven-Bridge)
- **Agnostic Core**: ThirdRaven must function 100% without an internet connection or external AI.
- **Provider Pattern**: Implement an `Integrations` layer where RavenPair can be toggled as a service provider.
- **Async Enrichment**: Use FastAPI background tasks to handle external AI requests so the user experience remains fast.

## Code Style & Architecture

### 1. API Design
- **Versioned Routes**: All endpoints reside under `/api/v1/`.
- **Response Schemas**: Never return raw SQLModels. Always use `PublicRead` Pydantic schemas to filter internal IDs or sensitive metadata.
- **Dependency Injection**: Use `Annotated` for DB sessions and Auth dependencies.

### 2. Database Patterns
- **Soft Deletes**: Implement a `deleted_at` timestamp for core entities rather than hard-deleting records.
- **Atomic Transactions**: Use context managers for financial ledger entries to ensure data integrity.
- **SQLite Optimization**: Use `PRAGMA foreign_keys = ON;` for local development.
 
### 3. Folder Structure
```text
.
├── app/
│   ├── api/v1/         # Domain-specific routers (contacts, ledger, assets)
│   ├── core/           # Security, Config, Logging
│   ├── crud/           # Business logic & DB operations
│   ├── models/         # SQLModel Table definitions
│   ├── schemas/        # Pydantic Request/Response DTOs
│   └── main.py         # App initialization
├── migrations/         # Alembic version history
├── tests/              # Functional and unit tests
├── CLAUDE.md           # Development standards (This file)
└── pyproject.toml      # Dependency and Tool configuration
