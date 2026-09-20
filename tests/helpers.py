"""Helpers shared across test modules: seeding the temp database through the
real repositories, and reading back what the rule engine assigned.

Fixtures live in conftest.py; these are plain functions so tests can call
them with explicit arguments.
"""

from typing import Any

from leggen.repositories import CategoryRepository, TransactionRepository
from leggen.repositories.db import get_db_connection

DEFAULT_ACCOUNT_ID = "acc-1"
DEFAULT_IBAN = "LT313250081177977789"


def seed_transactions(rows: list[dict[str, Any]]) -> None:
    """Persist transactions through the real repository.

    Each row needs `id` and `value`; `account_id`, `iban`, `date`,
    `description`, `currency`, `status` and `raw` fall back to defaults.
    """
    by_account: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        account_id = row.get("account_id", DEFAULT_ACCOUNT_ID)
        by_account.setdefault(account_id, []).append(
            {
                "transactionId": row["id"],
                "internalTransactionId": f"int-{row['id']}",
                "institutionId": "TEST_BANK",
                "iban": row.get("iban", DEFAULT_IBAN),
                "accountId": account_id,
                "transactionDate": row.get("date", "2025-09-05T10:00:00"),
                "description": row.get("description", "Payment"),
                "transactionValue": row["value"],
                "transactionCurrency": row.get("currency", "EUR"),
                "transactionStatus": row.get("status", "booked"),
                "rawTransaction": row.get("raw", {}),
            }
        )
    repo = TransactionRepository()
    for account_id, transactions in by_account.items():
        repo.persist(account_id, transactions)


def persist_transactions(rows: list[tuple]) -> None:
    """Tuple shorthand for `seed_transactions`.

    Each row: (txn_id, account_id, date, value, currency, status).
    """
    seed_transactions(
        [
            {
                "id": txn_id,
                "account_id": account_id,
                "date": date,
                "value": value,
                "currency": currency,
                "status": status,
                "description": f"Transaction {txn_id}",
                "raw": {"transactionId": txn_id},
            }
            for txn_id, account_id, date, value, currency, status in rows
        ]
    )


def category_id(name: str) -> int:
    """ID of the category with this name (the defaults are seeded by migrations)."""
    return next(
        c for c in CategoryRepository().get_all_categories() if c["name"] == name
    )["id"]


def category_assignments() -> dict[str, dict[str, Any]]:
    """Every transaction_categories row, keyed by transaction ID."""
    with get_db_connection(row_factory=True) as conn:
        rows = conn.execute(
            "SELECT transactionId, categoryId, source, ruleId, exclude_from_stats"
            " FROM transaction_categories"
        ).fetchall()
    return {row["transactionId"]: dict(row) for row in rows}
