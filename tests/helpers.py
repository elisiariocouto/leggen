"""Helpers shared across test modules: seeding the temp database through the
real repositories, and reading back what the rule engine assigned.

Fixtures live in conftest.py; these are plain functions so tests can call
them with explicit arguments.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import AsyncMock, patch

from leggen.repositories import (
    CategoryRepository,
    SessionRepository,
    TransactionRepository,
)
from leggen.repositories.db import get_db_connection
from leggen.services.sync_service import SyncService

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


# --- Sync ---------------------------------------------------------------

DEFAULT_SESSION = {
    "session_id": "sess-1",
    "aspsp_name": "TEST_BANK",
    "aspsp_country": "PT",
    "status": "active",
    "created_at": "2025-09-01T00:00:00Z",
}


def seed_session(accounts: list[Any], **overrides: Any) -> dict[str, Any]:
    """Persist an EnableBanking session row.

    `accounts` is what the bank returned: dicts carrying `uid` (and possibly
    `account_id.iban`), or plain UID strings for older rows.
    """
    row = {**DEFAULT_SESSION, "accounts": accounts, **overrides}
    SessionRepository().persist(row)
    return row


def account_details(uid: str, iban: str, **overrides: Any) -> dict[str, Any]:
    """An account-details payload as EnableBanking returns it."""
    return {
        "uid": uid,
        "account_id": {"iban": iban},
        "name": "Test Account",
        "currency": "EUR",
        **overrides,
    }


def bank_transaction(
    transaction_id: str, description: str, amount: str, **overrides: Any
) -> dict[str, Any]:
    """One transaction in EnableBanking's own format."""
    return {
        "transaction_id": transaction_id,
        "entry_reference": f"ref-{transaction_id}",
        "booking_date": "2025-09-01",
        "transaction_amount": {"amount": amount, "currency": "EUR"},
        "credit_debit_indicator": "DBIT",
        "remittance_information": [description],
        "status": "BOOK",
        **overrides,
    }


@contextmanager
def enablebanking_returns(
    sync_service: SyncService,
    *,
    details: dict[str, dict[str, Any]] | Callable[..., Any] | BaseException,
    balances: dict[str, Any] | None = None,
    transactions: list[dict[str, Any]] | None = None,
) -> Iterator[AsyncMock]:
    """Stub the EnableBanking calls a sync makes; everything else stays real.

    `details` maps account UID to its details payload; a callable or an
    exception is used as the side effect instead. `balances` and
    `transactions` are returned for every account. Yields the account-details
    mock so tests can assert which accounts were looked up.
    """
    side_effect: Any = details
    if isinstance(details, dict):
        lookup = details

        def side_effect(uid: str) -> dict[str, Any]:
            return lookup[uid]

    bank = sync_service.enablebanking
    with (
        patch.object(bank, "get_account_details", side_effect=side_effect) as mocked,
        patch.object(bank, "get_account_balances", return_value=balances or {}),
        patch.object(
            bank,
            "get_account_transactions",
            return_value={"transactions": transactions or []},
        ),
        # Account enrichment looks the institution logo up when balances exist.
        patch.object(bank, "get_aspsps", return_value=[]),
    ):
        yield mocked
