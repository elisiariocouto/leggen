"""Tests for the balance repository and its unique-constraint migration."""

import pytest

from leggen.repositories import BalanceRepository
from leggen.repositories.db import create_connection, get_db_connection
from leggen.repositories.migration_repository import MigrationRepository
from leggen.utils.paths import path_manager


def _balance_row(timestamp="2026-07-01T10:00:00", type_="closingBooked", amount=100.0):
    # Matches BalanceRepository.persist's column order.
    return ("IBAN1", "Test Bank", "READY", "IBAN1", amount, "EUR", type_, timestamp)


@pytest.mark.unit
class TestBalanceRepositoryPersist:
    """The UNIQUE(account_id, type, timestamp) constraint makes the dedup in
    persist() live rather than dead code."""

    def test_duplicate_balance_is_skipped(self, mock_db_path):
        repo = BalanceRepository()

        repo.persist("IBAN1", [_balance_row(amount=100.0)])
        # Same account_id/type/timestamp, different amount — must not duplicate.
        repo.persist("IBAN1", [_balance_row(amount=250.0)])

        with get_db_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM balances").fetchone()[0]
        assert count == 1

    def test_distinct_timestamps_are_kept(self, mock_db_path):
        repo = BalanceRepository()

        repo.persist("IBAN1", [_balance_row(timestamp="2026-07-01T10:00:00")])
        repo.persist("IBAN1", [_balance_row(timestamp="2026-07-02T10:00:00")])

        with get_db_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM balances").fetchone()[0]
        assert count == 2


@pytest.fixture
def legacy_balances_db(temp_db_path):
    """A database whose balances table predates the unique constraint."""
    original = path_manager._database_path
    path_manager.set_database_path(temp_db_path)

    conn = create_connection(temp_db_path)
    conn.execute(
        """CREATE TABLE balances (
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
    conn.commit()
    conn.close()

    try:
        yield temp_db_path
    finally:
        path_manager._database_path = original


def _insert_legacy_balance(db_path, amount, timestamp="2026-07-01T10:00:00"):
    conn = create_connection(db_path)
    conn.execute(
        """INSERT INTO balances
            (account_id, bank, status, iban, amount, currency, type, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "IBAN1",
            "Test Bank",
            "READY",
            "IBAN1",
            amount,
            "EUR",
            "closingBooked",
            timestamp,
        ),
    )
    conn.commit()
    conn.close()


@pytest.mark.unit
class TestBalancesUniqueMigration:
    """The migration collapses accumulated duplicates and adds the constraint."""

    async def test_migration_dedups_and_adds_constraint(self, legacy_balances_db):
        # Two rows share (account_id, type, timestamp) — legacy append growth.
        _insert_legacy_balance(legacy_balances_db, amount=100.0)
        _insert_legacy_balance(legacy_balances_db, amount=250.0)
        _insert_legacy_balance(
            legacy_balances_db, amount=300.0, timestamp="2026-07-02T10:00:00"
        )

        repo = MigrationRepository()
        assert await repo._check_balances_unique_migration_needed() is True

        await repo.migrate_balances_unique_constraint_if_needed()

        conn = create_connection(legacy_balances_db)
        count = conn.execute("SELECT COUNT(*) FROM balances").fetchone()[0]
        # The most recent row (highest id) wins for the duplicated group.
        kept_amount = conn.execute(
            "SELECT amount FROM balances WHERE timestamp = '2026-07-01T10:00:00'"
        ).fetchone()[0]
        conn.close()

        assert count == 2
        assert kept_amount == 250.0

        # Migration is a no-op once the constraint exists.
        assert await repo._check_balances_unique_migration_needed() is False

    async def test_migration_skipped_when_constraint_present(self, mock_db_path):
        """ensure_tables() already builds the constrained schema."""
        repo = MigrationRepository()
        assert await repo._check_balances_unique_migration_needed() is False
