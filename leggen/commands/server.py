from contextlib import asynccontextmanager
from importlib import metadata

import click
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from leggen.api.routes import accounts, backup, banks, notifications, sync, transactions
from leggen.background.scheduler import scheduler
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

    # Run database migrations
    try:
        from leggen.services.database_service import DatabaseService

        db_service = DatabaseService()
        await db_service.run_migrations_if_needed()
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

    # Include API routes
    app.include_router(banks.router, prefix="/api/v1", tags=["banks"])
    app.include_router(accounts.router, prefix="/api/v1", tags=["accounts"])
    app.include_router(transactions.router, prefix="/api/v1", tags=["transactions"])
    app.include_router(sync.router, prefix="/api/v1", tags=["sync"])
    app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
    app.include_router(backup.router, prefix="/api/v1", tags=["backup"])

    @app.get("/api/v1/health")
    async def health():
        """Health check endpoint for API connectivity"""
        try:
            from leggen.api.models.common import APIResponse

            config_loaded = config._config is not None

            # Get version dynamically
            try:
                version = metadata.version("leggen")
            except metadata.PackageNotFoundError:
                version = "dev"

            return APIResponse(
                success=True,
                data={
                    "status": "healthy",
                    "config_loaded": config_loaded,
                    "version": version,
                    "message": "API is running and responsive",
                },
                message="Health check successful",
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            from leggen.api.models.common import APIResponse

            return APIResponse(
                success=False,
                data={"status": "unhealthy", "error": str(e)},
                message="Health check failed",
            )

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

    # Get config_dir and database from main CLI context
    config_dir = None
    database = None
    if ctx.parent:
        config_dir = ctx.parent.params.get("config_dir")
        database = ctx.parent.params.get("database")

    # Set up path manager with user-provided paths
    if config_dir:
        path_manager.set_config_dir(config_dir)
    if database:
        path_manager.set_database_path(database)

    if reload:
        # Use string import for reload to work properly
        uvicorn.run(
            "leggen.commands.server:create_app",
            factory=True,
            host=host,
            port=port,
            log_level="info",
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
            log_level="info",
            access_log=True,
        )
