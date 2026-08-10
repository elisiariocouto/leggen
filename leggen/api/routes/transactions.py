from typing import Annotated, List, Literal, Optional, Union

from fastapi import APIRouter, Depends, Query

from leggen.api.models.accounts import Transaction, TransactionSummary
from leggen.api.models.common import PaginatedResponse
from leggen.api.models.stats import CategoryStats, MonthlyStats, TransactionStats
from leggen.repositories import TransactionRepository
from leggen.services.data_processors import (
    calculate_category_stats,
    calculate_monthly_stats,
)
from leggen.utils.paths import path_manager

router = APIRouter()


# A category filter is either a numeric ID or the "uncategorized" bucket.
# Declaring it as a pattern lets FastAPI produce the 422, so the response
# carries field-level errors and the constraint shows up in the schema.
_CATEGORY_ID_PATTERN = r"^(\d+|uncategorized)$"


@router.get("/transactions")
async def get_all_transactions(
    transaction_repo: Annotated[TransactionRepository, Depends()],
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(default=50, ge=1, le=500, description="Items per page"),
    summary_only: bool = Query(
        default=True, description="Return transaction summaries only"
    ),
    date_from: Optional[str] = Query(
        default=None, description="Filter from date (YYYY-MM-DD)"
    ),
    date_to: Optional[str] = Query(
        default=None, description="Filter to date (YYYY-MM-DD)"
    ),
    min_amount: Optional[float] = Query(
        default=None, description="Minimum transaction amount"
    ),
    max_amount: Optional[float] = Query(
        default=None, description="Maximum transaction amount"
    ),
    search: Optional[str] = Query(
        default=None, description="Search in transaction descriptions"
    ),
    account_id: Optional[str] = Query(default=None, description="Filter by account ID"),
    category_id: Optional[str] = Query(
        default=None,
        pattern=_CATEGORY_ID_PATTERN,
        description="Filter by category ID or 'uncategorized' for transactions without a category",
    ),
) -> PaginatedResponse[Union[TransactionSummary, Transaction]]:
    """Get all transactions from database with filtering options"""
    # Calculate offset from page and per_page
    offset = (page - 1) * per_page
    limit = per_page

    # Get transactions from database
    db_transactions = transaction_repo.get_transactions(
        account_id=account_id,
        limit=limit,
        offset=offset,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
        category_id=category_id,
    )

    # Get total count for pagination info (respecting the same filters)
    total_transactions = transaction_repo.get_count(
        account_id=account_id,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
        category_id=category_id,
    )

    if summary_only:
        # Return simplified transaction summaries
        data: list[TransactionSummary | Transaction] = [
            TransactionSummary(
                transaction_id=txn["transactionId"],  # NEW: stable bank-provided ID
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
            )
            for txn in db_transactions
        ]
    else:
        # Return full transaction details
        data = [
            Transaction(
                transaction_id=txn["transactionId"],  # NEW: stable bank-provided ID
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
            )
            for txn in db_transactions
        ]

    total_pages = (total_transactions + per_page - 1) // per_page

    return PaginatedResponse(
        data=data,
        total=total_transactions,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@router.get("/transactions/stats")
async def get_transaction_stats(
    transaction_repo: Annotated[TransactionRepository, Depends()],
    date_from: str = Query(description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(description="End date (YYYY-MM-DD)"),
    account_id: Optional[str] = Query(default=None, description="Filter by account ID"),
    search: Optional[str] = Query(
        default=None, description="Search in transaction descriptions"
    ),
    min_amount: Optional[float] = Query(
        default=None, description="Minimum transaction amount"
    ),
    max_amount: Optional[float] = Query(
        default=None, description="Maximum transaction amount"
    ),
    group_by: Optional[Literal["month"]] = Query(
        default=None, description="Group results by month"
    ),
    category_id: Optional[str] = Query(
        default=None,
        pattern=_CATEGORY_ID_PATTERN,
        description="Filter by category ID or 'uncategorized' for transactions without a category",
    ),
) -> Union[TransactionStats, List[MonthlyStats]]:
    """Get transaction statistics for a date range.

    Without group_by: returns totals (transactions, income, expenses, etc.)
    With group_by=month: returns array of monthly stats.
    """
    if group_by == "month":
        db_path = path_manager.get_database_path()
        monthly = calculate_monthly_stats(
            db_path,
            account_id=account_id,
            date_from=date_from,
            date_to=date_to,
        )
        return [MonthlyStats(**entry) for entry in monthly]

    totals = transaction_repo.get_stats_totals(
        account_id=account_id,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
        category_id=category_id,
    )
    return TransactionStats(date_from=date_from, date_to=date_to, **totals)


@router.get("/transactions/stats/by-category")
async def get_stats_by_category(
    date_from: str = Query(description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(description="End date (YYYY-MM-DD)"),
    account_id: Optional[str] = Query(default=None, description="Filter by account ID"),
) -> List[CategoryStats]:
    """Get transaction statistics grouped by category."""
    db_path = path_manager.get_database_path()
    category_stats = calculate_category_stats(
        db_path,
        account_id=account_id,
        date_from=date_from,
        date_to=date_to,
    )
    return [CategoryStats(**entry) for entry in category_stats]
