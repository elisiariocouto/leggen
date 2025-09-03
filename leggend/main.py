from contextlib import asynccontextmanager
from importlib import metadata

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from leggend.api.routes import banks, accounts, sync, notifications, transactions
from leggend.background.scheduler import scheduler
from leggend.config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting leggend service...")

    # Load configuration
    try:
        config.load_config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise

    # Start background scheduler
    scheduler.start()
    logger.info("Background scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down leggend service...")
    scheduler.shutdown()


def create_app() -> FastAPI:
    # Get version dynamically from package metadata
    try:
        version = metadata.version("leggen")
    except metadata.PackageNotFoundError:
        version = "unknown"

    app = FastAPI(
        title="Leggend API",
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
        ],  # SvelteKit dev servers
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

    @app.get("/")
    async def root():
        # Get version dynamically
        try:
            version = metadata.version("leggen")
        except metadata.PackageNotFoundError:
            version = "unknown"
        return {"message": "Leggend API is running", "version": version}

    @app.get("/health")
    async def health():
        return {"status": "healthy", "config_loaded": config._config is not None}

    return app


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Start the Leggend API service")
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    args = parser.parse_args()

    if args.reload:
        # Use string import for reload to work properly
        uvicorn.run(
            "leggend.main:create_app",
            factory=True,
            host=args.host,
            port=args.port,
            log_level="info",
            access_log=True,
            reload=True,
            reload_dirs=["leggend", "leggen"],  # Watch both directories
        )
    else:
        app = create_app()
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info",
            access_log=True,
        )


if __name__ == "__main__":
    main()
