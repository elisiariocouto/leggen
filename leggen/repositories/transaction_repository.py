import json
import sqlite3
from typing import Any

from loguru import logger

from leggen.repositories.db import db_exists, get_db_connection

# SQLite's default parameter limit is 999; keep IN() chunks safely under it.
_SELECT_CHUNK_SIZE = 900

# Shared JOIN fragment: category lookups hang off (accountId, transactionId).
_CATEGORY_JOIN = """
                LEFT JOIN transaction_categories tc ON t.accountId = tc.accountId AND t.transactionId = tc.transactionId
                LEFT JOIN categories c ON tc.categoryId = c.id"""


class TransactionRepository:
    """Repository for transaction data operations"""

    def _build_filter_clause(
        self,
        account_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        search: str | None = None,
        category_id: str | None = None,
    ) -> tuple[str, list[str | int | float]]:
        """Build WHERE clause and params for transaction filtering."""
        clause = ""
        params: list[str | int | float] = []

        if account_id:
            clause += " AND t.accountId = ?"
            params.append(account_id)

        if date_from:
            clause += " AND t.transactionDate >= ?"
            params.append(date_from)

        if date_to:
            # transactionDate carries a time component, so an inclusive end
            # date means "anything before the start of the following day"
            clause += " AND t.transactionDate < date(?, '+1 day')"
            params.append(date_to)

        if min_amount is not None:
            clause += " AND t.transactionValue >= ?"
            params.append(min_amount)

        if max_amount is not None:
            clause += " AND t.transactionValue <= ?"
            params.append(max_amount)

        if search:
            clause += " AND t.description LIKE ?"
            params.append(f"%{search}%")

        if category_id:
            if category_id == "uncategorized":
                clause += " AND tc.categoryId IS NULL"
            else:
                clause += " AND tc.categoryId = ?"
                params.append(int(category_id))

        return clause, params

    def create_table(self):
        """Create transactions table with indexes"""
        with get_db_connection() as conn:
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
        self, account_id: str, transactions: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], int]:
        """Persist transactions to database.

        Returns (new_transactions, updated_count). Rows that already exist
        with identical content are left untouched and counted in neither.
        """
        # Every row must belong to the account being persisted — a mismatch
        # would write under another account's primary key while this method
        # logs success for account_id.
        mismatched = {txn["accountId"] for txn in transactions} - {account_id}
        if mismatched:
            raise ValueError(
                f"persist() called for account {account_id} with transactions "
                f"belonging to {sorted(mismatched)}"
            )

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Load only the batch's existing rows (chunked, deduplicated
                # IN() to stay under SQLite's parameter limit) and compare in
                # memory. An unconstrained account SELECT would read the
                # whole history — including rawTransaction blobs — on every
                # incremental sync.
                existing_rows: dict[tuple[str, str], tuple] = {}
                txn_ids = list(
                    dict.fromkeys(txn["transactionId"] for txn in transactions)
                )
                for start in range(0, len(txn_ids), _SELECT_CHUNK_SIZE):
                    chunk = txn_ids[start : start + _SELECT_CHUNK_SIZE]
                    placeholders = ",".join("?" * len(chunk))
                    cursor.execute(
                        f"""SELECT
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
                        FROM transactions
                        WHERE accountId = ? AND transactionId IN ({placeholders})""",
                        (account_id, *chunk),
                    )
                    for row in cursor.fetchall():
                        existing_rows[(row[0], row[1])] = tuple(row[2:])

                new_transactions = []
                updated_count = 0
                rows_to_write = []

                for transaction in transactions:
                    row_values = (
                        transaction.get("internalTransactionId"),
                        transaction["institutionId"],
                        transaction["iban"],
                        transaction["transactionDate"],
                        transaction["description"],
                        transaction["transactionValue"],
                        transaction["transactionCurrency"],
                        transaction["transactionStatus"],
                        json.dumps(transaction["rawTransaction"]),
                    )
                    key = (transaction["accountId"], transaction["transactionId"])
                    existing = existing_rows.get(key)

                    if existing is not None and existing == row_values:
                        continue

                    rows_to_write.append((*key, *row_values))
                    if existing is None:
                        new_transactions.append(transaction)
                    else:
                        updated_count += 1
                    # Record the row so a duplicate key later in the same
                    # batch is treated as an update, not a second insert.
                    existing_rows[key] = row_values

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

                if rows_to_write:
                    try:
                        cursor.executemany(insert_sql, rows_to_write)
                    except sqlite3.IntegrityError:
                        # One bad row (e.g. a NULL key) must not sink the
                        # whole batch: retry row by row and skip offenders.
                        for row in rows_to_write:
                            try:
                                cursor.execute(insert_sql, row)
                            except sqlite3.IntegrityError as e:
                                logger.warning(
                                    f"Failed to insert transaction {row[1]}: {e}"
                                )

                conn.commit()

            logger.info(
                f"Persisted {len(new_transactions)} new and {updated_count} updated "
                f"transactions for account {account_id}"
            )
            return new_transactions, updated_count
        except Exception as e:
            logger.error(f"Failed to persist transactions: {e}")
            raise

    def get_transactions(
        self,
        account_id: str | None = None,
        limit: int | None = 100,
        offset: int = 0,
        date_from: str | None = None,
        date_to: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        search: str | None = None,
        category_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get transactions with optional filtering"""
        if not db_exists():
            return []

        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()

            filter_clause, params = self._build_filter_clause(
                account_id=account_id,
                date_from=date_from,
                date_to=date_to,
                min_amount=min_amount,
                max_amount=max_amount,
                search=search,
                category_id=category_id,
            )

            query = (
                f"""SELECT t.*, tc.categoryId, c.name as categoryName, c.color as categoryColor
                FROM transactions t{_CATEGORY_JOIN}
                WHERE 1=1"""
                + filter_clause
            )
            query += " ORDER BY t.transactionDate DESC"

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
        account_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        search: str | None = None,
        category_id: str | None = None,
    ) -> int:
        """Get total count of transactions matching filters"""
        if not db_exists():
            return 0

        with get_db_connection() as conn:
            cursor = conn.cursor()

            filter_clause, params = self._build_filter_clause(
                account_id=account_id,
                date_from=date_from,
                date_to=date_to,
                min_amount=min_amount,
                max_amount=max_amount,
                search=search,
                category_id=category_id,
            )

            query = (
                f"""SELECT COUNT(*) FROM transactions t{_CATEGORY_JOIN}
                WHERE 1=1"""
                + filter_clause
            )
            cursor.execute(query, params)
            return cursor.fetchone()[0]

    def get_stats_totals(
        self,
        account_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        search: str | None = None,
        category_id: str | None = None,
    ) -> dict[str, Any]:
        """Aggregate totals for the filtered set, computed in SQL.

        Transactions whose category is flagged exclude_from_stats are left
        out. Summing amounts across currencies is meaningless, so money
        totals cover only the dominant (most frequent) currency of the set,
        while the counts cover every matching transaction.
        """
        empty: dict[str, Any] = {
            "total_transactions": 0,
            "booked_transactions": 0,
            "pending_transactions": 0,
            "currency": None,
            "total_income": 0,
            "total_expenses": 0,
            "net_change": 0,
            "average_transaction": 0,
            "accounts_included": 0,
        }
        if not db_exists():
            return empty

        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()

            filter_clause, params = self._build_filter_clause(
                account_id=account_id,
                date_from=date_from,
                date_to=date_to,
                min_amount=min_amount,
                max_amount=max_amount,
                search=search,
                category_id=category_id,
            )

            base = (
                f"""FROM transactions t{_CATEGORY_JOIN}
                WHERE (c.exclude_from_stats IS NULL OR c.exclude_from_stats = 0)"""
                + filter_clause
            )

            cursor.execute(
                f"""SELECT t.transactionCurrency AS currency, COUNT(*) AS n
                {base}
                GROUP BY t.transactionCurrency ORDER BY n DESC LIMIT 1""",
                params,
            )
            row = cursor.fetchone()
            if row is None:
                return empty
            # A NULL currency (legacy rows) still counts as the dominant
            # group, hence `IS ?` below instead of `= ?`.
            currency = row["currency"]

            # Placeholder order matters: the four currency parameters sit in
            # the SELECT list, before the filter parameters from the WHERE.
            cursor.execute(
                f"""SELECT
                    COUNT(*) AS total_transactions,
                    SUM(CASE WHEN t.transactionStatus = 'booked' THEN 1 ELSE 0 END) AS booked_transactions,
                    SUM(CASE WHEN t.transactionStatus = 'pending' THEN 1 ELSE 0 END) AS pending_transactions,
                    COUNT(DISTINCT t.accountId) AS accounts_included,
                    COALESCE(SUM(CASE WHEN t.transactionCurrency IS ? AND t.transactionValue > 0 THEN t.transactionValue ELSE 0 END), 0) AS total_income,
                    COALESCE(SUM(CASE WHEN t.transactionCurrency IS ? AND t.transactionValue < 0 THEN ABS(t.transactionValue) ELSE 0 END), 0) AS total_expenses,
                    COALESCE(SUM(CASE WHEN t.transactionCurrency IS ? THEN t.transactionValue ELSE 0 END), 0) AS money_sum,
                    SUM(CASE WHEN t.transactionCurrency IS ? THEN 1 ELSE 0 END) AS money_count
                {base}""",
                [currency] * 4 + params,
            )
            totals = cursor.fetchone()

            money_count = totals["money_count"] or 0
            total_income = round(totals["total_income"], 2)
            total_expenses = round(totals["total_expenses"], 2)

            return {
                "total_transactions": totals["total_transactions"],
                "booked_transactions": totals["booked_transactions"] or 0,
                "pending_transactions": totals["pending_transactions"] or 0,
                "currency": currency,
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_change": round(total_income - total_expenses, 2),
                "average_transaction": round(totals["money_sum"] / money_count, 2)
                if money_count
                else 0,
                "accounts_included": totals["accounts_included"],
            }

    def get_transaction_by_id(
        self, account_id: str, transaction_id: str
    ) -> dict[str, Any] | None:
        """Get a single transaction by its primary key."""
        if not db_exists():
            return None

        with get_db_connection(row_factory=True) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT t.*, tc.categoryId, c.name as categoryName, c.color as categoryColor
                FROM transactions t
                LEFT JOIN transaction_categories tc ON t.accountId = tc.accountId AND t.transactionId = tc.transactionId
                LEFT JOIN categories c ON tc.categoryId = c.id
                WHERE t.accountId = ? AND t.transactionId = ?""",
                (account_id, transaction_id),
            )
            row = cursor.fetchone()
            if row:
                transaction = dict(row)
                if transaction["rawTransaction"]:
                    transaction["rawTransaction"] = json.loads(
                        transaction["rawTransaction"]
                    )
                return transaction
            return None
