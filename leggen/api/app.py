"""Assembly of the FastAPI application.

`create_app()` is what the `server` command runs and what
`scripts/dump_openapi.py` introspects; the CLI module itself only knows how
to start uvicorn.
"""

from contextlib import asynccontextmanager
from importlib import metadata

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from leggen.api.dependencies.auth import get_current_user
from leggen.api.errors import register_exception_handlers, use_error_schema_in_openapi
from leggen.api.models.common import HealthStatus
from leggen.api.routes import (
    accounts,
    analytics,
    auth,
    backup,
    banks,
    categories,
    category_rules,
    notifications,
    sync,
    transactions,
)
from leggen.background.scheduler import scheduler
from leggen.repositories import run_migrations
from leggen.services.enablebanking_service import close_enablebanking_service
from leggen.services.rules import seed_default_category_rules
from leggen.utils.config import config

API_PREFIX = "/api/v1"

# Known placeholder values from config.example.toml; a server must not start
# with them in place.
_PLACEHOLDER_VALUES = {"YOUR_BCRYPT_HASH", "YOUR_API_KEY", "YOUR_JWT_SECRET"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting leggen server...")

    try:
        config.load_config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise

    auth_cfg = config.auth_config
    if not auth_cfg:
        raise RuntimeError(
            "Missing [auth] section in config. "
            "Run 'leggen generate-auth-config' to generate one."
        )
    placeholder_fields = [
        key
        for key in ("password_hash", "api_key", "jwt_secret")
        if auth_cfg.get(key) in _PLACEHOLDER_VALUES
    ]
    if placeholder_fields:
        raise RuntimeError(
            f"Placeholder auth values detected for: {', '.join(placeholder_fields)}. "
            "Run 'leggen generate-auth-config' to generate real values."
        )

    # Create the schema on a new database, or upgrade an existing one
    try:
        version = run_migrations()
        logger.info(f"Database schema at version {version}")
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        raise

    # A database that has never had category rules gets the builtin set
    seeded = seed_default_category_rules()
    if seeded:
        logger.info(f"Seeded {seeded} builtin category rules")

    scheduler.start()
    logger.info("Background scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down leggen server...")
    scheduler.shutdown()
    await close_enablebanking_service()


# Rendered at the top of the OpenAPI document. Written for a reader — human
# or agent — arriving with nothing but this URL and an API key.
API_DESCRIPTION = """\
Leggen syncs bank accounts and transactions from EnableBanking into a local
database and serves them, with categories, statistics and notifications.

## Authentication

Every endpoint except `/auth/login` and `/health` needs one of:

- `Authorization: Bearer <jwt>` — from `POST /auth/login` (the web app's flow)
- `X-API-Key: <key>` — the `auth.api_key` from the server's config, for the
  CLI and programmatic access

## Categorizing transactions with rules

Categories can be assigned by hand, or by **rules**: small Lua scripts that
receive a transaction as `tx` and return `true` when the category applies.
Rules run in priority order over every transaction without a manual category;
the first match wins. They run over new transactions on every sync and over
history on demand. Manual assignments are never overridden by a rule.

The loop for writing a rule, whether by hand or by an agent working this API:

1. `GET /category-rules/reference` — the `tx` fields, the stdlib and examples.
2. `GET /transactions?search=...` — find transactions the rule should cover.
3. `POST /category-rules/test` — run a draft against one of them; `log()`
   output comes back, so the script can print what it sees.
4. `POST /category-rules/preview` — every transaction the draft matches.
   Check this for false positives before going further.
5. `POST /category-rules` — save it, then `POST /category-rules/apply`
   (with `dry_run=true` first) to categorize history.

A rule can also set `exclude_from_stats` on the transactions it categorizes,
for things like transfers between the user's own accounts.

## Errors

Every error is `{detail, code, status, errors?}`: `detail` is a human-readable
string on every status including 422, `code` is machine-readable
(`NOT_FOUND`, `INVALID_RULE_SCRIPT`, ...).
"""

# Every router except auth sits behind authentication, tagged for the docs.
_PROTECTED_ROUTERS: list[tuple[APIRouter, str]] = [
    (banks.router, "banks"),
    (accounts.router, "accounts"),
    (transactions.router, "transactions"),
    (categories.router, "categories"),
    (category_rules.router, "category-rules"),
    (sync.router, "sync"),
    (notifications.router, "notifications"),
    (backup.router, "backup"),
    (analytics.router, "analytics"),
]


def _package_version() -> str:
    try:
        return metadata.version("leggen")
    except metadata.PackageNotFoundError:
        return "unknown"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Leggen API",
        description=API_DESCRIPTION,
        version=_package_version(),
        lifespan=lifespan,
        docs_url=f"{API_PREFIX}/docs",
        openapi_url=f"{API_PREFIX}/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        # Frontend container and dev servers. Vite falls through to the next
        # free port when 5173 is taken, so the nearby ports are allowed too.
        allow_origin_regex=r"http://localhost:(3000|517[0-9]|518[0-9])",
        allow_origins=["http://frontend:80"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Give every error response the same envelope
    register_exception_handlers(app)

    # Login is the one public router
    app.include_router(auth.router, prefix=API_PREFIX, tags=["auth"])

    protected = APIRouter(prefix=API_PREFIX, dependencies=[Depends(get_current_user)])
    for router, tag in _PROTECTED_ROUTERS:
        protected.include_router(router, tags=[tag])
    app.include_router(protected)

    @app.get(f"{API_PREFIX}/health", response_model=HealthStatus)
    async def health():
        """Health check endpoint for API connectivity"""
        try:
            return HealthStatus(
                status="healthy",
                config_loaded=config.is_loaded,
                version=app.version,
            )
        except Exception as e:
            # This endpoint is unauthenticated, so the failure reason stays in
            # the log; the status code is what callers act on.
            logger.error(f"Health check failed: {e}")
            return JSONResponse(status_code=503, content={"status": "unhealthy"})

    # Document the error envelope; must run once every route is registered
    use_error_schema_in_openapi(app)

    return app
