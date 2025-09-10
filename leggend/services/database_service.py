from datetime import datetime
from typing import List, Dict, Any, Optional
import sqlite3

from loguru import logger

from leggend.config import config
import leggen.database.sqlite as sqlite_db


class DatabaseService:
    def __init__(self):
        self.db_config = config.database_config
        self.sqlite_enabled = self.db_config.get("sqlite", True)

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
        transactions = []

        # Process booked transactions
        for transaction in transaction_data.get("transactions", {}).get("booked", []):
            processed = self._process_single_transaction(
                account_id, account_info, transaction, "booked"
            )
            transactions.append(processed)

        # Process pending transactions
        for transaction in transaction_data.get("transactions", {}).get("pending", []):
            processed = self._process_single_transaction(
                account_id, account_info, transaction, "pending"
            )
            transactions.append(processed)

        return transactions

    def _process_single_transaction(
        self,
        account_id: str,
        account_info: Dict[str, Any],
        transaction: Dict[str, Any],
        status: str,
    ) -> Dict[str, Any]:
        """Process a single transaction into standardized format"""
        # Extract dates
        booked_date = transaction.get("bookingDateTime") or transaction.get(
            "bookingDate"
        )
        value_date = transaction.get("valueDateTime") or transaction.get("valueDate")

        if booked_date and value_date:
            min_date = min(
                datetime.fromisoformat(booked_date), datetime.fromisoformat(value_date)
            )
        else:
            date_str = booked_date or value_date
            if not date_str:
                raise ValueError("No valid date found in transaction")
            min_date = datetime.fromisoformat(date_str)

        # Extract amount and currency
        transaction_amount = transaction.get("transactionAmount", {})
        amount = float(transaction_amount.get("amount", 0))
        currency = transaction_amount.get("currency", "")

        # Extract description
        description = transaction.get(
            "remittanceInformationUnstructured",
            ",".join(transaction.get("remittanceInformationUnstructuredArray", [])),
        )

        # Extract transaction IDs - transactionId is now primary, internalTransactionId is reference
        transaction_id = transaction.get("transactionId")
        internal_transaction_id = transaction.get("internalTransactionId")

        if not transaction_id:
            raise ValueError("Transaction missing required transactionId field")

        return {
            "accountId": account_id,
            "transactionId": transaction_id,
            "internalTransactionId": internal_transaction_id,
            "institutionId": account_info["institution_id"],
            "iban": account_info.get("iban", "N/A"),
            "transactionDate": min_date,
            "description": description,
            "transactionValue": amount,
            "transactionCurrency": currency,
            "transactionStatus": status,
            "rawTransaction": transaction,
        }

    async def get_transactions_from_db(
        self,
        account_id: Optional[str] = None,
        limit: Optional[int] = 100,
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
            transactions = sqlite_db.get_transactions(
                account_id=account_id,
                limit=limit or 100,
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

            count = sqlite_db.get_transaction_count(account_id=account_id, **filters)
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
            balances = sqlite_db.get_balances(account_id=account_id)
            logger.debug(f"Retrieved {len(balances)} balances from database")
            return balances
        except Exception as e:
            logger.error(f"Failed to get balances from database: {e}")
            return []

    async def get_account_summary_from_db(
        self, account_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get basic account info from SQLite database (avoids GoCardless call)"""
        if not self.sqlite_enabled:
            return None

        try:
            summary = sqlite_db.get_account_summary(account_id)
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
            accounts = sqlite_db.get_accounts(account_ids=account_ids)
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
            account = sqlite_db.get_account(account_id)
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
        from pathlib import Path

        db_path = Path.home() / ".config" / "leggen" / "leggen.db"
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
        from pathlib import Path

        db_path = Path.home() / ".config" / "leggen" / "leggen.db"
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
        from pathlib import Path

        db_path = Path.home() / ".config" / "leggen" / "leggen.db"
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
        from pathlib import Path

        db_path = Path.home() / ".config" / "leggen" / "leggen.db"
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
        from pathlib import Path

        db_path = Path.home() / ".config" / "leggen" / "leggen.db"
        if not db_path.exists():
            return False

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check if transactions table has the old primary key structure
            cursor.execute("PRAGMA table_info(transactions)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            # If we have internalTransactionId as primary key, migration is needed
            if "internalTransactionId" in column_names:
                # Check if there are duplicate (accountId, transactionId) pairs
                cursor.execute("""
                    SELECT COUNT(*) as duplicates
                    FROM (
                        SELECT accountId, json_extract(rawTransaction, '$.transactionId') as transactionId, COUNT(*) as cnt
                        FROM transactions
                        WHERE json_extract(rawTransaction, '$.transactionId') IS NOT NULL
                        GROUP BY accountId, json_extract(rawTransaction, '$.transactionId')
                        HAVING COUNT(*) > 1
                    )
                """)
                duplicates = cursor.fetchone()[0]
                conn.close()
                return duplicates > 0
            else:
                conn.close()
                return False

        except Exception as e:
            logger.error(f"Failed to check composite key migration status: {e}")
            return False

    async def _migrate_to_composite_key(self):
        """Migrate transactions table to use composite primary key (accountId, transactionId)"""
        from pathlib import Path

        db_path = Path.home() / ".config" / "leggen" / "leggen.db"
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

            from pathlib import Path

            db_path = Path.home() / ".config" / "leggen" / "leggen.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
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
            import sqlite3
            import json

            from pathlib import Path

            db_path = Path.home() / ".config" / "leggen" / "leggen.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
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
            from pathlib import Path

            db_path = Path.home() / ".config" / "leggen" / "leggen.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # Use the sqlite_db module function
            sqlite_db.persist_account(account_data)

            logger.info(
                f"Persisted account details to SQLite for account {account_data['id']}"
            )
        except Exception as e:
            logger.error(f"Failed to persist account details to SQLite: {e}")
            raise
