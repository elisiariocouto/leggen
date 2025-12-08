from typing import Any, Dict, List, Optional

from leggen.repositories.base_repository import BaseRepository


class AccountRepository(BaseRepository):
    """Repository for account data operations"""

    def create_table(self):
        """Create accounts table with indexes"""
        with self._get_db_connection() as conn:
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
        self.create_table()

        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if account exists and preserve display_name
            cursor.execute(
                "SELECT display_name FROM accounts WHERE id = ?", (account_data["id"],)
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
        self, account_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get account details from database"""
        if not self._db_exists():
            return []

        with self._get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM accounts"
            params = []

            if account_ids:
                placeholders = ",".join("?" * len(account_ids))
                query += f" WHERE id IN ({placeholders})"
                params.extend(account_ids)

            query += " ORDER BY created DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get specific account details from database"""
        if not self._db_exists():
            return None

        with self._get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None
