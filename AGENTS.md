# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. (`CLAUDE.md` is a symlink to `AGENTS.md`.)

Leggen is a self-hosted Open Banking dashboard: a Python CLI + FastAPI server (`leggen/`) and a React PWA frontend (`frontend/`). It syncs bank accounts and transactions from EnableBanking into SQLite, with categorization, analytics, Discord/Telegram notifications, and S3 backups.

## Setup for Development

### Prerequisites
- **uv** must be installed
- **Configuration file**: `cp config.example.toml config.toml` and edit it

### Generate Mock Database
```bash
uv run leggen --config config.toml generate_sample_db --database ./test-data.db --accounts 5 --transactions 100 --force
```

### Start the API Server
```bash
export LEGGEN_DATABASE_PATH=./test-data.db
export LEGGEN_CONFIG_FILE=./config.toml
uv run leggen server --reload
```
API at `http://localhost:8000`, docs at `http://localhost:8000/api/v1/docs`.

### Start the Frontend
```bash
cd frontend && npm install && npm run dev
```
Frontend dev server at `http://localhost:5173` (port 3000 is only the Docker nginx port), configured to connect to the API at `http://localhost:8000/api/v1`.

## Build/Lint/Test Commands

A `justfile` wraps the common dev commands: `just server`, `just frontend`, `just seed`, `just check`, `just test`, `just build`, `just release`. The underlying commands are listed below.

### Backend (Python)
- **Lint**: `uv run ruff check .`
- **Format**: `uv run ruff format .`
- **Type check**: `uv run mypy leggen --check-untyped-defs`
- **All checks**: `uv run pre-commit run --all-files`
- **Run all tests**: `uv run pytest`
- **Run single test**: `uv run pytest tests/unit/test_api_accounts.py::TestAccountsAPI::test_get_all_accounts_success -v`
- **Run tests by marker**: `uv run pytest -m "api"` (markers: `unit`, `integration`, `slow`, `api`, `cli`; `asyncio_mode = "auto"`)

### Frontend (React/TypeScript)
- **Dev server**: `cd frontend && npm run dev`
- **Build**: `cd frontend && npm run build`
- **Lint**: `cd frontend && npm run lint`

## Architecture

### CLI is an HTTP client, not a library
Nearly all business logic lives in the FastAPI server. CLI commands (`leggen/commands/`) call the running server over HTTP via `LeggenAPIClient` (`leggen/api_client.py`) — they fail if the server isn't up. Exceptions that run locally: `server`, `generate_auth_config`, `generate_sample_db`.

### CLI command discovery
`leggen/main.py` defines a custom Click group that discovers commands dynamically: dropping `foo.py` in `leggen/commands/` with a function named `foo` registers a `foo` command. A subdirectory becomes a command group when it has an `__init__.py` defining a Click group named after the directory (see `commands/bank/`); its command modules use plain `@click.command()`. Global options (`--config`, `--database`, `--api-url`, `--api-key`, …) all have `LEGGEN_*` env-var equivalents.

### Backend layering
Routes → services → repositories:
- `leggen/commands/server.py` — `create_app()` assembles the FastAPI app; the lifespan hook loads config, runs DB migrations, and starts the scheduler
- `leggen/api/routes/` — routers mounted under `/api/v1`; all except `auth` require authentication (JWT Bearer from the frontend login flow, or `X-API-Key` header for CLI/programmatic access — resolved in `leggen/api/dependencies/auth.py`)
- `leggen/api/models/` — Pydantic request/response models
- `leggen/services/` — business logic: `sync_service.py` (orchestrator), `enablebanking_service.py` (external API; auth is an RS256 JWT signed with the RSA key at config `key_path`), `notification_service.py`, `backup_service.py`, `data_processors.py` (keyword extraction for categorization lives in `leggen/utils/keywords.py`)
- `leggen/repositories/` — raw SQL against SQLite via stdlib `sqlite3` (no ORM). `db.py` provides the connection context manager; `ensure_tables()` in `repositories/__init__.py` creates tables at startup; schema changes are imperative `migrate_*_if_needed()` methods in `migration_repository.py` (no Alembic — add a migration method there when changing schema)

### Config and paths are singletons
- `leggen/utils/config.py` — `config` singleton, validated against the Pydantic model in `leggen/models/config.py`; also writes config back to disk (`update_section`)
- `leggen/utils/paths.py` — `path_manager` singleton resolving config dir and DB path from `LEGGEN_CONFIG_DIR` / `LEGGEN_DATABASE_PATH`
- Tests reset the `config` singleton's internal fields rather than replacing the instance (other modules hold it by reference) — see `tests/conftest.py`, which also generates a throwaway RSA keypair and test config at import time

### Sync flow
APScheduler (`leggen/background/scheduler.py`, cron from config, live-reschedulable via `PUT /api/v1/sync/schedule`) or `POST /api/v1/sync` → `SyncService.sync_all_accounts()` → fetch balances/transactions from EnableBanking → transform in `data_processors.py` → persist via repositories → fire notifications (transaction filters + account-expiry warnings).

### Frontend
- Vite + React + TypeScript + Tailwind + shadcn/ui, TanStack Router (file-based routes in `frontend/src/routes/`) and TanStack Query
- `frontend/src/routeTree.gen.ts` is generated by the router plugin — never edit by hand
- `frontend/src/lib/api.ts` — Axios instance; attaches JWT from localStorage, redirects to `/login` on 401
- `frontend/src/types/api.ts` is **hand-written**, manually mirrored from the Pydantic models in `leggen/api/models/` — update both sides when changing API shapes
- Contexts in `frontend/src/contexts/` (Auth, Theme, BalanceVisibility); layout in `frontend/src/routes/__root.tsx` + `SiteHeader.tsx`/`AppSidebar.tsx`

## Code Style Guidelines

### Python
- Type hints for all function parameters and return values
- Specific exceptions; loguru for logging
- `pathlib.Path` instead of `os.path`
- Click framework for CLI commands

### TypeScript/React
- Imports: React hooks first, then third-party, then local components/types
- `import type` for type-only imports
- Tailwind CSS with `clsx` for conditional classes; shadcn/ui components; lucide-react icons
- Data fetching with @tanstack/react-query
- Use the shadcn MCP tools when adding UI components to stay consistent with the existing design system

## Commits and Releases
- Conventional commits: `type(scope): Description starting with uppercase and ending with period.`
  - Scopes: `cli`, `api`, `frontend` (optional); types: `feat`, `fix`, `refactor` (avoid too many different types)
  - Example: `feat(frontend): Add support for S3 backups.`
  - Avoid specific numbers/counts or data-dependent information that may become outdated
- Pre-commit hooks (`pre-commit install`) run ruff check/format and mypy; when pre-commit fails, the commit is canceled
- Releases: `scripts/release.sh` (CalVer `YEAR.MONTH.MICRO`, git-cliff changelog, tag push triggers PyPI + Docker publishing)
- Never log sensitive data; use environment variables for secrets
