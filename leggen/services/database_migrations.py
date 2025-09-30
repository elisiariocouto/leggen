"""Database migration functions for Leggen."""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from loguru import logger


def run_all_migrations(db_path: Path) -> None:
    """Run all necessary database migrations."""
    if not db_path.exists():
        logger.info("Database file not found, skipping migrations")
        return

    migrate_balance_timestamps_if_needed(db_path)
    migrate_null_transaction_ids_if_needed(db_path)
    migrate_to_composite_key_if_needed(db_path)
    migrate_add_display_name_if_needed(db_path)
    migrate_add_sync_operations_if_needed(db_path)
    migrate_add_logo_if_needed(db_path)


def migrate_balance_timestamps_if_needed(db_path: Path) -> None:
    """Check and migrate balance timestamps if needed."""
    try:
        if _check_balance_timestamp_migration_needed(db_path):
            logger.info("Balance timestamp migration needed, starting...")
            _migrate_balance_timestamps(db_path)
            logger.info("Balance timestamp migration completed")
        else:
            logger.info("Balance timestamps are already consistent")
    except Exception as e:
        logger.error(f"Balance timestamp migration failed: {e}")
        raise


def _check_balance_timestamp_migration_needed(db_path: Path) -> bool:
    """Check if balance timestamps need migration."""
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


def _migrate_balance_timestamps(db_path: Path) -> None:
    """Convert all Unix timestamps to datetime strings."""
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
                    dt_string = _unix_to_datetime_string(float(unix_timestamp))

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


def migrate_null_transaction_ids_if_needed(db_path: Path) -> None:
    """Check and migrate null transaction IDs if needed."""
    try:
        if _check_null_transaction_ids_migration_needed(db_path):
            logger.info("Null transaction IDs migration needed, starting...")
            _migrate_null_transaction_ids(db_path)
            logger.info("Null transaction IDs migration completed")
        else:
            logger.info("No null transaction IDs found to migrate")
    except Exception as e:
        logger.error(f"Null transaction IDs migration failed: {e}")
        raise


def _check_null_transaction_ids_migration_needed(db_path: Path) -> bool:
    """Check if null transaction IDs need migration."""
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


def _migrate_null_transaction_ids(db_path: Path) -> None:
    """Populate null internalTransactionId fields using transactionId from raw data."""
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


def migrate_to_composite_key_if_needed(db_path: Path) -> None:
    """Check and migrate to composite primary key if needed."""
    try:
        if _check_composite_key_migration_needed(db_path):
            logger.info("Composite key migration needed, starting...")
            _migrate_to_composite_key(db_path)
            logger.info("Composite key migration completed")
        else:
            logger.info("Composite key migration not needed")
    except Exception as e:
        logger.error(f"Composite key migration failed: {e}")
        raise


def _check_composite_key_migration_needed(db_path: Path) -> bool:
    """Check if composite key migration is needed."""
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


def _migrate_to_composite_key(db_path: Path) -> None:
    """Migrate transactions table to use composite primary key (accountId, transactionId)."""
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


def migrate_add_display_name_if_needed(db_path: Path) -> None:
    """Check and add display_name column to accounts table if needed."""
    try:
        if _check_display_name_migration_needed(db_path):
            logger.info("Display name column migration needed, starting...")
            _migrate_add_display_name(db_path)
            logger.info("Display name column migration completed")
        else:
            logger.info("Display name column already exists")
    except Exception as e:
        logger.error(f"Display name column migration failed: {e}")
        raise


def _check_display_name_migration_needed(db_path: Path) -> bool:
    """Check if display_name column needs to be added to accounts table."""
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


def _migrate_add_display_name(db_path: Path) -> None:
    """Add display_name column to accounts table."""
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


def migrate_add_sync_operations_if_needed(db_path: Path) -> None:
    """Check and add sync_operations table if needed."""
    try:
        if _check_sync_operations_migration_needed(db_path):
            logger.info("Sync operations table migration needed, starting...")
            _migrate_add_sync_operations(db_path)
            logger.info("Sync operations table migration completed")
        else:
            logger.info("Sync operations table already exists")
    except Exception as e:
        logger.error(f"Sync operations table migration failed: {e}")
        raise


def _check_sync_operations_migration_needed(db_path: Path) -> bool:
    """Check if sync_operations table needs to be created."""
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


def _migrate_add_sync_operations(db_path: Path) -> None:
    """Add sync_operations table."""
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


def migrate_add_logo_if_needed(db_path: Path) -> None:
    """Check and add logo column to accounts table if needed."""
    try:
        if _check_logo_migration_needed(db_path):
            logger.info("Logo column migration needed, starting...")
            _migrate_add_logo(db_path)
            logger.info("Logo column migration completed")
        else:
            logger.info("Logo column already exists")
    except Exception as e:
        logger.error(f"Logo column migration failed: {e}")
        raise


def _check_logo_migration_needed(db_path: Path) -> bool:
    """Check if logo column needs to be added to accounts table."""
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


def _migrate_add_logo(db_path: Path) -> None:
    """Add logo column to accounts table."""
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


def _unix_to_datetime_string(unix_timestamp: float) -> str:
    """Convert Unix timestamp to datetime string."""
    dt = datetime.fromtimestamp(unix_timestamp)
    return dt.isoformat()
