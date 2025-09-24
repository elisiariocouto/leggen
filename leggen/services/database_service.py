import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger

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

        await self._migrate_balance_timestamps_if_needed()
        await self._migrate_null_transaction_ids_if_needed()
        await self._migrate_to_composite_key_if_needed()
        await self._migrate_add_display_name_if_needed()
        await self._migrate_add_sync_operations_if_needed()
        await self._migrate_add_logo_if_needed()

    async def _migrate_balance_timestamps_if_needed(self):
        """Check and migrate balance timestamps if needed"""
        try:
            if await self._check_balance_timestamp_migration_needed():
                logger.info("Balance timestamp migration needed, starting...")
                await self._migrate_balance_timestamps()
                logger.info("Balance timestamp migration completed")
            else:
                logger.info("Balance timestamps are already consistent")
        except Exception as e:
            logger.error(f"Balance timestamp migration failed: {e}")
            raise

    async def _check_balance_timestamp_migration_needed(self) -> bool:
        """Check if balance timestamps need migration"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return False

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check for mixed timestamp types
            cursor.execute("""
                SELECT typeof(timestamp) as type, COUNT(*) as count
                FROM balances
                GROUP BY typeof(timestamp)
            """)

            types = cursor.fetchall()
            conn.close()

            # If we have both 'real' and 'text' types, migration is needed
            type_names = [row[0] for row in types]
            return "real" in type_names and "text" in type_names

        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return False

    async def _migrate_balance_timestamps(self):
        """Convert all Unix timestamps to datetime strings"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            logger.warning("Database file not found, skipping migration")
            return

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get all balances with REAL timestamps
            cursor.execute("""
                SELECT id, timestamp
                FROM balances
                WHERE typeof(timestamp) = 'real'
                ORDER BY id
            """)

            unix_records = cursor.fetchall()
            total_records = len(unix_records)

            if total_records == 0:
                logger.info("No Unix timestamps found to migrate")
                conn.close()
                return

            logger.info(
                f"Migrating {total_records} balance records from Unix to datetime format"
            )

            # Convert and update in batches
            batch_size = 100
            migrated_count = 0

            for i in range(0, total_records, batch_size):
                batch = unix_records[i : i + batch_size]

                for record_id, unix_timestamp in batch:
                    try:
                        # Convert Unix timestamp to datetime string
                        dt_string = self._unix_to_datetime_string(float(unix_timestamp))

                        # Update the record
                        cursor.execute(
                            """
                            UPDATE balances
                            SET timestamp = ?
                            WHERE id = ?
                        """,
                            (dt_string, record_id),
                        )

                        migrated_count += 1

                        if migrated_count % 100 == 0:
                            logger.info(
                                f"Migrated {migrated_count}/{total_records} balance records"
                            )

                    except Exception as e:
                        logger.error(f"Failed to migrate record {record_id}: {e}")
                        continue

                # Commit batch
                conn.commit()

            conn.close()
            logger.info(f"Successfully migrated {migrated_count} balance records")

        except Exception as e:
            logger.error(f"Balance timestamp migration failed: {e}")
            raise

    async def _migrate_null_transaction_ids_if_needed(self):
        """Check and migrate null transaction IDs if needed"""
        try:
            if await self._check_null_transaction_ids_migration_needed():
                logger.info("Null transaction IDs migration needed, starting...")
                await self._migrate_null_transaction_ids()
                logger.info("Null transaction IDs migration completed")
            else:
                logger.info("No null transaction IDs found to migrate")
        except Exception as e:
            logger.error(f"Null transaction IDs migration failed: {e}")
            raise

    async def _check_null_transaction_ids_migration_needed(self) -> bool:
        """Check if null transaction IDs need migration"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return False

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check for transactions with null or empty internalTransactionId
            cursor.execute("""
                SELECT COUNT(*)
                FROM transactions
                WHERE (internalTransactionId IS NULL OR internalTransactionId = '')
                AND json_extract(rawTransaction, '$.transactionId') IS NOT NULL
            """)

            count = cursor.fetchone()[0]
            conn.close()

            return count > 0

        except Exception as e:
            logger.error(f"Failed to check null transaction IDs migration status: {e}")
            return False

    async def _migrate_null_transaction_ids(self):
        """Populate null internalTransactionId fields using transactionId from raw data"""
        import uuid

        db_path = path_manager.get_database_path()
        if not db_path.exists():
            logger.warning("Database file not found, skipping migration")
            return

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get all transactions with null/empty internalTransactionId but valid transactionId in raw data
            cursor.execute("""
                SELECT rowid, json_extract(rawTransaction, '$.transactionId') as transactionId
                FROM transactions
                WHERE (internalTransactionId IS NULL OR internalTransactionId = '')
                AND json_extract(rawTransaction, '$.transactionId') IS NOT NULL
                ORDER BY rowid
            """)

            null_records = cursor.fetchall()
            total_records = len(null_records)

            if total_records == 0:
                logger.info("No null transaction IDs found to migrate")
                conn.close()
                return

            logger.info(
                f"Migrating {total_records} transaction records with null internalTransactionId"
            )

            # Update in batches
            batch_size = 100
            migrated_count = 0
            skipped_duplicates = 0

            for i in range(0, total_records, batch_size):
                batch = null_records[i : i + batch_size]

                for rowid, transaction_id in batch:
                    try:
                        # Check if this transactionId is already used by another record
                        cursor.execute(
                            "SELECT COUNT(*) FROM transactions WHERE internalTransactionId = ?",
                            (str(transaction_id),),
                        )
                        existing_count = cursor.fetchone()[0]

                        if existing_count > 0:
                            # Generate a unique ID to avoid constraint violation
                            unique_id = f"{str(transaction_id)}_{uuid.uuid4().hex[:8]}"
                            logger.debug(
                                f"Generated unique ID for duplicate transactionId: {unique_id}"
                            )
                        else:
                            # Use the original transactionId
                            unique_id = str(transaction_id)

                        # Update the record
                        cursor.execute(
                            """
                            UPDATE transactions
                            SET internalTransactionId = ?
                            WHERE rowid = ?
                            """,
                            (unique_id, rowid),
                        )

                        migrated_count += 1

                        if migrated_count % 100 == 0:
                            logger.info(
                                f"Migrated {migrated_count}/{total_records} transaction records"
                            )

                    except Exception as e:
                        logger.error(f"Failed to migrate record {rowid}: {e}")
                        continue

                # Commit batch
                conn.commit()

            conn.close()
            logger.info(f"Successfully migrated {migrated_count} transaction records")
            if skipped_duplicates > 0:
                logger.info(
                    f"Generated unique IDs for {skipped_duplicates} duplicate transactionIds"
                )

        except Exception as e:
            logger.error(f"Null transaction IDs migration failed: {e}")
            raise

    async def _migrate_to_composite_key_if_needed(self):
        """Check and migrate to composite primary key if needed"""
        try:
            if await self._check_composite_key_migration_needed():
                logger.info("Composite key migration needed, starting...")
                await self._migrate_to_composite_key()
                logger.info("Composite key migration completed")
            else:
                logger.info("Composite key migration not needed")
        except Exception as e:
            logger.error(f"Composite key migration failed: {e}")
            raise

    async def _check_composite_key_migration_needed(self) -> bool:
        """Check if composite key migration is needed"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return False

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check if transactions table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'"
            )
            if not cursor.fetchone():
                conn.close()
                return False

            # Check if transactions table has the old primary key structure
            cursor.execute("PRAGMA table_info(transactions)")
            columns = cursor.fetchall()

            # Check if internalTransactionId is the primary key (old structure)
            internal_transaction_id_is_pk = any(
                col[1] == "internalTransactionId" and col[5] == 1  # col[5] is pk flag
                for col in columns
            )

            # Check if we have the new composite primary key structure
            has_composite_key = any(
                col[1] in ["accountId", "transactionId"]
                and col[5] == 1  # col[5] is pk flag
                for col in columns
            )

            conn.close()

            # Migration is needed if:
            # 1. internalTransactionId is still the primary key (old structure), OR
            # 2. We don't have the new composite key structure yet
            return internal_transaction_id_is_pk or not has_composite_key

        except Exception as e:
            logger.error(f"Failed to check composite key migration status: {e}")
            return False

    async def _migrate_to_composite_key(self):
        """Migrate transactions table to use composite primary key (accountId, transactionId)"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            logger.warning("Database file not found, skipping migration")
            return

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            logger.info("Starting composite key migration...")

            # Step 1: Create temporary table with new schema
            logger.info("Creating temporary table with composite primary key...")
            cursor.execute("DROP TABLE IF EXISTS transactions_temp")
            cursor.execute("""
                CREATE TABLE transactions_temp (
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
                )
            """)

            # Step 2: Insert deduplicated data (keep most recent duplicate)
            logger.info("Inserting deduplicated data...")
            cursor.execute("""
                INSERT INTO transactions_temp
                SELECT
                    accountId,
                    json_extract(rawTransaction, '$.transactionId') as transactionId,
                    internalTransactionId,
                    institutionId,
                    iban,
                    transactionDate,
                    description,
                    transactionValue,
                    transactionCurrency,
                    transactionStatus,
                    rawTransaction
                FROM (
                    SELECT *,
                           ROW_NUMBER() OVER (
                               PARTITION BY accountId, json_extract(rawTransaction, '$.transactionId')
                               ORDER BY transactionDate DESC, rowid DESC
                           ) as rn
                    FROM transactions
                    WHERE json_extract(rawTransaction, '$.transactionId') IS NOT NULL
                    AND accountId IS NOT NULL
                ) WHERE rn = 1
            """)

            # Get counts for reporting
            cursor.execute("SELECT COUNT(*) FROM transactions")
            old_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM transactions_temp")
            new_count = cursor.fetchone()[0]

            duplicates_removed = old_count - new_count
            logger.info(
                f"Migration stats: {old_count} → {new_count} records ({duplicates_removed} duplicates removed)"
            )

            # Step 3: Replace tables
            logger.info("Replacing tables...")
            cursor.execute("ALTER TABLE transactions RENAME TO transactions_old")
            cursor.execute("ALTER TABLE transactions_temp RENAME TO transactions")

            # Step 4: Recreate indexes
            logger.info("Recreating indexes...")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_internal_id ON transactions(internalTransactionId)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transactionDate)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_account_date ON transactions(accountId, transactionDate)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions(transactionValue)"
            )

            # Step 5: Cleanup
            logger.info("Cleaning up...")
            cursor.execute("DROP TABLE transactions_old")

            conn.commit()
            conn.close()

            logger.info("Composite key migration completed successfully")

        except Exception as e:
            logger.error(f"Composite key migration failed: {e}")
            raise

    async def _migrate_add_display_name_if_needed(self):
        """Check and add display_name column to accounts table if needed"""
        try:
            if await self._check_display_name_migration_needed():
                logger.info("Display name column migration needed, starting...")
                await self._migrate_add_display_name()
                logger.info("Display name column migration completed")
            else:
                logger.info("Display name column already exists")
        except Exception as e:
            logger.error(f"Display name column migration failed: {e}")
            raise

    async def _check_display_name_migration_needed(self) -> bool:
        """Check if display_name column needs to be added to accounts table"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return False

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check if accounts table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'"
            )
            if not cursor.fetchone():
                conn.close()
                return False

            # Check if display_name column exists
            cursor.execute("PRAGMA table_info(accounts)")
            columns = cursor.fetchall()

            # Check if display_name column exists
            has_display_name = any(col[1] == "display_name" for col in columns)

            conn.close()
            return not has_display_name

        except Exception as e:
            logger.error(f"Failed to check display_name migration status: {e}")
            return False

    async def _migrate_add_display_name(self):
        """Add display_name column to accounts table"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            logger.warning("Database file not found, skipping migration")
            return

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            logger.info("Adding display_name column to accounts table...")

            # Add the display_name column
            cursor.execute("""
                ALTER TABLE accounts
                ADD COLUMN display_name TEXT
            """)

            conn.commit()
            conn.close()

            logger.info("Display name column migration completed successfully")

        except Exception as e:
            logger.error(f"Display name column migration failed: {e}")
            raise

    def _unix_to_datetime_string(self, unix_timestamp: float) -> str:
        """Convert Unix timestamp to datetime string"""
        dt = datetime.fromtimestamp(unix_timestamp)
        return dt.isoformat()

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
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        cursor = conn.cursor()

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

        try:
            cursor.execute(query, params)
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

            conn.close()
            return transactions

        except Exception as e:
            conn.close()
            raise e

    def _get_balances(self, account_id=None):
        """Get latest balances from SQLite database"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return []
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

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

        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()

            balances = [dict(row) for row in rows]
            conn.close()
            return balances

        except Exception as e:
            conn.close()
            raise e

    def _get_account_summary(self, account_id):
        """Get basic account info from transactions table (avoids GoCardless API call)"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return None
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Get account info from most recent transaction
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
            conn.close()

            if row:
                return dict(row)
            return None

        except Exception as e:
            conn.close()
            raise e

    def _get_transaction_count(self, account_id=None, **filters):
        """Get total count of transactions matching filters"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return 0
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

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

        try:
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            conn.close()
            return count

        except Exception as e:
            conn.close()
            raise e

    def _persist_account(self, account_data: dict):
        """Persist account details to SQLite database"""
        db_path = path_manager.get_database_path()
        conn = sqlite3.connect(str(db_path))
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

        try:
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
            conn.close()

            return account_data

        except Exception as e:
            conn.close()
            raise e

    def _get_accounts(self, account_ids=None):
        """Get account details from SQLite database"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return []
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM accounts"
        params = []

        if account_ids:
            placeholders = ",".join("?" * len(account_ids))
            query += f" WHERE id IN ({placeholders})"
            params.extend(account_ids)

        query += " ORDER BY created DESC"

        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()

            accounts = [dict(row) for row in rows]
            conn.close()
            return accounts

        except Exception as e:
            conn.close()
            raise e

    def _get_account(self, account_id: str):
        """Get specific account details from SQLite database"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return None
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None

        except Exception as e:
            conn.close()
            raise e

    def _get_historical_balances(self, account_id=None, days=365):
        """Get historical balance progression based on transaction history"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return []

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
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

            cursor.execute(formatted_query, params)
            rows = cursor.fetchall()

            conn.close()
            return [dict(row) for row in rows]

        except Exception as e:
            conn.close()
            raise e

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

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
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

            cursor.execute(query, params)
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

            conn.close()
            return monthly_stats

        except Exception as e:
            conn.close()
            raise e

    async def _check_sync_operations_migration_needed(self) -> bool:
        """Check if sync_operations table needs to be created"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return False

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check if sync_operations table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sync_operations'"
            )
            table_exists = cursor.fetchone() is not None

            conn.close()
            return not table_exists

        except Exception as e:
            logger.error(f"Failed to check sync_operations migration status: {e}")
            return False

    async def _migrate_add_sync_operations(self):
        """Add sync_operations table"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            logger.warning("Database file not found, skipping migration")
            return

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            logger.info("Creating sync_operations table...")

            # Create the sync_operations table
            cursor.execute("""
                CREATE TABLE sync_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at DATETIME NOT NULL,
                    completed_at DATETIME,
                    success BOOLEAN,
                    accounts_processed INTEGER DEFAULT 0,
                    transactions_added INTEGER DEFAULT 0,
                    transactions_updated INTEGER DEFAULT 0,
                    balances_updated INTEGER DEFAULT 0,
                    duration_seconds REAL,
                    errors TEXT,
                    logs TEXT,
                    trigger_type TEXT DEFAULT 'manual'
                )
            """)

            # Create indexes for better performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_sync_operations_started_at ON sync_operations(started_at)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_sync_operations_success ON sync_operations(success)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_sync_operations_trigger_type ON sync_operations(trigger_type)"
            )

            conn.commit()
            conn.close()

            logger.info("Sync operations table migration completed successfully")

        except Exception as e:
            logger.error(f"Sync operations table migration failed: {e}")
            raise

    async def _migrate_add_sync_operations_if_needed(self):
        """Check and add sync_operations table if needed"""
        try:
            if await self._check_sync_operations_migration_needed():
                logger.info("Sync operations table migration needed, starting...")
                await self._migrate_add_sync_operations()
                logger.info("Sync operations table migration completed")
            else:
                logger.info("Sync operations table already exists")
        except Exception as e:
            logger.error(f"Sync operations table migration failed: {e}")
            raise

    async def _migrate_add_logo_if_needed(self):
        """Check and add logo column to accounts table if needed"""
        try:
            if await self._check_logo_migration_needed():
                logger.info("Logo column migration needed, starting...")
                await self._migrate_add_logo()
                logger.info("Logo column migration completed")
            else:
                logger.info("Logo column already exists")
        except Exception as e:
            logger.error(f"Logo column migration failed: {e}")
            raise

    async def _check_logo_migration_needed(self) -> bool:
        """Check if logo column needs to be added to accounts table"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return False

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check if accounts table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'"
            )
            if not cursor.fetchone():
                conn.close()
                return False

            # Check if logo column exists
            cursor.execute("PRAGMA table_info(accounts)")
            columns = cursor.fetchall()

            # Check if logo column exists
            has_logo = any(col[1] == "logo" for col in columns)

            conn.close()
            return not has_logo

        except Exception as e:
            logger.error(f"Failed to check logo migration status: {e}")
            return False

    async def _migrate_add_logo(self):
        """Add logo column to accounts table"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            logger.warning("Database file not found, skipping migration")
            return

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            logger.info("Adding logo column to accounts table...")

            # Add the logo column
            cursor.execute("""
                ALTER TABLE accounts
                ADD COLUMN logo TEXT
            """)

            conn.commit()
            conn.close()

            logger.info("Logo column migration completed successfully")

        except Exception as e:
            logger.error(f"Logo column migration failed: {e}")
            raise

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
