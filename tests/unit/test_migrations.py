"""Tests for the versioned schema migration runner."""

import sqlite3
from pathlib import Path
from typing import Any

import pytest

import leggen.repositories.migrations as migrations_pkg
from leggen.errors import UnsupportedDatabaseVersionError
from leggen.repositories.migrations import (
    LATEST_VERSION,
    MIGRATIONS,
    run_migrations,
)
from leggen.repositories.migrations._helpers import (
    add_column_if_missing,
    column_exists,
    table_exists,
)
from leggen.repositories.migrations._steps import Migration

# The schema as shipped in 2025.9.22, the oldest release that can be upgraded:
# everything the baseline creates except `categories.exclude_from_stats` and
# `sync_operations.warnings`, which later migrations add.
_LEGACY_SCHEMA = (
    """CREATE TABLE accounts (
        id TEXT PRIMARY KEY, institution_id TEXT, status TEXT, iban TEXT, name TEXT,
        currency TEXT, created DATETIME, last_accessed DATETIME, last_updated DATETIME,
        display_name TEXT, logo TEXT
    )""",
    """CREATE TABLE balances (
        id INTEGER PRIMARY KEY AUTOINCREMENT, account_id TEXT, bank TEXT, status TEXT,
        iban TEXT, amount REAL, currency TEXT, type TEXT, timestamp DATETIME
    )""",
    """CREATE TABLE transactions (
        accountId TEXT NOT NULL, transactionId TEXT NOT NULL, internalTransactionId TEXT,
        institutionId TEXT, iban TEXT, transactionDate DATETIME, description TEXT,
        transactionValue REAL, transactionCurrency TEXT, transactionStatus TEXT,
        rawTransaction JSON, PRIMARY KEY (accountId, transactionId)
    )""",
    """CREATE TABLE sync_operations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, started_at DATETIME NOT NULL,
        completed_at DATETIME, success BOOLEAN, accounts_processed INTEGER DEFAULT 0,
        transactions_added INTEGER DEFAULT 0, transactions_updated INTEGER DEFAULT 0,
        balances_updated INTEGER DEFAULT 0, duration_seconds REAL, errors TEXT,
        logs TEXT, trigger_type TEXT DEFAULT 'manual'
    )""",
    """CREATE TABLE sessions (
        session_id TEXT PRIMARY KEY, aspsp_name TEXT NOT NULL, aspsp_country TEXT NOT NULL,
        accounts JSON, valid_until DATETIME, created_at DATETIME, status TEXT DEFAULT 'active'
    )""",
    """CREATE TABLE expiry_notifications (
        session_id TEXT NOT NULL, threshold INTEGER NOT NULL, sent_at DATETIME NOT NULL,
        PRIMARY KEY (session_id, threshold)
    )""",
    """CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,
        color TEXT DEFAULT '#6b7280', icon TEXT, is_default BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE transaction_categories (
        accountId TEXT NOT NULL, transactionId TEXT NOT NULL, categoryId INTEGER NOT NULL,
        assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (accountId, transactionId),
        FOREIGN KEY (categoryId) REFERENCES categories(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE category_keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT, keyword TEXT NOT NULL, categoryId INTEGER NOT NULL,
        frequency INTEGER DEFAULT 1, UNIQUE(keyword, categoryId),
        FOREIGN KEY (categoryId) REFERENCES categories(id) ON DELETE CASCADE
    )""",
    "CREATE INDEX idx_accounts_institution_id ON accounts(institution_id)",
    "CREATE INDEX idx_accounts_status ON accounts(status)",
    "CREATE INDEX idx_balances_account_id ON balances(account_id)",
    "CREATE INDEX idx_balances_timestamp ON balances(timestamp)",
    "CREATE INDEX idx_balances_account_type_timestamp ON balances(account_id, type, timestamp)",
    "CREATE INDEX idx_transactions_date ON transactions(transactionDate)",
    "CREATE INDEX idx_transactions_account_date ON transactions(accountId, transactionDate)",
    "CREATE INDEX idx_transactions_amount ON transactions(transactionValue)",
    "CREATE INDEX idx_transactions_description ON transactions(description)",
    "CREATE INDEX idx_sync_operations_started_at ON sync_operations(started_at)",
    "CREATE INDEX idx_sync_operations_success ON sync_operations(success)",
    "CREATE INDEX idx_sync_operations_trigger_type ON sync_operations(trigger_type)",
    "CREATE INDEX idx_tc_category ON transaction_categories(categoryId)",
    "CREATE INDEX idx_ck_keyword ON category_keywords(keyword)",
    "CREATE INDEX idx_ck_category ON category_keywords(categoryId)",
)


def _build_legacy_db(path: Path) -> None:
    """Create a 2025.9.22-era database."""
    conn = sqlite3.connect(path)
    for statement in _LEGACY_SCHEMA:
        conn.execute(statement)
    conn.commit()
    conn.close()


def _schema_snapshot(path: Path) -> dict[str, Any]:
    """Describe the schema by meaning rather than by stored SQL text.

    Raw `sqlite_master.sql` cannot be compared directly: ALTER TABLE appends
    columns (so order differs from a freshly created table) and RENAME TO
    quotes the table name. Both are cosmetic, since every query addresses
    columns by name.
    """
    conn = sqlite3.connect(path)
    try:
        snapshot: dict[str, Any] = {}
        tables = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master"
                " WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        for table in tables:
            columns = {
                row[1]: (row[2].upper(), row[3], row[4], row[5])
                for row in conn.execute(f"PRAGMA table_info({table})")
            }
            indexes = {}
            for row in conn.execute(f"PRAGMA index_list({table})"):
                name, unique, origin = row[1], row[2], row[3]
                cols = tuple(r[2] for r in conn.execute(f"PRAGMA index_info({name})"))
                # Auto-generated index names vary; key those by their columns.
                key = name if origin == "c" else f"<{origin}>{cols}"
                indexes[key] = (cols, unique)
            snapshot[table] = {
                "columns": columns,
                "indexes": indexes,
                "foreign_keys": sorted(
                    (r[2], r[3], r[4], r[6])
                    for r in conn.execute(f"PRAGMA foreign_key_list({table})")
                ),
            }
        return snapshot
    finally:
        conn.close()


def _user_version(path: Path) -> int:
    conn = sqlite3.connect(path)
    try:
        return int(conn.execute("PRAGMA user_version").fetchone()[0])
    finally:
        conn.close()


class TestMigrationList:
    """The list itself must stay well-formed."""

    def test_versions_are_contiguous_from_one(self):
        assert [m.version for m in MIGRATIONS] == list(range(1, LATEST_VERSION + 1))

    def test_names_are_unique(self):
        assert len({m.name for m in MIGRATIONS}) == LATEST_VERSION

    def test_baseline_is_first(self):
        assert MIGRATIONS[0].name == "baseline_schema"


class TestFreshDatabase:
    def test_creates_every_table_and_stamps_version(self, tmp_path):
        db = tmp_path / "fresh.db"

        assert run_migrations(db) == LATEST_VERSION
        assert _user_version(db) == LATEST_VERSION

        assert set(_schema_snapshot(db)) == {
            "accounts",
            "balances",
            "transactions",
            "sync_operations",
            "sessions",
            "expiry_notifications",
            "categories",
            "transaction_categories",
            "category_keywords",
        }

    def test_seeds_default_categories_once(self, tmp_path):
        db = tmp_path / "fresh.db"
        run_migrations(db)

        conn = sqlite3.connect(db)
        try:
            assert conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 13
            # The Inter-account category is both seeded by the baseline and
            # inserted by migration 2; it must not be duplicated.
            assert (
                conn.execute(
                    "SELECT COUNT(*) FROM categories WHERE name = 'Inter-account'"
                ).fetchone()[0]
                == 1
            )
            assert (
                conn.execute(
                    "SELECT exclude_from_stats FROM categories WHERE name = 'Inter-account'"
                ).fetchone()[0]
                == 1
            )
        finally:
            conn.close()

    def test_creates_parent_directory(self, tmp_path):
        db = tmp_path / "nested" / "dir" / "leggen.db"
        assert run_migrations(db) == LATEST_VERSION
        assert db.exists()

    def test_is_idempotent(self, tmp_path):
        db = tmp_path / "fresh.db"
        run_migrations(db)
        before = _schema_snapshot(db)

        assert run_migrations(db) == LATEST_VERSION
        assert _schema_snapshot(db) == before


class TestLegacyDatabase:
    def test_converges_to_the_fresh_schema(self, tmp_path):
        """A migrated 2025.9.22 database must match a new install exactly."""
        fresh = tmp_path / "fresh.db"
        legacy = tmp_path / "legacy.db"

        run_migrations(fresh)
        _build_legacy_db(legacy)
        run_migrations(legacy)

        assert _schema_snapshot(legacy) == _schema_snapshot(fresh)
        assert _user_version(legacy) == _user_version(fresh) == LATEST_VERSION

    def test_adds_the_missing_columns(self, tmp_path):
        db = tmp_path / "legacy.db"
        _build_legacy_db(db)
        run_migrations(db)

        conn = sqlite3.connect(db)
        try:
            cursor = conn.cursor()
            assert column_exists(cursor, "categories", "exclude_from_stats")
            assert column_exists(cursor, "sync_operations", "warnings")
        finally:
            conn.close()

    def test_normalizes_space_separated_dates(self, tmp_path):
        db = tmp_path / "legacy.db"
        _build_legacy_db(db)
        conn = sqlite3.connect(db)
        conn.execute(
            "INSERT INTO transactions (accountId, transactionId, transactionDate)"
            " VALUES ('acc', 'tx-space', '2024-01-01 10:00:00')"
        )
        conn.execute(
            "INSERT INTO transactions (accountId, transactionId, transactionDate)"
            " VALUES ('acc', 'tx-iso', '2024-01-02T10:00:00')"
        )
        conn.commit()
        conn.close()

        run_migrations(db)

        conn = sqlite3.connect(db)
        try:
            dates = [
                row[0]
                for row in conn.execute(
                    "SELECT transactionDate FROM transactions ORDER BY transactionId"
                )
            ]
        finally:
            conn.close()
        assert dates == ["2024-01-02T10:00:00", "2024-01-01T10:00:00"]

    def test_removes_orphaned_category_links(self, tmp_path):
        db = tmp_path / "legacy.db"
        _build_legacy_db(db)
        conn = sqlite3.connect(db)
        conn.execute("INSERT INTO categories (id, name) VALUES (1, 'Kept')")
        conn.execute(
            "INSERT INTO transaction_categories (accountId, transactionId, categoryId)"
            " VALUES ('acc', 'kept', 1)"
        )
        # Written before foreign keys were enforced, so the cascade never fired.
        conn.execute(
            "INSERT INTO transaction_categories (accountId, transactionId, categoryId)"
            " VALUES ('acc', 'orphan', 999)"
        )
        conn.execute(
            "INSERT INTO category_keywords (keyword, categoryId) VALUES ('orphan', 999)"
        )
        conn.commit()
        conn.close()

        run_migrations(db)

        conn = sqlite3.connect(db)
        try:
            assert [
                row[0]
                for row in conn.execute(
                    "SELECT transactionId FROM transaction_categories"
                )
            ] == ["kept"]
            assert (
                conn.execute("SELECT COUNT(*) FROM category_keywords").fetchone()[0]
                == 0
            )
        finally:
            conn.close()

    def test_preserves_existing_rows(self, tmp_path):
        db = tmp_path / "legacy.db"
        _build_legacy_db(db)
        conn = sqlite3.connect(db)
        conn.execute("INSERT INTO accounts (id, name) VALUES ('acc-1', 'Checking')")
        conn.execute(
            "INSERT INTO transactions (accountId, transactionId, transactionValue)"
            " VALUES ('acc-1', 'tx-1', 42.5)"
        )
        conn.commit()
        conn.close()

        run_migrations(db)

        conn = sqlite3.connect(db)
        try:
            assert conn.execute("SELECT name FROM accounts").fetchone()[0] == "Checking"
            assert (
                conn.execute("SELECT transactionValue FROM transactions").fetchone()[0]
                == 42.5
            )
        finally:
            conn.close()

    def test_inter_account_is_excluded_when_seeded_before_the_column_existed(
        self, tmp_path
    ):
        """An empty legacy categories table is seeded by the baseline without
        exclude_from_stats; migration 2 must still flag Inter-account."""
        db = tmp_path / "legacy.db"
        _build_legacy_db(db)

        run_migrations(db)

        conn = sqlite3.connect(db)
        try:
            assert conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 13
            excluded = conn.execute(
                "SELECT name FROM categories WHERE exclude_from_stats = 1"
            ).fetchall()
            assert excluded == [("Inter-account",)]
        finally:
            conn.close()

    def test_does_not_duplicate_an_existing_inter_account_category(self, tmp_path):
        db = tmp_path / "legacy.db"
        _build_legacy_db(db)
        conn = sqlite3.connect(db)
        conn.execute("INSERT INTO categories (name) VALUES ('Inter-account')")
        conn.commit()
        conn.close()

        run_migrations(db)

        conn = sqlite3.connect(db)
        try:
            assert (
                conn.execute(
                    "SELECT COUNT(*) FROM categories WHERE name = 'Inter-account'"
                ).fetchone()[0]
                == 1
            )
        finally:
            conn.close()


class TestPreBaselineDatabase:
    """Databases older than 2025.9.22 must be refused, not silently broken."""

    def test_rejects_a_pre_composite_key_database(self, tmp_path):
        db = tmp_path / "ancient.db"
        conn = sqlite3.connect(db)
        conn.execute(
            "CREATE TABLE transactions ("
            " internalTransactionId TEXT PRIMARY KEY, accountId TEXT, rawTransaction JSON)"
        )
        conn.commit()
        conn.close()

        with pytest.raises(UnsupportedDatabaseVersionError) as excinfo:
            run_migrations(db)
        assert "2025.9.22" in str(excinfo.value)

    def test_leaves_the_rejected_database_untouched(self, tmp_path):
        db = tmp_path / "ancient.db"
        conn = sqlite3.connect(db)
        conn.execute(
            "CREATE TABLE transactions ("
            " internalTransactionId TEXT PRIMARY KEY, accountId TEXT)"
        )
        conn.commit()
        conn.close()
        before = _schema_snapshot(db)

        with pytest.raises(UnsupportedDatabaseVersionError):
            run_migrations(db)

        assert _schema_snapshot(db) == before
        assert _user_version(db) == 0

    def test_fresh_database_is_not_mistaken_for_pre_baseline(self, tmp_path):
        """An empty file has no transactions table; it must migrate normally."""
        assert run_migrations(tmp_path / "empty.db") == LATEST_VERSION


class TestAtomicity:
    def test_a_failing_migration_rolls_back_and_keeps_the_version(
        self, tmp_path, monkeypatch
    ):
        db = tmp_path / "fresh.db"
        run_migrations(db)
        before = _schema_snapshot(db)

        def explode(cursor):
            cursor.execute("ALTER TABLE accounts ADD COLUMN doomed TEXT")
            raise RuntimeError("boom")

        broken = Migration(LATEST_VERSION + 1, "explodes", explode)
        monkeypatch.setattr(
            migrations_pkg, "MIGRATIONS", (*MIGRATIONS, broken), raising=True
        )

        with pytest.raises(RuntimeError, match="boom"):
            run_migrations(db)

        # The half-applied ALTER is gone and the stamp never advanced.
        assert _schema_snapshot(db) == before
        assert _user_version(db) == LATEST_VERSION


class TestNewerDatabase:
    def test_a_newer_schema_is_left_alone(self, tmp_path):
        db = tmp_path / "future.db"
        run_migrations(db)
        conn = sqlite3.connect(db)
        conn.execute(f"PRAGMA user_version = {LATEST_VERSION + 5}")
        conn.commit()
        conn.close()

        assert run_migrations(db) == LATEST_VERSION + 5


class TestHelpers:
    def test_table_and_column_existence(self, tmp_path):
        db = tmp_path / "fresh.db"
        run_migrations(db)
        conn = sqlite3.connect(db)
        try:
            cursor = conn.cursor()
            assert table_exists(cursor, "accounts")
            assert not table_exists(cursor, "nope")
            assert column_exists(cursor, "accounts", "display_name")
            assert not column_exists(cursor, "accounts", "nope")
            assert not column_exists(cursor, "nope", "whatever")
        finally:
            conn.close()

    def test_add_column_if_missing_is_idempotent(self, tmp_path):
        db = tmp_path / "fresh.db"
        run_migrations(db)
        conn = sqlite3.connect(db)
        try:
            cursor = conn.cursor()
            assert add_column_if_missing(cursor, "accounts", "extra", "TEXT") is True
            assert add_column_if_missing(cursor, "accounts", "extra", "TEXT") is False
            # A missing table is a no-op rather than an error.
            assert add_column_if_missing(cursor, "nope", "extra", "TEXT") is False
        finally:
            conn.close()
