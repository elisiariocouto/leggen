"""FastAPI dependency injection setup for repositories and services."""

from typing import Annotated

from fastapi import Depends

from leggen.repositories import (
    AccountRepository,
    BalanceRepository,
    MigrationRepository,
    SessionRepository,
    SyncRepository,
    TransactionRepository,
)
from leggen.services.data_processors import AnalyticsProcessor
from leggen.services.enablebanking_service import EnableBankingService
from leggen.utils.config import config

# Type annotations for dependency injection
# Depends() with no args tells FastAPI to instantiate the class directly
AccountRepo = Annotated[AccountRepository, Depends()]
BalanceRepo = Annotated[BalanceRepository, Depends()]
TransactionRepo = Annotated[TransactionRepository, Depends()]
SyncRepo = Annotated[SyncRepository, Depends()]
MigrationRepo = Annotated[MigrationRepository, Depends()]
SessionRepo = Annotated[SessionRepository, Depends()]
AnalyticsProc = Annotated[AnalyticsProcessor, Depends()]
EnableBanking = Annotated[EnableBankingService, Depends()]


def is_sqlite_enabled() -> bool:
    """Check if SQLite is enabled in configuration."""
    return config.database_config.get("sqlite", True)
