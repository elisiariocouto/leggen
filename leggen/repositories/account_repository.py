import sqlite3
from typing import Any, Dict, List, Optional

from leggen.repositories.db import db_exists, get_db_connection


class AccountRepository:
    """Repository for account data operations"""

    def create_table(self):
        """Create accounts table with indexes"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
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
            )"""
            )

            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_accounts_institution_id
                   ON accounts(institution_id)"""
            )
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_accounts_status
                   ON accounts(status)"""
            )

            conn.commit()

    def persist(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Persist account details to database"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if account exists and preserve display_name
            cursor.execute(
                "SELECT display_name FROM accounts WHERE id = ?",
                (account_data["id"],),
            )
            existing_row = cursor.fetchone()
            existing_display_name = existing_row[0] if existing_row else None

            # Use existing display_name if not provided in account_data
            display_name = account_data.get("display_name", existing_display_name)

            cursor.execute(
                """INSERT OR REPLACE INTO accounts (
                id,
                institution_id,
                status,
                iban,
                name,
                currency,
                created,
                last_accessed,
                last_updated,
                display_name,
                logo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    account_data["id"],
                    account_data["institution_id"],
                    account_data["status"],
                    account_data.get("iban"),
                    account_data.get("name"),
                    account_data.get("currency"),
                    account_data["created"],
                    account_data.get("last_accessed"),
                    account_data.get("last_updated", account_data["created"]),
                    display_name,
                    account_data.get("logo"),
                ),
            )
            conn.commit()

        return account_data

    def get_accounts(
        self,
        account_ids: Optional[List[str]] = None,
        include_deleted: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get account details from database"""
        if not db_exists():
            return []

        try:
            with get_db_connection(row_factory=True) as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM accounts"
                params: list = []
                conditions = []

                if account_ids:
                    placeholders = ",".join("?" * len(account_ids))
                    conditions.append(f"id IN ({placeholders})")
                    params.extend(account_ids)

                if not include_deleted:
                    conditions.append("status != 'DELETED'")

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

                query += " ORDER BY created DESC"

                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [dict(row) for row in rows]
        except sqlite3.OperationalError:
            return []

    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get specific account details from database"""
        if not db_exists():
            return None

        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def delete_account(self, account_id: str, delete_data: bool = True) -> bool:
        """Soft-delete an account and optionally delete its associated data.

        Sets the account status to 'DELETED' instead of removing the row,
        so account metadata remains available for display purposes.

        Returns True if the account existed and was soft-deleted.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if account exists
            cursor.execute("SELECT id FROM accounts WHERE id = ?", (account_id,))
            if not cursor.fetchone():
                return False

            if delete_data:
                cursor.execute(
                    "DELETE FROM transactions WHERE accountId = ?", (account_id,)
                )
                cursor.execute(
                    "DELETE FROM balances WHERE account_id = ?", (account_id,)
                )

            cursor.execute(
                "UPDATE accounts SET status = 'DELETED' WHERE id = ?", (account_id,)
            )
            conn.commit()
            return True
