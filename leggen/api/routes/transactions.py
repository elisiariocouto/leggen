from typing import Annotated, List, Literal, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from leggen.api.models.accounts import Transaction, TransactionSummary
from leggen.api.models.common import PaginatedResponse
from leggen.repositories import TransactionRepository
from leggen.services.data_processors import calculate_monthly_stats

router = APIRouter()


@router.get("/transactions")
async def get_all_transactions(
    transaction_repo: Annotated[TransactionRepository, Depends()],
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(default=50, le=500, description="Items per page"),
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
) -> PaginatedResponse[Union[TransactionSummary, Transaction]]:
    """Get all transactions from database with filtering options"""
    try:
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
        )

        # Get total count for pagination info (respecting the same filters)
        total_transactions = transaction_repo.get_count(
            account_id=account_id,
            date_from=date_from,
            date_to=date_to,
            min_amount=min_amount,
            max_amount=max_amount,
            search=search,
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

    except Exception as e:
        logger.error(f"Failed to get transactions from database: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get transactions: {str(e)}"
        ) from e


@router.get("/transactions/stats")
async def get_transaction_stats(
    transaction_repo: Annotated[TransactionRepository, Depends()],
    date_from: str = Query(description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(description="End date (YYYY-MM-DD)"),
    account_id: Optional[str] = Query(default=None, description="Filter by account ID"),
    group_by: Optional[Literal["month"]] = Query(
        default=None, description="Group results by month"
    ),
) -> Union[dict, List[dict]]:
    """Get transaction statistics for a date range.

    Without group_by: returns totals (transactions, income, expenses, etc.)
    With group_by=month: returns array of monthly stats.
    """
    try:
        if group_by == "month":
            from leggen.utils.paths import path_manager

            db_path = path_manager.get_database_path()
            return calculate_monthly_stats(
                db_path,
                account_id=account_id,
                date_from=date_from,
                date_to=date_to,
            )

        # Default: return totals
        recent_transactions = transaction_repo.get_transactions(
            account_id=account_id,
            date_from=date_from,
            date_to=date_to,
            limit=None,
        )

        total_transactions = len(recent_transactions)
        total_income = sum(
            txn["transactionValue"]
            for txn in recent_transactions
            if txn["transactionValue"] > 0
        )
        total_expenses = sum(
            abs(txn["transactionValue"])
            for txn in recent_transactions
            if txn["transactionValue"] < 0
        )
        net_change = total_income - total_expenses

        booked_count = len(
            [txn for txn in recent_transactions if txn["transactionStatus"] == "booked"]
        )
        pending_count = len(
            [
                txn
                for txn in recent_transactions
                if txn["transactionStatus"] == "pending"
            ]
        )

        unique_accounts = len({txn["accountId"] for txn in recent_transactions})

        return {
            "date_from": date_from,
            "date_to": date_to,
            "total_transactions": total_transactions,
            "booked_transactions": booked_count,
            "pending_transactions": pending_count,
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "net_change": round(net_change, 2),
            "average_transaction": round(
                sum(txn["transactionValue"] for txn in recent_transactions)
                / total_transactions,
                2,
            )
            if total_transactions > 0
            else 0,
            "accounts_included": unique_accounts,
        }

    except Exception as e:
        logger.error(f"Failed to get transaction stats from database: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get transaction stats: {str(e)}"
        ) from e
