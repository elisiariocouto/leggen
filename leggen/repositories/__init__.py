from leggen.repositories.account_repository import AccountRepository
from leggen.repositories.balance_repository import BalanceRepository
from leggen.repositories.category_repository import CategoryRepository
from leggen.repositories.migration_repository import MigrationRepository
from leggen.repositories.session_repository import SessionRepository
from leggen.repositories.sync_repository import SyncRepository
from leggen.repositories.transaction_repository import TransactionRepository

__all__ = [
    "AccountRepository",
    "BalanceRepository",
    "CategoryRepository",
    "MigrationRepository",
    "SessionRepository",
    "SyncRepository",
    "TransactionRepository",
    "ensure_tables",
]


def ensure_tables() -> None:
    """Create all database tables. Call once at startup."""
    AccountRepository().create_table()
    BalanceRepository().create_table()
    TransactionRepository().create_table()
    SyncRepository().create_table()
    SessionRepository().create_table()
    CategoryRepository().create_table()
