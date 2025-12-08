import json
import sqlite3
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from leggen.repositories.base_repository import BaseRepository


class TransactionRepository(BaseRepository):
    """Repository for transaction data operations"""

    def create_table(self):
        """Create transactions table with indexes"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
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
            )"""
            )

            # Create indexes for better performance
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_transactions_internal_id
                   ON transactions(internalTransactionId)"""
            )
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

    def persist(
        self, account_id: str, transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Persist transactions to database, return new ones"""
        try:
            self.create_table()

            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                insert_sql = """INSERT OR REPLACE INTO transactions (
                    accountId,
                    transactionId,
                    internalTransactionId,
                    institutionId,
                    iban,
                    transactionDate,
                    description,
                    transactionValue,
                    transactionCurrency,
                    transactionStatus,
                    rawTransaction
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

                new_transactions = []

                for transaction in transactions:
                    try:
                        # Check if transaction already exists
                        cursor.execute(
                            """SELECT COUNT(*) FROM transactions
                               WHERE accountId = ? AND transactionId = ?""",
                            (transaction["accountId"], transaction["transactionId"]),
                        )
                        exists = cursor.fetchone()[0] > 0

                        cursor.execute(
                            insert_sql,
                            (
                                transaction["accountId"],
                                transaction["transactionId"],
                                transaction.get("internalTransactionId"),
                                transaction["institutionId"],
                                transaction["iban"],
                                transaction["transactionDate"],
                                transaction["description"],
                                transaction["transactionValue"],
                                transaction["transactionCurrency"],
                                transaction["transactionStatus"],
                                json.dumps(transaction["rawTransaction"]),
                            ),
                        )

                        if not exists:
                            new_transactions.append(transaction)

                    except sqlite3.IntegrityError as e:
                        logger.warning(
                            f"Failed to insert transaction {transaction.get('transactionId')}: {e}"
                        )
                        continue

                conn.commit()

            logger.info(
                f"Persisted {len(new_transactions)} new transactions for account {account_id}"
            )
            return new_transactions
        except Exception as e:
            logger.error(f"Failed to persist transactions: {e}")
            raise

    def get_transactions(
        self,
        account_id: Optional[str] = None,
        limit: Optional[int] = 100,
        offset: int = 0,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get transactions with optional filtering"""
        if not self._db_exists():
            return []

        with self._get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM transactions WHERE 1=1"
            params: List[Union[str, int, float]] = []

            if account_id:
                query += " AND accountId = ?"
                params.append(account_id)

            if date_from:
                query += " AND transactionDate >= ?"
                params.append(date_from)

            if date_to:
                query += " AND transactionDate <= ?"
                params.append(date_to)

            if min_amount is not None:
                query += " AND transactionValue >= ?"
                params.append(min_amount)

            if max_amount is not None:
                query += " AND transactionValue <= ?"
                params.append(max_amount)

            if search:
                query += " AND description LIKE ?"
                params.append(f"%{search}%")

            query += " ORDER BY transactionDate DESC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            if offset:
                query += " OFFSET ?"
                params.append(offset)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            transactions = []
            for row in rows:
                transaction = dict(row)
                if transaction["rawTransaction"]:
                    transaction["rawTransaction"] = json.loads(
                        transaction["rawTransaction"]
                    )
                transactions.append(transaction)

            return transactions

    def get_count(
        self,
        account_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        search: Optional[str] = None,
    ) -> int:
        """Get total count of transactions matching filters"""
        if not self._db_exists():
            return 0

        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT COUNT(*) FROM transactions WHERE 1=1"
            params: List[Union[str, float]] = []

            if account_id:
                query += " AND accountId = ?"
                params.append(account_id)

            if date_from:
                query += " AND transactionDate >= ?"
                params.append(date_from)

            if date_to:
                query += " AND transactionDate <= ?"
                params.append(date_to)

            if min_amount is not None:
                query += " AND transactionValue >= ?"
                params.append(min_amount)

            if max_amount is not None:
                query += " AND transactionValue <= ?"
                params.append(max_amount)

            if search:
                query += " AND description LIKE ?"
                params.append(f"%{search}%")

            cursor.execute(query, params)
            return cursor.fetchone()[0]

    def get_account_summary(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get basic account info from transactions table"""
        if not self._db_exists():
            return None

        with self._get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT DISTINCT accountId, institutionId, iban
                FROM transactions
                WHERE accountId = ?
                ORDER BY transactionDate DESC
                LIMIT 1
            """,
                (account_id,),
            )

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
