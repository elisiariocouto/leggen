import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import and_, desc, func
from sqlmodel import col, select

from leggen.models.database import Account, Balance, SyncOperation, Transaction
from leggen.services.database import get_session, init_database
from leggen.services.transaction_processor import TransactionProcessor
from leggen.utils.config import config
from leggen.utils.paths import path_manager


class DatabaseService:
    def __init__(self):
        self.db_config = config.database_config
        self.sqlite_enabled = self.db_config.get("sqlite", True)
        self.transaction_processor = TransactionProcessor()

    async def persist_balance(
        self, account_id: str, balance_data: Dict[str, Any]
    ) -> None:
        """Persist account balance data"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, skipping balance persistence")
            return

        await self._persist_balance_sqlite(account_id, balance_data)

    async def persist_transactions(
        self, account_id: str, transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Persist transactions and return new transactions"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, skipping transaction persistence")
            return transactions

        return await self._persist_transactions_sqlite(account_id, transactions)

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

    async def get_transactions_from_db(
        self,
        account_id: Optional[str] = None,
        limit: Optional[int] = None,  # None means no limit, used for stats
        offset: Optional[int] = 0,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get transactions from SQLite database"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, cannot read transactions")
            return []

        try:
            transactions = self._get_transactions(
                account_id=account_id,
                limit=limit,  # Pass limit as-is, None means no limit
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

    async def get_transaction_count_from_db(
        self,
        account_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        search: Optional[str] = None,
    ) -> int:
        """Get total count of transactions from SQLite database"""
        if not self.sqlite_enabled:
            return 0

        try:
            filters = {
                "date_from": date_from,
                "date_to": date_to,
                "min_amount": min_amount,
                "max_amount": max_amount,
                "search": search,
            }
            # Remove None values
            filters = {k: v for k, v in filters.items() if v is not None}

            count = self._get_transaction_count(account_id=account_id, **filters)
            logger.debug(f"Total transaction count: {count}")
            return count
        except Exception as e:
            logger.error(f"Failed to get transaction count from database: {e}")
            return 0

    async def get_balances_from_db(
        self, account_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get balances from SQLite database"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, cannot read balances")
            return []

        try:
            balances = self._get_balances(account_id=account_id)
            logger.debug(f"Retrieved {len(balances)} balances from database")
            return balances
        except Exception as e:
            logger.error(f"Failed to get balances from database: {e}")
            return []

    async def get_historical_balances_from_db(
        self, account_id: Optional[str] = None, days: int = 365
    ) -> List[Dict[str, Any]]:
        """Get historical balance progression from SQLite database"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, cannot read historical balances")
            return []

        try:
            balances = self._get_historical_balances(account_id=account_id, days=days)
            logger.debug(
                f"Retrieved {len(balances)} historical balance points from database"
            )
            return balances
        except Exception as e:
            logger.error(f"Failed to get historical balances from database: {e}")
            return []

    async def get_account_summary_from_db(
        self, account_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get basic account info from SQLite database (avoids GoCardless call)"""
        if not self.sqlite_enabled:
            return None

        try:
            summary = self._get_account_summary(account_id)
            if summary:
                logger.debug(
                    f"Retrieved account summary from database for {account_id}"
                )
            return summary
        except Exception as e:
            logger.error(f"Failed to get account summary from database: {e}")
            return None

    async def persist_account_details(self, account_data: Dict[str, Any]) -> None:
        """Persist account details to database"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, skipping account persistence")
            return

        await self._persist_account_details_sqlite(account_data)

    async def get_accounts_from_db(
        self, account_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get account details from database"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, cannot read accounts")
            return []

        try:
            accounts = self._get_accounts(account_ids=account_ids)
            logger.debug(f"Retrieved {len(accounts)} accounts from database")
            return accounts
        except Exception as e:
            logger.error(f"Failed to get accounts from database: {e}")
            return []

    async def get_account_details_from_db(
        self, account_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get specific account details from database"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, cannot read account")
            return None

        try:
            account = self._get_account(account_id)
            if account:
                logger.debug(
                    f"Retrieved account details from database for {account_id}"
                )
            return account
        except Exception as e:
            logger.error(f"Failed to get account details from database: {e}")
            return None

    async def run_migrations_if_needed(self):
        """Run all necessary database migrations using Alembic"""
        if not self.sqlite_enabled:
            logger.info("SQLite database disabled, skipping migrations")
            return

        db_path = path_manager.get_database_path()

        # Initialize SQLModel tables (creates if not exists)
        init_database()

        # Run Alembic migrations
        import os

        from alembic.config import Config

        from alembic import command

        # Get the alembic.ini path (project root)
        alembic_ini_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "alembic.ini"
        )

        if not os.path.exists(alembic_ini_path):
            logger.warning(f"Alembic config not found at {alembic_ini_path}")
            return

        alembic_cfg = Config(alembic_ini_path)

        try:
            # Check if database already has all tables (existing database)
            # If so, stamp it with the latest revision without running migrations
            import sqlite3

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check if alembic_version table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='alembic_version'
            """)
            has_alembic = cursor.fetchone() is not None

            # Check if all main tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('accounts', 'transactions', 'balances', 'sync_operations')
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]
            conn.close()

            if not has_alembic and len(existing_tables) >= 4:
                # This is an existing database without Alembic tracking
                # Stamp it with the latest revision
                logger.info("Marking existing database with current Alembic revision")
                command.stamp(alembic_cfg, "head")
            else:
                # Run migrations normally
                logger.info("Running Alembic migrations")
                command.upgrade(alembic_cfg, "head")

            logger.info("Database migrations completed successfully")
        except Exception as e:
            logger.error(f"Failed to run Alembic migrations: {e}")
            raise

        logger.info("Database migrations completed")

    async def _persist_balance_sqlite(
        self, account_id: str, balance_data: Dict[str, Any]
    ) -> None:
        """Persist balance to database using SQLModel"""
        try:
            with get_session() as session:
                # Convert GoCardless balance format to our format and persist
                for balance in balance_data.get("balances", []):
                    balance_amount = balance["balanceAmount"]

                    db_balance = Balance(
                        account_id=account_id,
                        bank=balance_data.get("institution_id", "unknown"),
                        status=balance_data.get("account_status", ""),
                        iban=balance_data.get("iban", "N/A"),
                        amount=float(balance_amount["amount"]),
                        currency=balance_amount["currency"],
                        type=balance["balanceType"],
                        timestamp=datetime.now(),
                    )
                    session.add(db_balance)

                session.commit()

            logger.info(f"Persisted balances for account {account_id}")
        except Exception as e:
            logger.error(f"Failed to persist balances: {e}")
            raise

    async def _persist_transactions_sqlite(
        self, account_id: str, transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Persist transactions to database using SQLModel"""
        try:
            new_transactions = []

            with get_session() as session:
                for transaction in transactions:
                    # Check if transaction already exists
                    statement = select(Transaction).where(
                        Transaction.accountId == transaction["accountId"],
                        Transaction.transactionId == transaction["transactionId"],
                    )
                    existing = session.exec(statement).first()

                    if existing:
                        # Update existing transaction
                        existing.internalTransactionId = transaction.get(
                            "internalTransactionId"
                        )
                        existing.institutionId = transaction["institutionId"]
                        existing.iban = transaction["iban"]
                        existing.transactionDate = transaction["transactionDate"]
                        existing.description = transaction["description"]
                        existing.transactionValue = transaction["transactionValue"]
                        existing.transactionCurrency = transaction[
                            "transactionCurrency"
                        ]
                        existing.transactionStatus = transaction["transactionStatus"]
                        existing.rawTransaction = transaction["rawTransaction"]
                    else:
                        # Add new transaction
                        db_transaction = Transaction(
                            accountId=transaction["accountId"],
                            transactionId=transaction["transactionId"],
                            internalTransactionId=transaction.get(
                                "internalTransactionId"
                            ),
                            institutionId=transaction["institutionId"],
                            iban=transaction["iban"],
                            transactionDate=transaction["transactionDate"],
                            description=transaction["description"],
                            transactionValue=transaction["transactionValue"],
                            transactionCurrency=transaction["transactionCurrency"],
                            transactionStatus=transaction["transactionStatus"],
                            rawTransaction=transaction["rawTransaction"],
                        )
                        session.add(db_transaction)
                        new_transactions.append(transaction)

                session.commit()

            logger.info(
                f"Persisted {len(new_transactions)} new transactions for account {account_id}"
            )
            return new_transactions
        except Exception as e:
            logger.error(f"Failed to persist transactions: {e}")
            raise

    async def _persist_account_details_sqlite(
        self, account_data: Dict[str, Any]
    ) -> None:
        """Persist account details using SQLModel"""
        try:
            self._persist_account(account_data)
            logger.info(f"Persisted account details for account {account_data['id']}")
        except Exception as e:
            logger.error(f"Failed to persist account details: {e}")
            raise

    def _get_transactions(
        self,
        account_id=None,
        limit=100,
        offset=0,
        date_from=None,
        date_to=None,
        min_amount=None,
        max_amount=None,
        search=None,
    ):
        """Get transactions from database with optional filtering using SQLModel"""
        try:
            with get_session() as session:
                statement = select(Transaction)

                # Apply filters
                if account_id:
                    statement = statement.where(Transaction.accountId == account_id)

                if date_from:
                    statement = statement.where(
                        Transaction.transactionDate >= date_from
                    )

                if date_to:
                    statement = statement.where(Transaction.transactionDate <= date_to)

                if min_amount is not None:
                    statement = statement.where(
                        Transaction.transactionValue >= min_amount
                    )

                if max_amount is not None:
                    statement = statement.where(
                        Transaction.transactionValue <= max_amount
                    )

                if search:
                    statement = statement.where(
                        col(Transaction.description).contains(search)
                    )

                # Add ordering
                statement = statement.order_by(desc(col(Transaction.transactionDate)))

                # Add pagination
                if limit:
                    statement = statement.limit(limit)

                if offset:
                    statement = statement.offset(offset)

                results = session.exec(statement).all()

                # Convert to list of dicts
                transactions = []
                for row in results:
                    transaction = row.model_dump()
                    transactions.append(transaction)

                return transactions
        except Exception as e:
            logger.error(f"Failed to get transactions: {e}")
            return []

    def _get_balances(self, account_id=None):
        """Get latest balances from database using SQLModel"""
        try:
            with get_session() as session:
                # Subquery to get max timestamp for each account_id and type
                subquery = (
                    select(
                        Balance.account_id,
                        Balance.type,
                        func.max(Balance.timestamp).label("max_timestamp"),
                    )
                    .group_by(Balance.account_id, Balance.type)
                    .subquery()
                )

                # Main query to get latest balances
                statement = select(Balance).join(
                    subquery,
                    and_(
                        col(Balance.account_id) == subquery.c.account_id,
                        col(Balance.type) == subquery.c.type,
                        col(Balance.timestamp) == subquery.c.max_timestamp,
                    ),
                )

                if account_id:
                    statement = statement.where(Balance.account_id == account_id)

                statement = statement.order_by(Balance.account_id, Balance.type)

                results = session.exec(statement).all()
                return [balance.model_dump() for balance in results]
        except Exception as e:
            logger.error(f"Failed to get balances: {e}")
            return []

    def _get_account_summary(self, account_id):
        """Get basic account info from transactions table"""
        try:
            with get_session() as session:
                statement = (
                    select(
                        Transaction.accountId,
                        Transaction.institutionId,
                        Transaction.iban,
                    )
                    .where(Transaction.accountId == account_id)
                    .order_by(desc(col(Transaction.transactionDate)))
                    .limit(1)
                )

                result = session.exec(statement).first()
                if result:
                    return {
                        "accountId": result[0],
                        "institutionId": result[1],
                        "iban": result[2],
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get account summary: {e}")
            return None

    def _get_transaction_count(self, account_id=None, **filters):
        """Get total count of transactions matching filters using SQLModel"""
        try:
            with get_session() as session:
                statement = select(func.count()).select_from(Transaction)

                # Apply filters
                if account_id:
                    statement = statement.where(Transaction.accountId == account_id)

                if filters.get("date_from"):
                    statement = statement.where(
                        Transaction.transactionDate >= filters["date_from"]
                    )

                if filters.get("date_to"):
                    statement = statement.where(
                        Transaction.transactionDate <= filters["date_to"]
                    )

                if filters.get("min_amount") is not None:
                    statement = statement.where(
                        Transaction.transactionValue >= filters["min_amount"]
                    )

                if filters.get("max_amount") is not None:
                    statement = statement.where(
                        Transaction.transactionValue <= filters["max_amount"]
                    )

                if filters.get("search"):
                    statement = statement.where(
                        col(Transaction.description).contains(filters["search"])
                    )

                count = session.exec(statement).one()
                return count
        except Exception as e:
            logger.error(f"Failed to get transaction count: {e}")
            return 0

    def _persist_account(self, account_data: dict):
        """Persist account details using SQLModel"""
        try:
            with get_session() as session:
                # Check if account exists
                statement = select(Account).where(Account.id == account_data["id"])
                existing = session.exec(statement).first()

                if existing:
                    # Preserve display_name if not provided in new data
                    display_name = account_data.get(
                        "display_name", existing.display_name
                    )

                    # Update existing account
                    existing.institution_id = account_data["institution_id"]
                    existing.status = account_data["status"]
                    existing.iban = account_data.get("iban")
                    existing.name = account_data.get("name")
                    existing.currency = account_data.get("currency")
                    existing.created = account_data["created"]
                    existing.last_accessed = account_data.get("last_accessed")
                    existing.last_updated = account_data.get(
                        "last_updated", account_data["created"]
                    )
                    existing.display_name = display_name
                    existing.logo = account_data.get("logo")
                else:
                    # Create new account
                    db_account = Account(
                        id=account_data["id"],
                        institution_id=account_data["institution_id"],
                        status=account_data["status"],
                        iban=account_data.get("iban"),
                        name=account_data.get("name"),
                        currency=account_data.get("currency"),
                        created=account_data["created"],
                        last_accessed=account_data.get("last_accessed"),
                        last_updated=account_data.get(
                            "last_updated", account_data["created"]
                        ),
                        display_name=account_data.get("display_name"),
                        logo=account_data.get("logo"),
                    )
                    session.add(db_account)

                session.commit()
                return account_data
        except Exception as e:
            logger.error(f"Failed to persist account: {e}")
            raise

    def _get_accounts(self, account_ids=None):
        """Get account details using SQLModel"""
        try:
            with get_session() as session:
                statement = select(Account)

                if account_ids:
                    statement = statement.where(col(Account.id).in_(account_ids))

                statement = statement.order_by(desc(col(Account.created)))

                results = session.exec(statement).all()
                return [account.model_dump() for account in results]
        except Exception as e:
            logger.error(f"Failed to get accounts: {e}")
            return []

    def _get_account(self, account_id: str):
        """Get specific account details using SQLModel"""
        try:
            with get_session() as session:
                statement = select(Account).where(Account.id == account_id)
                result = session.exec(statement).first()
                return result.model_dump() if result else None
        except Exception as e:
            logger.error(f"Failed to get account: {e}")
            return None

    def _get_historical_balances(self, account_id=None, days=365):
        """Get historical balance progression based on transaction history"""
        # This method uses complex CTEs and window functions that are better kept as raw SQL
        # for performance and readability
        from leggen.services.database_helpers import get_db_connection

        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return []

        cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        today_date = datetime.now().date().isoformat()

        # Single SQL query to generate historical balances using window functions
        query = """
        WITH RECURSIVE date_series AS (
            -- Generate weekly dates from cutoff_date to today
            SELECT date(?) as ref_date
            UNION ALL
            SELECT date(ref_date, '+7 days')
            FROM date_series
            WHERE ref_date < date(?)
        ),
        current_balances AS (
            -- Get current balance for each account/type
            SELECT account_id, type, amount, currency
            FROM balances b1
            WHERE b1.timestamp = (
                SELECT MAX(b2.timestamp)
                FROM balances b2
                WHERE b2.account_id = b1.account_id AND b1.type = b2.type
            )
            {account_filter}
            AND b1.type = 'closingBooked'  -- Focus on closingBooked for charts
        ),
        historical_points AS (
            -- Calculate balance at each weekly point by subtracting future transactions
            SELECT
                cb.account_id,
                cb.type as balance_type,
                cb.currency,
                ds.ref_date,
                cb.amount - COALESCE(
                    (SELECT SUM(t.transactionValue)
                     FROM transactions t
                     WHERE t.accountId = cb.account_id
                     AND date(t.transactionDate) > ds.ref_date), 0
                ) as balance_amount
            FROM current_balances cb
            CROSS JOIN date_series ds
        )
        SELECT
            account_id || '_' || balance_type || '_' || ref_date as id,
            account_id,
            balance_amount,
            balance_type,
            currency,
            ref_date as reference_date
        FROM historical_points
        ORDER BY account_id, ref_date
        """

        # Build parameters and account filter
        params = [cutoff_date, today_date]
        if account_id:
            account_filter = "AND b1.account_id = ?"
            params.append(account_id)
        else:
            account_filter = ""

        # Format the query with conditional filter
        formatted_query = query.format(account_filter=account_filter)

        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(formatted_query, tuple(params))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get historical balances: {e}")
            return []

    async def get_monthly_transaction_stats_from_db(
        self,
        account_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get monthly transaction statistics aggregated by the database"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, cannot read monthly stats")
            return []

        try:
            monthly_stats = self._get_monthly_transaction_stats(
                account_id=account_id,
                date_from=date_from,
                date_to=date_to,
            )
            logger.debug(
                f"Retrieved {len(monthly_stats)} monthly stat points from database"
            )
            return monthly_stats
        except Exception as e:
            logger.error(f"Failed to get monthly transaction stats from database: {e}")
            return []

    def _get_monthly_transaction_stats(
        self,
        account_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get monthly transaction statistics - using raw SQL for date aggregation"""
        from leggen.services.database_helpers import get_db_connection

        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return []

        # SQL query to aggregate transactions by month
        query = """
        SELECT
            strftime('%Y-%m', transactionDate) as month,
            COALESCE(SUM(CASE WHEN transactionValue > 0 THEN transactionValue ELSE 0 END), 0) as income,
            COALESCE(SUM(CASE WHEN transactionValue < 0 THEN ABS(transactionValue) ELSE 0 END), 0) as expenses,
            COALESCE(SUM(transactionValue), 0) as net
        FROM transactions
        WHERE 1=1
        """

        params = []

        if account_id:
            query += " AND accountId = ?"
            params.append(account_id)

        if date_from:
            query += " AND transactionDate >= ?"
            params.append(date_from)

        if date_to:
            query += " AND transactionDate <= ?"
            params.append(date_to)

        query += """
        GROUP BY strftime('%Y-%m', transactionDate)
        ORDER BY month ASC
        """

        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()

                # Convert to desired format with proper month display
                monthly_stats = []
                for row in rows:
                    # Convert YYYY-MM to display format like "Mar 2024"
                    year, month_num = row["month"].split("-")
                    month_date = datetime.strptime(f"{year}-{month_num}-01", "%Y-%m-%d")
                    display_month = month_date.strftime("%b %Y")

                    monthly_stats.append(
                        {
                            "month": display_month,
                            "income": round(row["income"], 2),
                            "expenses": round(row["expenses"], 2),
                            "net": round(row["net"], 2),
                        }
                    )

                return monthly_stats
        except Exception as e:
            logger.error(f"Failed to get monthly transaction stats: {e}")
            return []

    async def persist_sync_operation(self, sync_operation: Dict[str, Any]) -> int:
        """Persist sync operation to database using SQLModel"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, cannot persist sync operation")
            return 0

        try:
            with get_session() as session:
                db_sync = SyncOperation(
                    started_at=sync_operation.get("started_at"),
                    completed_at=sync_operation.get("completed_at"),
                    success=sync_operation.get("success"),
                    accounts_processed=sync_operation.get("accounts_processed", 0),
                    transactions_added=sync_operation.get("transactions_added", 0),
                    transactions_updated=sync_operation.get("transactions_updated", 0),
                    balances_updated=sync_operation.get("balances_updated", 0),
                    duration_seconds=sync_operation.get("duration_seconds"),
                    errors=json.dumps(sync_operation.get("errors", [])),
                    logs=json.dumps(sync_operation.get("logs", [])),
                    trigger_type=sync_operation.get("trigger_type", "manual"),
                )
                session.add(db_sync)
                session.commit()
                session.refresh(db_sync)

                operation_id = db_sync.id
                if operation_id is None:
                    raise ValueError("Failed to get operation ID after insert")

                logger.debug(f"Persisted sync operation with ID: {operation_id}")
                return operation_id

        except Exception as e:
            logger.error(f"Failed to persist sync operation: {e}")
            raise

    async def get_sync_operations(
        self, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get sync operations from database using SQLModel"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, cannot get sync operations")
            return []

        try:
            with get_session() as session:
                statement = (
                    select(SyncOperation)
                    .order_by(desc(col(SyncOperation.started_at)))
                    .limit(limit)
                    .offset(offset)
                )

                results = session.exec(statement).all()

                operations = []
                for sync_op in results:
                    operation = sync_op.model_dump()
                    # Parse JSON fields
                    if operation["errors"]:
                        operation["errors"] = json.loads(operation["errors"])
                    else:
                        operation["errors"] = []

                    if operation["logs"]:
                        operation["logs"] = json.loads(operation["logs"])
                    else:
                        operation["logs"] = []

                    operations.append(operation)

                return operations

        except Exception as e:
            logger.error(f"Failed to get sync operations: {e}")
            return []
