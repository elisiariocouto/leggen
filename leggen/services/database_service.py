from functools import wraps
from typing import Any, Dict, List, Optional

from loguru import logger

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
from leggen.utils.paths import path_manager


def require_sqlite(func):
    """Decorator to check if SQLite is enabled before executing method"""

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.sqlite_enabled:
            logger.warning(f"SQLite database disabled, skipping {func.__name__}")
            return_type = func.__annotations__.get("return")
            if return_type is int:
                return 0
            elif return_type in (list, List[Dict[str, Any]]):
                return []
            return None
        return await func(self, *args, **kwargs)

    return wrapper


class DatabaseService:
    """Simplified database service using repository pattern"""

    def __init__(self):
        self.db_config = config.database_config
        self.sqlite_enabled = self.db_config.get("sqlite", True)

        # Repositories
        self.transactions = TransactionRepository()
        self.accounts = AccountRepository()
        self.balances = BalanceRepository()
        self.migrations = MigrationRepository()
        self.sync = SyncRepository()

        # Data processors
        self.transaction_processor = TransactionProcessor()
        self.balance_transformer = BalanceTransformer()
        self.analytics_processor = AnalyticsProcessor()

    # Migration methods
    async def run_migrations_if_needed(self):
        """Run all necessary database migrations"""
        if not self.sqlite_enabled:
            logger.info("SQLite database disabled, skipping migrations")
            return

        await self.migrations.run_all_migrations()

    # Transaction methods
    def process_transactions(
        self,
        account_id: str,
        account_info: Dict[str, Any],
        transaction_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Process raw transaction data into standardized format"""
        return self.transaction_processor.process_transactions(
            account_id, account_info, transaction_data
        )

    @require_sqlite
    async def persist_transactions(
        self, account_id: str, transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Persist transactions and return new transactions"""
        return self.transactions.persist(account_id, transactions)

    @require_sqlite
    async def get_transactions_from_db(
        self,
        account_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get transactions from database"""
        try:
            transactions = self.transactions.get_transactions(
                account_id=account_id,
                limit=limit,
                offset=offset or 0,
                date_from=date_from,
                date_to=date_to,
                min_amount=min_amount,
                max_amount=max_amount,
                search=search,
            )
            logger.debug(f"Retrieved {len(transactions)} transactions from database")
            return transactions
        except Exception as e:
            logger.error(f"Failed to get transactions from database: {e}")
            return []

    @require_sqlite
    async def get_transaction_count_from_db(
        self,
        account_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        search: Optional[str] = None,
    ) -> int:
        """Get total count of transactions from database"""
        try:
            count = self.transactions.get_count(
                account_id=account_id,
                date_from=date_from,
                date_to=date_to,
                min_amount=min_amount,
                max_amount=max_amount,
                search=search,
            )
            logger.debug(f"Total transaction count: {count}")
            return count
        except Exception as e:
            logger.error(f"Failed to get transaction count from database: {e}")
            return 0

    @require_sqlite
    async def get_account_summary_from_db(
        self, account_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get basic account info from database (avoids GoCardless call)"""
        try:
            summary = self.transactions.get_account_summary(account_id)
            if summary:
                logger.debug(
                    f"Retrieved account summary from database for {account_id}"
                )
            return summary
        except Exception as e:
            logger.error(f"Failed to get account summary from database: {e}")
            return None

    # Account methods
    @require_sqlite
    async def persist_account_details(self, account_data: Dict[str, Any]) -> None:
        """Persist account details to database"""
        try:
            self.accounts.persist(account_data)
            logger.info(f"Persisted account details for account {account_data['id']}")
        except Exception as e:
            logger.error(f"Failed to persist account details: {e}")
            raise

    @require_sqlite
    async def get_accounts_from_db(
        self, account_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get account details from database"""
        try:
            accounts = self.accounts.get_accounts(account_ids=account_ids)
            logger.debug(f"Retrieved {len(accounts)} accounts from database")
            return accounts
        except Exception as e:
            logger.error(f"Failed to get accounts from database: {e}")
            return []

    @require_sqlite
    async def get_account_details_from_db(
        self, account_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get specific account details from database"""
        try:
            account = self.accounts.get_account(account_id)
            if account:
                logger.debug(
                    f"Retrieved account details from database for {account_id}"
                )
            return account
        except Exception as e:
            logger.error(f"Failed to get account details from database: {e}")
            return None

    # Balance methods
    @require_sqlite
    async def persist_balance(
        self, account_id: str, balance_data: Dict[str, Any]
    ) -> None:
        """Persist account balance data"""
        try:
            balance_rows = self.balance_transformer.transform_to_database_format(
                account_id, balance_data
            )
            self.balances.persist(account_id, balance_rows)
            logger.info(f"Persisted balances for account {account_id}")
        except Exception as e:
            logger.error(f"Failed to persist balances: {e}")
            raise

    @require_sqlite
    async def get_balances_from_db(
        self, account_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get balances from database"""
        try:
            balances = self.balances.get_balances(account_id=account_id)
            logger.debug(f"Retrieved {len(balances)} balances from database")
            return balances
        except Exception as e:
            logger.error(f"Failed to get balances from database: {e}")
            return []

    # Analytics methods
    @require_sqlite
    async def get_historical_balances_from_db(
        self, account_id: Optional[str] = None, days: int = 365
    ) -> List[Dict[str, Any]]:
        """Get historical balance progression from database"""
        try:
            db_path = path_manager.get_database_path()
            balances = self.analytics_processor.calculate_historical_balances(
                db_path, account_id=account_id, days=days
            )
            logger.debug(
                f"Retrieved {len(balances)} historical balance points from database"
            )
            return balances
        except Exception as e:
            logger.error(f"Failed to get historical balances from database: {e}")
            return []

    @require_sqlite
    async def get_monthly_transaction_stats_from_db(
        self,
        account_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get monthly transaction statistics aggregated by the database"""
        try:
            db_path = path_manager.get_database_path()
            monthly_stats = self.analytics_processor.calculate_monthly_stats(
                db_path, account_id=account_id, date_from=date_from, date_to=date_to
            )
            logger.debug(
                f"Retrieved {len(monthly_stats)} monthly stat points from database"
            )
            return monthly_stats
        except Exception as e:
            logger.error(f"Failed to get monthly transaction stats from database: {e}")
            return []

    # Sync operation methods
    async def persist_sync_operation(self, sync_operation: Dict[str, Any]) -> int:
        """Persist sync operation to database and return the ID"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, cannot persist sync operation")
            return 0

        return self.sync.persist(sync_operation)

    async def get_sync_operations(
        self, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get sync operations from database"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, cannot get sync operations")
            return []

        return self.sync.get_operations(limit, offset)
