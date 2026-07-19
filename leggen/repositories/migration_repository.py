import uuid
from datetime import datetime

from loguru import logger

from leggen.repositories.db import create_connection
from leggen.utils.paths import path_manager


class MigrationRepository:
    """Repository for database migrations"""

    async def run_all_migrations(self):
        """Run all necessary database migrations"""
        await self.migrate_balance_timestamps_if_needed()
        await self.migrate_null_transaction_ids_if_needed()
        await self.migrate_to_composite_key_if_needed()
        await self.migrate_add_display_name_if_needed()
        await self.migrate_add_logo_if_needed()
        await self.migrate_add_exclude_from_stats_if_needed()
        await self.migrate_transaction_date_format_if_needed()
        await self.cleanup_orphaned_category_rows()

    async def migrate_transaction_date_format_if_needed(self):
        """Normalize transactionDate values to ISO 8601 T-separated strings.

        Rows written through sqlite3's deprecated datetime adapter used a
        space separator ("YYYY-MM-DD HH:MM:SS"), while newer rows use "T".
        Lexicographic date comparisons require a single format.
        """
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return

        try:
            conn = create_connection(db_path)
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE transactions"
                " SET transactionDate = replace(transactionDate, ' ', 'T')"
                " WHERE transactionDate LIKE '% %'"
            )
            normalized = cursor.rowcount

            conn.commit()
            conn.close()

            if normalized:
                logger.info(
                    f"Normalized {normalized} space-separated transaction dates to ISO format"
                )

        except Exception as e:
            logger.error(f"Failed to normalize transaction date format: {e}")
            raise

    async def cleanup_orphaned_category_rows(self):
        """Remove category link rows orphaned by deletes made before
        foreign key enforcement was enabled (ON DELETE CASCADE never fired)."""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return

        try:
            conn = create_connection(db_path)
            cursor = conn.cursor()

            removed = 0
            for table in ("transaction_categories", "category_keywords"):
                cursor.execute(
                    f"DELETE FROM {table} "
                    "WHERE categoryId NOT IN (SELECT id FROM categories)"
                )
                removed += cursor.rowcount

            conn.commit()
            conn.close()

            if removed:
                logger.info(f"Removed {removed} orphaned category link rows")

        except Exception as e:
            logger.error(f"Failed to clean up orphaned category rows: {e}")
            raise

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
            conn = create_connection(db_path)
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
            conn = create_connection(db_path)
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
            conn = create_connection(db_path)
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
            conn = create_connection(db_path)
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
            conn = create_connection(db_path)
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
            conn = create_connection(db_path)
            cursor = conn.cursor()

            logger.info("Starting composite key migration...")

            # Derive the bank transaction ID with the same fallback chain the
            # sync path uses (EnableBanking is snake_case; legacy GoCardless
            # data was camelCase).
            key_expr = (
                "COALESCE("
                "json_extract(rawTransaction, '$.transaction_id'), "
                "json_extract(rawTransaction, '$.transactionId'), "
                "json_extract(rawTransaction, '$.entry_reference'), "
                "internalTransactionId)"
            )

            cursor.execute("SELECT COUNT(*) FROM transactions")
            source_count = cursor.fetchone()[0]
            cursor.execute(
                f"SELECT COUNT(*) FROM transactions WHERE {key_expr} IS NULL"
            )
            missing_key_count = cursor.fetchone()[0]
            if missing_key_count:
                raise RuntimeError(
                    f"{missing_key_count} of {source_count} transactions have no "
                    "derivable transaction ID; aborting composite key migration "
                    "to avoid data loss"
                )

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
            cursor.execute(f"""
                INSERT INTO transactions_temp
                SELECT
                    accountId,
                    {key_expr} as transactionId,
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
                               PARTITION BY accountId, {key_expr}
                               ORDER BY transactionDate DESC
                           ) as rn
                    FROM transactions
                    WHERE {key_expr} IS NOT NULL
                )
                WHERE rn = 1
            """)

            rows_migrated = cursor.rowcount
            logger.info(
                f"Migrated {rows_migrated} of {source_count} transactions "
                f"({source_count - rows_migrated} duplicates collapsed)"
            )

            logger.info("Replacing old table...")
            cursor.execute("DROP TABLE transactions")
            cursor.execute("ALTER TABLE transactions_temp RENAME TO transactions")

            logger.info("Recreating indexes...")
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
            conn = create_connection(db_path)
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
            conn = create_connection(db_path)
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
            conn = create_connection(db_path)
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
            conn = create_connection(db_path)
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

    # Exclude from stats migration methods
    async def migrate_add_exclude_from_stats_if_needed(self):
        """Check and add exclude_from_stats column to categories table if needed"""
        try:
            if await self._check_exclude_from_stats_migration_needed():
                logger.info("Exclude from stats column migration needed, starting...")
                await self._migrate_add_exclude_from_stats()
                logger.info("Exclude from stats column migration completed")
            else:
                logger.info("Exclude from stats column already exists")
        except Exception as e:
            logger.error(f"Exclude from stats column migration failed: {e}")
            raise

    async def _check_exclude_from_stats_migration_needed(self) -> bool:
        """Check if exclude_from_stats column needs to be added"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            return False

        try:
            conn = create_connection(db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='categories'"
            )
            if not cursor.fetchone():
                conn.close()
                return False

            cursor.execute("PRAGMA table_info(categories)")
            columns = cursor.fetchall()

            has_column = any(col[1] == "exclude_from_stats" for col in columns)

            conn.close()
            return not has_column

        except Exception as e:
            logger.error(f"Failed to check exclude_from_stats migration status: {e}")
            return False

    async def _migrate_add_exclude_from_stats(self):
        """Add exclude_from_stats column to categories table and insert Inter-account category"""
        db_path = path_manager.get_database_path()
        if not db_path.exists():
            logger.warning("Database file not found, skipping migration")
            return

        try:
            conn = create_connection(db_path)
            cursor = conn.cursor()

            logger.info("Adding exclude_from_stats column to categories table...")

            cursor.execute("""
                ALTER TABLE categories
                ADD COLUMN exclude_from_stats BOOLEAN DEFAULT 0
            """)

            # Insert the new Inter-account default category if it doesn't exist
            cursor.execute(
                "SELECT COUNT(*) FROM categories WHERE name = ?",
                ("Inter-account",),
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO categories (name, color, icon, is_default, exclude_from_stats) VALUES (?, ?, ?, 1, 1)",
                    ("Inter-account", "#14b8a6", "arrow-left-right"),
                )
                logger.info("Inserted 'Inter-account' default category")

            conn.commit()
            conn.close()

            logger.info("Exclude from stats column migration completed successfully")

        except Exception as e:
            logger.error(f"Exclude from stats column migration failed: {e}")
            raise
