import os
from contextlib import asynccontextmanager
from importlib import metadata

import click
import uvicorn
from fastapi import Depends, FastAPI
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
    notifications,
    sync,
    transactions,
)
from leggen.background.scheduler import scheduler
from leggen.repositories import MigrationRepository, ensure_tables
from leggen.services.enablebanking_service import close_enablebanking_service
from leggen.utils.config import config
from leggen.utils.paths import path_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting leggen server...")

    # Load configuration
    try:
        config.load_config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise

    # Validate auth configuration is present
    if not config.auth_config:
        raise RuntimeError(
            "Missing [auth] section in config. "
            "Run 'leggen generate-auth-config' to generate one."
        )

    # Reject known placeholder values from config.example.toml
    _PLACEHOLDER_VALUES = {"YOUR_BCRYPT_HASH", "YOUR_API_KEY", "YOUR_JWT_SECRET"}
    auth_cfg = config.auth_config
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

    # Ensure tables exist, then run schema/data migrations on legacy databases
    try:
        ensure_tables()
        migrations = MigrationRepository()
        await migrations.run_all_migrations()
        logger.info("Database migrations completed")
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        raise

    # Start background scheduler
    scheduler.start()
    logger.info("Background scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down leggen server...")
    scheduler.shutdown()
    await scheduler.close_services()
    await close_enablebanking_service()


def create_app() -> FastAPI:
    # Get version dynamically from package metadata
    try:
        version = metadata.version("leggen")
    except metadata.PackageNotFoundError:
        version = "unknown"

    app = FastAPI(
        title="Leggen API",
        description="Open Banking API for Leggen",
        version=version,
        lifespan=lifespan,
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://frontend:80",
        ],  # Frontend container and dev servers
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Give every error response the same envelope
    register_exception_handlers(app)

    # Include auth routes (public, no auth dependency)
    app.include_router(auth.router, prefix="/api/v1", tags=["auth"])

    # Include API routes (protected by auth)
    auth_deps = [Depends(get_current_user)]
    app.include_router(
        banks.router, prefix="/api/v1", tags=["banks"], dependencies=auth_deps
    )
    app.include_router(
        accounts.router, prefix="/api/v1", tags=["accounts"], dependencies=auth_deps
    )
    app.include_router(
        transactions.router,
        prefix="/api/v1",
        tags=["transactions"],
        dependencies=auth_deps,
    )
    app.include_router(
        categories.router,
        prefix="/api/v1",
        tags=["categories"],
        dependencies=auth_deps,
    )
    app.include_router(
        sync.router, prefix="/api/v1", tags=["sync"], dependencies=auth_deps
    )
    app.include_router(
        notifications.router,
        prefix="/api/v1",
        tags=["notifications"],
        dependencies=auth_deps,
    )
    app.include_router(
        backup.router, prefix="/api/v1", tags=["backup"], dependencies=auth_deps
    )
    app.include_router(
        analytics.router, prefix="/api/v1", tags=["analytics"], dependencies=auth_deps
    )

    @app.get("/api/v1/health", response_model=HealthStatus)
    async def health():
        """Health check endpoint for API connectivity"""
        try:
            config_loaded = config.is_loaded

            # Get version dynamically
            try:
                version = metadata.version("leggen")
            except metadata.PackageNotFoundError:
                version = "dev"

            return HealthStatus(
                status="healthy",
                config_loaded=config_loaded,
                version=version,
            )
        except Exception as e:
            # This endpoint is unauthenticated, so the failure reason stays in
            # the log; the status code is what callers act on.
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy"},
            )

    # Document the error envelope; must run once every route is registered
    use_error_schema_in_openapi(app)

    return app


@click.command()
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development",
)
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host to bind to (default: 0.0.0.0)",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port to bind to (default: 8000)",
)
@click.pass_context
def server(ctx: click.Context, reload: bool, host: str, port: int):
    """Start the Leggen API server"""

    # Get config, config_dir, database, and log_level from main CLI context
    config_path = None
    config_dir = None
    database = None
    log_level = "info"
    if ctx.parent:
        config_path = ctx.parent.params.get("config")
        config_dir = ctx.parent.params.get("config_dir")
        database = ctx.parent.params.get("database")
        log_level = ctx.parent.params.get("log_level", "info").lower()

    # Set up path manager and config singleton with user-provided paths
    if config_dir:
        path_manager.set_config_dir(config_dir)
    if database:
        path_manager.set_database_path(database)
    if config_path:
        config.set_config_path(config_path)

    if reload:
        # The reload worker is a fresh process where only the environment
        # survives, so path flags must be exported to reach it.
        if config_path:
            os.environ["LEGGEN_CONFIG_FILE"] = str(config_path)
        if config_dir:
            os.environ["LEGGEN_CONFIG_DIR"] = str(config_dir)
        if database:
            os.environ["LEGGEN_DATABASE_PATH"] = str(database)

        # Use string import for reload to work properly
        uvicorn.run(
            "leggen.commands.server:create_app",
            factory=True,
            host=host,
            port=port,
            log_level=log_level,
            access_log=True,
            reload=True,
            reload_dirs=["leggen"],  # Watch leggen directory
        )
    else:
        app = create_app()
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
            access_log=True,
        )
