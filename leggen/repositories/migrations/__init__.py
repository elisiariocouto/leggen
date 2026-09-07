"""Versioned schema migrations.

The applied version is stamped in SQLite's `PRAGMA user_version`, which is
transactional: each migration and its stamp commit or roll back together, so a
crash can never leave a database recorded as migrated but only half-changed.

Databases created before version tracking start at 0 and replay every step;
each one guards itself, so replaying is a near no-op on an up-to-date schema.
"""

import sqlite3
from pathlib import Path

from loguru import logger

from leggen.errors import UnsupportedDatabaseVersionError
from leggen.repositories.migrations._helpers import table_exists
from leggen.repositories.migrations._steps import (
    DEFAULT_CATEGORIES,
    LATEST_VERSION,
    MIGRATIONS,
    Migration,
)
from leggen.utils.paths import path_manager

__all__ = [
    "DEFAULT_CATEGORIES",
    "LATEST_VERSION",
    "MIGRATIONS",
    "Migration",
    "run_migrations",
]

# The oldest release whose schema this codebase can upgrade. Older migrations
# were retired into the baseline; see _steps.py.
MINIMUM_SUPPORTED_VERSION = "2025.9.22"


def _connect(db_path: Path) -> sqlite3.Connection:
    """Open a connection with explicit transaction control.

    Since Python 3.12 the default `isolation_level=""` no longer opens a
    transaction implicitly around DDL, so migrations must issue their own
    BEGIN. The pragmas mirror `repositories.db.create_connection`.
    """
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def _is_pre_baseline(cursor: sqlite3.Cursor) -> bool:
    """Return True for a database older than the baseline schema.

    The baseline is created with CREATE TABLE IF NOT EXISTS, so it cannot
    reshape tables that already exist. A pre-baseline `transactions` still
    keyed on internalTransactionId would survive untouched and the application
    would fail later with "no such column: transactionId". Detect it up front
    and refuse instead.

    A database with no transactions table is a fresh install, not a legacy one.
    """
    if not table_exists(cursor, "transactions"):
        return False
    primary_key = {
        row[1]: row[5] for row in cursor.execute("PRAGMA table_info(transactions)")
    }
    return not (primary_key.get("accountId") and primary_key.get("transactionId"))


def run_migrations(db_path: Path | None = None) -> int:
    """Bring the database up to the latest schema version.

    Creates the database and its parent directory if absent. Returns the
    version now stamped on it.
    """
    if db_path is None:
        db_path = path_manager.get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = _connect(db_path)
    try:
        cursor = conn.cursor()

        if _is_pre_baseline(cursor):
            raise UnsupportedDatabaseVersionError(
                f"This database predates leggen {MINIMUM_SUPPORTED_VERSION} and cannot "
                "be upgraded directly, because the migrations that would modernize it "
                "have been retired. Upgrade to a release between "
                f"{MINIMUM_SUPPORTED_VERSION} and 2026.8.x, start leggen once so it "
                "migrates, then upgrade to this version."
            )

        current = cursor.execute("PRAGMA user_version").fetchone()[0]
        if current > LATEST_VERSION:
            logger.warning(
                f"Database schema version {current} is newer than this release "
                f"supports ({LATEST_VERSION}); it was likely written by a newer "
                "leggen. Continuing without changes."
            )
            return current

        for migration in MIGRATIONS:
            if migration.version <= current:
                continue

            cursor.execute("BEGIN")
            try:
                migration.apply(cursor)
                # PRAGMA does not accept bound parameters; the value is an int
                # from our own migration list.
                cursor.execute(f"PRAGMA user_version = {migration.version}")
                cursor.execute("COMMIT")
            except Exception:
                cursor.execute("ROLLBACK")
                logger.error(
                    f"Migration {migration.version} ({migration.name}) failed; "
                    "database left at version "
                    f"{cursor.execute('PRAGMA user_version').fetchone()[0]}"
                )
                raise

            logger.info(f"Applied migration {migration.version}: {migration.name}")

        return cursor.execute("PRAGMA user_version").fetchone()[0]
    finally:
        conn.close()
