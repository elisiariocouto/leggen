import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from leggend.api.routes import banks, accounts, sync, notifications
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
    app = FastAPI(
        title="Leggend API",
        description="Open Banking API for Leggen",
        version="0.6.11",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],  # SvelteKit dev servers
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(banks.router, prefix="/api/v1", tags=["banks"])
    app.include_router(accounts.router, prefix="/api/v1", tags=["accounts"])
    app.include_router(sync.router, prefix="/api/v1", tags=["sync"])
    app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])

    @app.get("/")
    async def root():
        return {"message": "Leggend API is running", "version": "0.6.11"}

    @app.get("/health")
    async def health():
        return {"status": "healthy", "config_loaded": config._config is not None}

    return app


def main():
    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()