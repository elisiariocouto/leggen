import sqlite3
from typing import Any

from loguru import logger

from leggen.repositories.db import db_exists, get_db_connection


class BalanceRepository:
    """Repository for balance data operations"""

    def create_table(self):
        """Create balances table with indexes"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

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

            conn.commit()

    def persist(self, account_id: str, balance_rows: list[tuple]) -> None:
        """Persist balance rows to database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                for row in balance_rows:
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
                            row,
                        )
                    except sqlite3.IntegrityError:
                        logger.warning(f"Skipped duplicate balance for {account_id}")

                conn.commit()

            logger.info(f"Persisted balances for account {account_id}")
        except Exception as e:
            logger.error(f"Failed to persist balances: {e}")
            raise

    def get_latest_balances_by_account(self) -> dict[str, list[dict[str, Any]]]:
        """Latest balances for every account in one query, grouped by account.

        Rows with a NULL amount (possible on legacy data — the column is
        nullable) are skipped: a balance without an amount is meaningless.
        """
        grouped: dict[str, list[dict[str, Any]]] = {}
        for balance in self.get_balances():
            if balance.get("amount") is None:
                logger.warning(
                    f"Skipping balance with NULL amount for {balance.get('account_id')}"
                )
                continue
            grouped.setdefault(balance["account_id"], []).append(balance)
        return grouped

    def get_net_worth_series(
        self,
        date_from: str,
        date_to: str,
        account_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Recorded balance snapshots per day, one row per account identity.

        Balances are appended on every sync, so this reads real history rather
        than reconstructing it from transactions. Two details matter:

        - Several syncs can land on one day; only the last per day is kept.
        - An account's `account_id` can change (this codebase has seen a
          migration from provider UUIDs to IBANs). Grouping on the IBAN keeps
          one real-world account as one series across that change; accounts
          without an IBAN fall back to their id.
        """
        if not db_exists():
            return []

        try:
            with get_db_connection(row_factory=True) as conn:
                cursor = conn.cursor()

                # closingBooked/CLBD is the account's settled position;
                # interimAvailable/ITAV is the fallback when a bank omits it.
                # Other types (e.g. authorised) would double-count.
                query = """
                    WITH ranked AS (
                        SELECT
                            COALESCE(NULLIF(b.iban, 'N/A'), b.account_id) AS series_key,
                            b.account_id,
                            b.amount,
                            b.currency,
                            date(b.timestamp) AS day,
                            ROW_NUMBER() OVER (
                                PARTITION BY COALESCE(NULLIF(b.iban, 'N/A'), b.account_id),
                                             date(b.timestamp)
                                ORDER BY
                                    CASE b.type
                                        WHEN 'closingBooked' THEN 1
                                        WHEN 'CLBD' THEN 2
                                        WHEN 'interimAvailable' THEN 3
                                        WHEN 'ITAV' THEN 4
                                    END,
                                    b.timestamp DESC
                            ) AS rn
                        FROM balances b
                        WHERE b.amount IS NOT NULL
                          AND b.type IN ('closingBooked', 'CLBD', 'interimAvailable', 'ITAV')
                          AND date(b.timestamp) >= date(?)
                          AND date(b.timestamp) <= date(?)
                """
                params: list[Any] = [date_from, date_to]

                if account_id:
                    query += " AND b.account_id = ?"
                    params.append(account_id)

                query += """
                    )
                    SELECT series_key, account_id, amount, currency, day
                    FROM ranked
                    WHERE rn = 1
                    ORDER BY day ASC, series_key ASC
                """

                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            return []

    def get_balances(self, account_id: str | None = None) -> list[dict[str, Any]]:
        """Get latest balances from database"""
        if not db_exists():
            return []

        try:
            with get_db_connection(row_factory=True) as conn:
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

                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [dict(row) for row in rows]
        except sqlite3.OperationalError:
            return []
