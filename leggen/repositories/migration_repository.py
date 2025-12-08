import sqlite3
import uuid
from datetime import datetime

from loguru import logger

from leggen.repositories.base_repository import BaseRepository
from leggen.utils.paths import path_manager


class MigrationRepository(BaseRepository):
    """Repository for database migrations"""

    async def run_all_migrations(self):
        """Run all necessary database migrations"""
        await self.migrate_balance_timestamps_if_needed()
        await self.migrate_null_transaction_ids_if_needed()
        await self.migrate_to_composite_key_if_needed()
        await self.migrate_add_display_name_if_needed()
        await self.migrate_add_sync_operations_if_needed()
        await self.migrate_add_logo_if_needed()

    # Balance timestamp migration methods
    async def migrate_balance_timestamps_if_needed(self):
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

            cursor.execute("""
                SELECT typeof(timestamp) as type, COUNT(*) as count
                FROM balances
                GROUP BY typeof(timestamp)
            """)

            types = cursor.fetchall()
            conn.close()

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

            batch_size = 100
            migrated_count = 0

            for i in range(0, total_records, batch_size):
                batch = unix_records[i : i + batch_size]

                for record_id, unix_timestamp in batch:
                    try:
                        dt_string = self._unix_to_datetime_string(float(unix_timestamp))

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

                conn.commit()

            conn.close()
            logger.info(f"Successfully migrated {migrated_count} balance records")

        except Exception as e:
            logger.error(f"Balance timestamp migration failed: {e}")
            raise

    def _unix_to_datetime_string(self, unix_timestamp: float) -> str:
        """Convert Unix timestamp to datetime string"""
        dt = datetime.fromtimestamp(unix_timestamp)
        return dt.isoformat()

    # Null transaction IDs migration methods
    async def migrate_null_transaction_ids_if_needed(self):
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
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            logger.warning("Database file not found, skipping migration")
            return

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

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

            batch_size = 100
            migrated_count = 0

            for i in range(0, total_records, batch_size):
                batch = null_records[i : i + batch_size]

                for rowid, transaction_id in batch:
                    try:
                        cursor.execute(
                            "SELECT COUNT(*) FROM transactions WHERE internalTransactionId = ?",
                            (str(transaction_id),),
                        )
                        existing_count = cursor.fetchone()[0]

                        if existing_count > 0:
                            unique_id = f"{str(transaction_id)}_{uuid.uuid4().hex[:8]}"
                            logger.debug(
                                f"Generated unique ID for duplicate transactionId: {unique_id}"
                            )
                        else:
                            unique_id = str(transaction_id)

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

                conn.commit()

            conn.close()
            logger.info(f"Successfully migrated {migrated_count} transaction records")

        except Exception as e:
            logger.error(f"Null transaction IDs migration failed: {e}")
            raise

    # Composite key migration methods
    async def migrate_to_composite_key_if_needed(self):
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

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'"
            )
            if not cursor.fetchone():
                conn.close()
                return False

            cursor.execute("PRAGMA table_info(transactions)")
            columns = cursor.fetchall()

            internal_transaction_id_is_pk = any(
                col[1] == "internalTransactionId" and col[5] == 1 for col in columns
            )

            has_composite_key = any(
                col[1] in ["accountId", "transactionId"] and col[5] == 1
                for col in columns
            )

            conn.close()

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
                               ORDER BY transactionDate DESC
                           ) as rn
                    FROM transactions
                    WHERE json_extract(rawTransaction, '$.transactionId') IS NOT NULL
                )
                WHERE rn = 1
            """)

            rows_migrated = cursor.rowcount
            logger.info(f"Migrated {rows_migrated} unique transactions")

            logger.info("Replacing old table...")
            cursor.execute("DROP TABLE transactions")
            cursor.execute("ALTER TABLE transactions_temp RENAME TO transactions")

            logger.info("Recreating indexes...")
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

            conn.commit()
            conn.close()

            logger.info("Composite key migration completed successfully")

        except Exception as e:
            logger.error(f"Composite key migration failed: {e}")
            raise

    # Display name migration methods
    async def migrate_add_display_name_if_needed(self):
        """Check and add display_name column if needed"""
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
        """Check if display_name column needs to be added"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return False

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'"
            )
            if not cursor.fetchone():
                conn.close()
                return False

            cursor.execute("PRAGMA table_info(accounts)")
            columns = cursor.fetchall()

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

    # Sync operations migration methods
    async def migrate_add_sync_operations_if_needed(self):
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

    async def _check_sync_operations_migration_needed(self) -> bool:
        """Check if sync_operations table needs to be created"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return False

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

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

    # Logo migration methods
    async def migrate_add_logo_if_needed(self):
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

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'"
            )
            if not cursor.fetchone():
                conn.close()
                return False

            cursor.execute("PRAGMA table_info(accounts)")
            columns = cursor.fetchall()

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
