import sqlite3
from typing import Any, Dict, List, Optional

from loguru import logger

from leggen.repositories.base_repository import BaseRepository


class BalanceRepository(BaseRepository):
    """Repository for balance data operations"""

    def create_table(self):
        """Create balances table with indexes"""
        with self._get_db_connection() as conn:
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

    def persist(self, account_id: str, balance_rows: List[tuple]) -> None:
        """Persist balance rows to database"""
        try:
            self.create_table()

            with self._get_db_connection() as conn:
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

    def get_balances(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get latest balances from database"""
        if not self._db_exists():
            return []

        with self._get_db_connection(row_factory=True) as conn:
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
