import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger

from leggen.services.database_helpers import get_db_connection
from leggen.services.database_migrations import run_all_migrations
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
        """Run all necessary database migrations"""
        if not self.sqlite_enabled:
            logger.info("SQLite database disabled, skipping migrations")
            return

        db_path = path_manager.get_database_path()
        run_all_migrations(db_path)

    async def _persist_balance_sqlite(
        self, account_id: str, balance_data: Dict[str, Any]
    ) -> None:
        """Persist balance to SQLite"""
        try:
            import sqlite3

            db_path = path_manager.get_database_path()
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Create the balances table if it doesn't exist
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT,
                bank TEXT,
                status TEXT,
                iban TEXT,
                amount REAL,
                currency TEXT,
                type TEXT,
                timestamp DATETIME
            )"""
            )

            # Create indexes for better performance
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_balances_account_id
                   ON balances(account_id)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_balances_timestamp
                   ON balances(timestamp)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_balances_account_type_timestamp
                   ON balances(account_id, type, timestamp)"""
            )

            # Convert GoCardless balance format to our format and persist
            for balance in balance_data.get("balances", []):
                balance_amount = balance["balanceAmount"]

                try:
                    cursor.execute(
                        """INSERT INTO balances (
                        account_id,
                        bank,
                        status,
                        iban,
                        amount,
                        currency,
                        type,
                        timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            account_id,
                            balance_data.get("institution_id", "unknown"),
                            balance_data.get("account_status"),
                            balance_data.get("iban", "N/A"),
                            float(balance_amount["amount"]),
                            balance_amount["currency"],
                            balance["balanceType"],
                            datetime.now().isoformat(),
                        ),
                    )
                except sqlite3.IntegrityError:
                    logger.warning(f"Skipped duplicate balance for {account_id}")

            conn.commit()
            conn.close()

            logger.info(f"Persisted balances to SQLite for account {account_id}")
        except Exception as e:
            logger.error(f"Failed to persist balances to SQLite: {e}")
            raise

    async def _persist_transactions_sqlite(
        self, account_id: str, transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Persist transactions to SQLite"""
        try:
            import json
            import sqlite3

            db_path = path_manager.get_database_path()
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # The table should already exist with the new schema from migration
            # If it doesn't exist, create it (for new installations)
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS transactions (
                accountId TEXT NOT NULL,
                transactionId TEXT NOT NULL,
                internalTransactionId TEXT,
                institutionId TEXT,
                iban TEXT,
                transactionDate DATETIME,
                description TEXT,
                transactionValue REAL,
                transactionCurrency TEXT,
                transactionStatus TEXT,
                rawTransaction JSON,
                PRIMARY KEY (accountId, transactionId)
            )"""
            )

            # Create indexes for better performance (if they don't exist)
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_transactions_internal_id
                   ON transactions(internalTransactionId)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_transactions_date
                   ON transactions(transactionDate)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_transactions_account_date
                   ON transactions(accountId, transactionDate)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_transactions_amount
                   ON transactions(transactionValue)"""
            )

            # Prepare an SQL statement for inserting/replacing data
            insert_sql = """INSERT OR REPLACE INTO transactions (
                accountId,
                transactionId,
                internalTransactionId,
                institutionId,
                iban,
                transactionDate,
                description,
                transactionValue,
                transactionCurrency,
                transactionStatus,
                rawTransaction
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

            new_transactions = []

            for transaction in transactions:
                try:
                    # Check if transaction already exists before insertion
                    cursor.execute(
                        """SELECT COUNT(*) FROM transactions
                           WHERE accountId = ? AND transactionId = ?""",
                        (transaction["accountId"], transaction["transactionId"]),
                    )
                    exists = cursor.fetchone()[0] > 0

                    cursor.execute(
                        insert_sql,
                        (
                            transaction["accountId"],
                            transaction["transactionId"],
                            transaction.get("internalTransactionId"),
                            transaction["institutionId"],
                            transaction["iban"],
                            transaction["transactionDate"],
                            transaction["description"],
                            transaction["transactionValue"],
                            transaction["transactionCurrency"],
                            transaction["transactionStatus"],
                            json.dumps(transaction["rawTransaction"]),
                        ),
                    )

                    # Only add to new_transactions if it didn't exist before
                    if not exists:
                        new_transactions.append(transaction)

                except sqlite3.IntegrityError as e:
                    logger.warning(
                        f"Failed to insert transaction {transaction.get('transactionId')}: {e}"
                    )
                    continue

            conn.commit()
            conn.close()

            logger.info(
                f"Persisted {len(new_transactions)} new transactions to SQLite for account {account_id}"
            )
            return new_transactions
        except Exception as e:
            logger.error(f"Failed to persist transactions to SQLite: {e}")
            raise

    async def _persist_account_details_sqlite(
        self, account_data: Dict[str, Any]
    ) -> None:
        """Persist account details to SQLite"""
        try:
            # Use the sqlite_db module function
            self._persist_account(account_data)

            logger.info(
                f"Persisted account details to SQLite for account {account_data['id']}"
            )
        except Exception as e:
            logger.error(f"Failed to persist account details to SQLite: {e}")
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
        """Get transactions from SQLite database with optional filtering"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return []

        # Build query with filters
        query = "SELECT * FROM transactions WHERE 1=1"
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

        if min_amount is not None:
            query += " AND transactionValue >= ?"
            params.append(min_amount)

        if max_amount is not None:
            query += " AND transactionValue <= ?"
            params.append(max_amount)

        if search:
            query += " AND description LIKE ?"
            params.append(f"%{search}%")

        # Add ordering and pagination
        query += " ORDER BY transactionDate DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        if offset:
            query += " OFFSET ?"
            params.append(offset)

        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            # Convert to list of dicts and parse JSON fields
            transactions = []
            for row in rows:
                transaction = dict(row)
                if transaction["rawTransaction"]:
                    transaction["rawTransaction"] = json.loads(
                        transaction["rawTransaction"]
                    )
                transactions.append(transaction)

            return transactions

    def _get_balances(self, account_id=None):
        """Get latest balances from SQLite database"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return []

        # Get latest balance for each account_id and type combination
        query = """
            SELECT * FROM balances b1
            WHERE b1.timestamp = (
                SELECT MAX(b2.timestamp)
                FROM balances b2
                WHERE b2.account_id = b1.account_id AND b2.type = b1.type
            )
        """
        params = []

        if account_id:
            query += " AND b1.account_id = ?"
            params.append(account_id)

        query += " ORDER BY b1.account_id, b1.type"

        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def _get_account_summary(self, account_id):
        """Get basic account info from transactions table (avoids GoCardless API call)"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return None

        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT accountId, institutionId, iban
                FROM transactions
                WHERE accountId = ?
                ORDER BY transactionDate DESC
                LIMIT 1
            """,
                (account_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def _get_transaction_count(self, account_id=None, **filters):
        """Get total count of transactions matching filters"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return 0

        query = "SELECT COUNT(*) FROM transactions WHERE 1=1"
        params = []

        if account_id:
            query += " AND accountId = ?"
            params.append(account_id)

        # Add same filters as get_transactions
        if filters.get("date_from"):
            query += " AND transactionDate >= ?"
            params.append(filters["date_from"])

        if filters.get("date_to"):
            query += " AND transactionDate <= ?"
            params.append(filters["date_to"])

        if filters.get("min_amount") is not None:
            query += " AND transactionValue >= ?"
            params.append(filters["min_amount"])

        if filters.get("max_amount") is not None:
            query += " AND transactionValue <= ?"
            params.append(filters["max_amount"])

        if filters.get("search"):
            query += " AND description LIKE ?"
            params.append(f"%{filters['search']}%")

        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            count = cursor.fetchone()[0]
            return count

    def _persist_account(self, account_data: dict):
        """Persist account details to SQLite database"""
        db_path = path_manager.get_database_path()

        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            # Create the accounts table if it doesn't exist
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                institution_id TEXT,
                status TEXT,
                iban TEXT,
                name TEXT,
                currency TEXT,
                created DATETIME,
                last_accessed DATETIME,
                last_updated DATETIME,
                display_name TEXT,
                logo TEXT
            )"""
            )

            # Create indexes for accounts table
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_accounts_institution_id
                   ON accounts(institution_id)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_accounts_status
                   ON accounts(status)"""
            )

            # First, check if account exists and preserve display_name
            cursor.execute(
                "SELECT display_name FROM accounts WHERE id = ?", (account_data["id"],)
            )
            existing_row = cursor.fetchone()
            existing_display_name = existing_row[0] if existing_row else None

            # Use existing display_name if not provided in account_data
            display_name = account_data.get("display_name", existing_display_name)

            # Insert or replace account data
            cursor.execute(
                """INSERT OR REPLACE INTO accounts (
                id,
                institution_id,
                status,
                iban,
                name,
                currency,
                created,
                last_accessed,
                last_updated,
                display_name,
                logo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    account_data["id"],
                    account_data["institution_id"],
                    account_data["status"],
                    account_data.get("iban"),
                    account_data.get("name"),
                    account_data.get("currency"),
                    account_data["created"],
                    account_data.get("last_accessed"),
                    account_data.get("last_updated", account_data["created"]),
                    display_name,
                    account_data.get("logo"),
                ),
            )
            conn.commit()

        return account_data

    def _get_accounts(self, account_ids=None):
        """Get account details from SQLite database"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return []

        query = "SELECT * FROM accounts"
        params = []

        if account_ids:
            placeholders = ",".join("?" * len(account_ids))
            query += f" WHERE id IN ({placeholders})"
            params.extend(account_ids)

        query += " ORDER BY created DESC"

        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def _get_account(self, account_id: str):
        """Get specific account details from SQLite database"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return None

        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def _get_historical_balances(self, account_id=None, days=365):
        """Get historical balance progression based on transaction history"""
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
                WHERE b2.account_id = b1.account_id AND b2.type = b1.type
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

        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(formatted_query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

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
        """Get monthly transaction statistics from SQLite database"""
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

    async def persist_sync_operation(self, sync_operation: Dict[str, Any]) -> int:
        """Persist sync operation to database and return the ID"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, cannot persist sync operation")
            return 0

        try:
            import json
            import sqlite3

            db_path = path_manager.get_database_path()
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Insert sync operation
            cursor.execute(
                """INSERT INTO sync_operations (
                    started_at, completed_at, success, accounts_processed,
                    transactions_added, transactions_updated, balances_updated,
                    duration_seconds, errors, logs, trigger_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    sync_operation.get("started_at"),
                    sync_operation.get("completed_at"),
                    sync_operation.get("success"),
                    sync_operation.get("accounts_processed", 0),
                    sync_operation.get("transactions_added", 0),
                    sync_operation.get("transactions_updated", 0),
                    sync_operation.get("balances_updated", 0),
                    sync_operation.get("duration_seconds"),
                    json.dumps(sync_operation.get("errors", [])),
                    json.dumps(sync_operation.get("logs", [])),
                    sync_operation.get("trigger_type", "manual"),
                ),
            )

            operation_id = cursor.lastrowid
            if operation_id is None:
                raise ValueError("Failed to get operation ID after insert")

            conn.commit()
            conn.close()

            logger.debug(f"Persisted sync operation with ID: {operation_id}")
            return operation_id

        except Exception as e:
            logger.error(f"Failed to persist sync operation: {e}")
            raise

    async def get_sync_operations(
        self, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get sync operations from database"""
        if not self.sqlite_enabled:
            logger.warning("SQLite database disabled, cannot get sync operations")
            return []

        try:
            import json
            import sqlite3

            db_path = path_manager.get_database_path()
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get sync operations ordered by started_at descending
            cursor.execute(
                """SELECT id, started_at, completed_at, success, accounts_processed,
                          transactions_added, transactions_updated, balances_updated,
                          duration_seconds, errors, logs, trigger_type
                   FROM sync_operations
                   ORDER BY started_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset),
            )

            operations = []
            for row in cursor.fetchall():
                operation = {
                    "id": row[0],
                    "started_at": row[1],
                    "completed_at": row[2],
                    "success": bool(row[3]) if row[3] is not None else None,
                    "accounts_processed": row[4],
                    "transactions_added": row[5],
                    "transactions_updated": row[6],
                    "balances_updated": row[7],
                    "duration_seconds": row[8],
                    "errors": json.loads(row[9]) if row[9] else [],
                    "logs": json.loads(row[10]) if row[10] else [],
                    "trigger_type": row[11],
                }
                operations.append(operation)

            conn.close()
            return operations

        except Exception as e:
            logger.error(f"Failed to get sync operations: {e}")
            return []
