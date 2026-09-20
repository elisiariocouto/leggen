from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from leggen.api.models.accounts import (
    Transaction,
    TransactionSummary,
    TransactionUpdate,
)
from leggen.api.models.common import PaginatedResponse
from leggen.api.models.stats import TransactionStats
from leggen.api.models.transactions import (
    TransactionListQuery,
    TransactionStatsFilters,
)
from leggen.errors import NotFoundError
from leggen.repositories import TransactionRepository

router = APIRouter()


def _to_summary(txn: dict[str, Any]) -> TransactionSummary:
    """Shape a repository row as a list-view summary."""
    return TransactionSummary(
        transaction_id=txn["transactionId"],
        internal_transaction_id=txn.get("internalTransactionId"),
        date=txn["transactionDate"],
        description=txn["description"],
        amount=txn["transactionValue"],
        currency=txn["transactionCurrency"],
        status=txn["transactionStatus"],
        account_id=txn["accountId"],
        category_id=txn.get("categoryId"),
        category_name=txn.get("categoryName"),
        category_color=txn.get("categoryColor"),
        exclude_from_stats=txn.get("exclude_from_stats"),
        category_source=txn.get("categorySource"),
        category_rule_id=txn.get("categoryRuleId"),
    )


def _to_transaction(txn: dict[str, Any]) -> Transaction:
    """Shape a repository row as the full transaction model."""
    return Transaction(
        transaction_id=txn["transactionId"],
        internal_transaction_id=txn.get("internalTransactionId"),
        institution_id=txn["institutionId"],
        iban=txn["iban"],
        account_id=txn["accountId"],
        transaction_date=txn["transactionDate"],
        description=txn["description"],
        transaction_value=txn["transactionValue"],
        transaction_currency=txn["transactionCurrency"],
        transaction_status=txn["transactionStatus"],
        raw_transaction=txn["rawTransaction"],
        category_id=txn.get("categoryId"),
        category_name=txn.get("categoryName"),
        category_color=txn.get("categoryColor"),
        exclude_from_stats=txn.get("exclude_from_stats"),
        category_source=txn.get("categorySource"),
        category_rule_id=txn.get("categoryRuleId"),
    )


@router.get("/transactions")
async def get_all_transactions(
    transaction_repo: Annotated[TransactionRepository, Depends()],
    query: Annotated[TransactionListQuery, Query()],
) -> PaginatedResponse[TransactionSummary | Transaction]:
    """Get all transactions from database with filtering options"""
    criteria = query.to_filter()
    db_transactions = transaction_repo.get_transactions(
        criteria,
        limit=query.per_page,
        offset=(query.page - 1) * query.per_page,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
    )
    total_transactions = transaction_repo.get_count(criteria)

    data: list[TransactionSummary | Transaction]
    if query.summary_only:
        data = [_to_summary(txn) for txn in db_transactions]
    else:
        data = [_to_transaction(txn) for txn in db_transactions]

    return PaginatedResponse.build(
        data, total=total_transactions, page=query.page, per_page=query.per_page
    )


@router.patch(
    "/transactions/{account_id}/{transaction_id}",
    response_model=Transaction,
    responses={404: {"description": "Transaction not found"}},
)
async def update_transaction(
    account_id: str,
    transaction_id: str,
    body: TransactionUpdate,
    transaction_repo: Annotated[TransactionRepository, Depends()],
) -> Transaction:
    """Update a transaction's user-editable fields.

    Only `exclude_from_stats` is editable; everything else is owned by the
    bank feed and overwritten on sync. Pass `null` to clear the override so
    the category's own flag applies again.
    """
    if not transaction_repo.set_exclude_from_stats(
        account_id, transaction_id, body.exclude_from_stats
    ):
        raise NotFoundError("Transaction not found.")
    txn = transaction_repo.get_transaction_by_id(account_id, transaction_id)
    if txn is None:
        raise NotFoundError("Transaction not found.")
    return _to_transaction(txn)


@router.get("/transactions/stats")
async def get_transaction_stats(
    transaction_repo: Annotated[TransactionRepository, Depends()],
    filters: Annotated[TransactionStatsFilters, Query()],
) -> TransactionStats:
    """Get transaction statistics for a date range."""
    totals = transaction_repo.get_stats_totals(filters.to_filter())
    return TransactionStats(
        date_from=filters.date_from.isoformat(),
        date_to=filters.date_to.isoformat(),
        **totals,
    )
