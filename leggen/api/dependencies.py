"""FastAPI dependency injection setup for repositories and services."""

from typing import Annotated

from fastapi import Depends

from leggen.repositories import (
    AccountRepository,
    BalanceRepository,
    MigrationRepository,
    SyncRepository,
    TransactionRepository,
)
from leggen.services.data_processors import (
    AnalyticsProcessor,
    BalanceTransformer,
    TransactionProcessor,
)
from leggen.utils.config import config


def get_account_repository() -> AccountRepository:
    """Get account repository instance."""
    return AccountRepository()


def get_balance_repository() -> BalanceRepository:
    """Get balance repository instance."""
    return BalanceRepository()


def get_transaction_repository() -> TransactionRepository:
    """Get transaction repository instance."""
    return TransactionRepository()


def get_sync_repository() -> SyncRepository:
    """Get sync repository instance."""
    return SyncRepository()


def get_migration_repository() -> MigrationRepository:
    """Get migration repository instance."""
    return MigrationRepository()


def get_transaction_processor() -> TransactionProcessor:
    """Get transaction processor instance."""
    return TransactionProcessor()


def get_balance_transformer() -> BalanceTransformer:
    """Get balance transformer instance."""
    return BalanceTransformer()


def get_analytics_processor() -> AnalyticsProcessor:
    """Get analytics processor instance."""
    return AnalyticsProcessor()


def is_sqlite_enabled() -> bool:
    """Check if SQLite is enabled in configuration."""
    return config.database_config.get("sqlite", True)


# Type annotations for dependency injection
AccountRepo = Annotated[AccountRepository, Depends(get_account_repository)]
BalanceRepo = Annotated[BalanceRepository, Depends(get_balance_repository)]
TransactionRepo = Annotated[TransactionRepository, Depends(get_transaction_repository)]
SyncRepo = Annotated[SyncRepository, Depends(get_sync_repository)]
MigrationRepo = Annotated[MigrationRepository, Depends(get_migration_repository)]
TransactionProc = Annotated[TransactionProcessor, Depends(get_transaction_processor)]
BalanceTransform = Annotated[BalanceTransformer, Depends(get_balance_transformer)]
AnalyticsProc = Annotated[AnalyticsProcessor, Depends(get_analytics_processor)]
