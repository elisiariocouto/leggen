"""Ordered schema migrations.

Version 1 is the baseline: the full schema as of release 2025.9.22, which is
the oldest database this codebase can upgrade. The migrations that produced
that shape (balance timestamps, null transaction IDs, the composite primary
key, and the accounts display_name/logo columns) were retired once they were a
year old; `leggen.repositories.migrations` refuses to touch a database that
never had them applied.

Add a schema change by appending a Migration here. Versions are contiguous
from 1 and are validated at import.
"""

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass

from leggen.repositories.migrations._helpers import (
    add_column_if_missing,
    column_exists,
)

# Seeded into `categories` when the table is empty. Lives here rather than in
# the repository because it is schema seed data, not query logic.
DEFAULT_CATEGORIES: list[dict[str, object]] = [
    {
        "name": "Groceries",
        "color": "#22c55e",
        "icon": "shopping-cart",
        "exclude_from_stats": False,
    },
    {
        "name": "Transport",
        "color": "#3b82f6",
        "icon": "car",
        "exclude_from_stats": False,
    },
    {
        "name": "Salary",
        "color": "#a855f7",
        "icon": "banknote",
        "exclude_from_stats": False,
    },
    {
        "name": "Dining",
        "color": "#f97316",
        "icon": "utensils",
        "exclude_from_stats": False,
    },
    {
        "name": "Shopping",
        "color": "#ec4899",
        "icon": "shopping-bag",
        "exclude_from_stats": False,
    },
    {
        "name": "Utilities",
        "color": "#64748b",
        "icon": "zap",
        "exclude_from_stats": False,
    },
    {
        "name": "Entertainment",
        "color": "#eab308",
        "icon": "film",
        "exclude_from_stats": False,
    },
    {
        "name": "Healthcare",
        "color": "#ef4444",
        "icon": "heart-pulse",
        "exclude_from_stats": False,
    },
    {
        "name": "Transfer",
        "color": "#06b6d4",
        "icon": "arrow-right-left",
        "exclude_from_stats": False,
    },
    {
        "name": "Inter-account",
        "color": "#14b8a6",
        "icon": "arrow-left-right",
        "exclude_from_stats": True,
    },
    {"name": "Cash", "color": "#84cc16", "icon": "wallet", "exclude_from_stats": False},
    {
        "name": "Subscriptions",
        "color": "#8b5cf6",
        "icon": "repeat",
        "exclude_from_stats": False,
    },
    {"name": "Other", "color": "#6b7280", "icon": "tag", "exclude_from_stats": False},
]

_BASELINE_TABLES = (
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
    )""",
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
    )""",
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
    )""",
    """CREATE TABLE IF NOT EXISTS sync_operations (
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
        trigger_type TEXT DEFAULT 'manual',
        warnings TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        aspsp_name TEXT NOT NULL,
        aspsp_country TEXT NOT NULL,
        accounts JSON,
        valid_until DATETIME,
        created_at DATETIME,
        status TEXT DEFAULT 'active'
    )""",
    """CREATE TABLE IF NOT EXISTS expiry_notifications (
        session_id TEXT NOT NULL,
        threshold INTEGER NOT NULL,
        sent_at DATETIME NOT NULL,
        PRIMARY KEY (session_id, threshold)
    )""",
    """CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        color TEXT DEFAULT '#6b7280',
        icon TEXT,
        is_default BOOLEAN DEFAULT 0,
        exclude_from_stats BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS transaction_categories (
        accountId TEXT NOT NULL,
        transactionId TEXT NOT NULL,
        categoryId INTEGER NOT NULL,
        assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (accountId, transactionId),
        FOREIGN KEY (categoryId) REFERENCES categories(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS category_keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        categoryId INTEGER NOT NULL,
        frequency INTEGER DEFAULT 1,
        UNIQUE(keyword, categoryId),
        FOREIGN KEY (categoryId) REFERENCES categories(id) ON DELETE CASCADE
    )""",
)

_BASELINE_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_accounts_institution_id ON accounts(institution_id)",
    "CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status)",
    "CREATE INDEX IF NOT EXISTS idx_balances_account_id ON balances(account_id)",
    "CREATE INDEX IF NOT EXISTS idx_balances_timestamp ON balances(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_balances_account_type_timestamp ON balances(account_id, type, timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transactionDate)",
    "CREATE INDEX IF NOT EXISTS idx_transactions_account_date ON transactions(accountId, transactionDate)",
    "CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions(transactionValue)",
    # Merchant analytics group by description; without this the group-by
    # full-scans the table.
    "CREATE INDEX IF NOT EXISTS idx_transactions_description ON transactions(description)",
    "CREATE INDEX IF NOT EXISTS idx_sync_operations_started_at ON sync_operations(started_at)",
    "CREATE INDEX IF NOT EXISTS idx_sync_operations_success ON sync_operations(success)",
    "CREATE INDEX IF NOT EXISTS idx_sync_operations_trigger_type ON sync_operations(trigger_type)",
    "CREATE INDEX IF NOT EXISTS idx_tc_category ON transaction_categories(categoryId)",
    "CREATE INDEX IF NOT EXISTS idx_ck_keyword ON category_keywords(keyword)",
    "CREATE INDEX IF NOT EXISTS idx_ck_category ON category_keywords(categoryId)",
)


def _baseline_schema(cursor: sqlite3.Cursor) -> None:
    """Create every table and index, and seed the default categories.

    On a database created before version tracking the tables already exist, so
    each statement is a no-op and the later migrations do the upgrading.
    """
    for statement in _BASELINE_TABLES:
        cursor.execute(statement)
    for statement in _BASELINE_INDEXES:
        cursor.execute(statement)

    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0]:
        return

    # A pre-baseline database reaches this point with its own `categories`
    # table, which does not gain exclude_from_stats until migration 2. Seed
    # only the columns that exist right now; migration 2 backfills the rest.
    if column_exists(cursor, "categories", "exclude_from_stats"):
        cursor.executemany(
            "INSERT INTO categories (name, color, icon, is_default, exclude_from_stats)"
            " VALUES (?, ?, ?, 1, ?)",
            [
                (c["name"], c["color"], c["icon"], c["exclude_from_stats"])
                for c in DEFAULT_CATEGORIES
            ],
        )
    else:
        cursor.executemany(
            "INSERT INTO categories (name, color, icon, is_default) VALUES (?, ?, ?, 1)",
            [(c["name"], c["color"], c["icon"]) for c in DEFAULT_CATEGORIES],
        )


def _categories_exclude_from_stats(cursor: sqlite3.Cursor) -> None:
    """Add categories.exclude_from_stats and the Inter-account category."""
    add_column_if_missing(
        cursor, "categories", "exclude_from_stats", "BOOLEAN DEFAULT 0"
    )

    cursor.execute("SELECT COUNT(*) FROM categories WHERE name = ?", ("Inter-account",))
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO categories (name, color, icon, is_default, exclude_from_stats)"
            " VALUES (?, ?, ?, 1, 1)",
            ("Inter-account", "#14b8a6", "arrow-left-right"),
        )
    else:
        # The row may have been seeded by the baseline against a table that did
        # not yet have the column, which defaults it to 0. Inter-account
        # transfers must never count towards spending statistics.
        cursor.execute(
            "UPDATE categories SET exclude_from_stats = 1 WHERE name = ?",
            ("Inter-account",),
        )


def _cleanup_orphaned_category_rows(cursor: sqlite3.Cursor) -> None:
    """Remove category links orphaned by deletes made before foreign key
    enforcement was enabled, when ON DELETE CASCADE never fired."""
    for table in ("transaction_categories", "category_keywords"):
        cursor.execute(
            f"DELETE FROM {table} WHERE categoryId NOT IN (SELECT id FROM categories)"
        )


def _transaction_date_iso_separator(cursor: sqlite3.Cursor) -> None:
    """Normalize transactionDate to ISO 8601 T-separated strings.

    Rows written through sqlite3's deprecated datetime adapter used a space
    separator; lexicographic date comparisons need a single format.
    """
    cursor.execute(
        "UPDATE transactions SET transactionDate = replace(transactionDate, ' ', 'T')"
        " WHERE transactionDate LIKE '% %'"
    )


def _sync_operations_warnings(cursor: sqlite3.Cursor) -> None:
    """Add the warnings column to sync_operations."""
    add_column_if_missing(cursor, "sync_operations", "warnings", "TEXT")


@dataclass(frozen=True)
class Migration:
    """One schema change, applied inside its own transaction."""

    version: int
    name: str
    apply: Callable[[sqlite3.Cursor], None]


# Ordered by the date each change was introduced.
MIGRATIONS: tuple[Migration, ...] = (
    Migration(1, "baseline_schema", _baseline_schema),
    Migration(2, "categories_exclude_from_stats", _categories_exclude_from_stats),
    Migration(3, "cleanup_orphaned_category_rows", _cleanup_orphaned_category_rows),
    Migration(4, "transaction_date_iso_separator", _transaction_date_iso_separator),
    Migration(5, "sync_operations_warnings", _sync_operations_warnings),
)

LATEST_VERSION = len(MIGRATIONS)

# Guard against a mis-numbered or duplicated entry silently skipping a step.
assert [m.version for m in MIGRATIONS] == list(range(1, LATEST_VERSION + 1)), (
    "migration versions must be contiguous starting at 1"
)
assert len({m.name for m in MIGRATIONS}) == LATEST_VERSION, (
    "migration names must be unique"
)
