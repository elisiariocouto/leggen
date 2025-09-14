from datetime import datetime, timedelta
from typing import List, Optional, Union

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from leggen.api.models.accounts import Transaction, TransactionSummary
from leggen.api.models.common import APIResponse, PaginatedResponse
from leggen.services.database_service import DatabaseService

router = APIRouter()
database_service = DatabaseService()


@router.get("/transactions", response_model=PaginatedResponse)
async def get_all_transactions(
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
) -> PaginatedResponse:
    """Get all transactions from database with filtering options"""
    try:
        # Calculate offset from page and per_page
        offset = (page - 1) * per_page
        limit = per_page

        # Get transactions from database instead of GoCardless API
        db_transactions = await database_service.get_transactions_from_db(
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
        total_transactions = await database_service.get_transaction_count_from_db(
            account_id=account_id,
            date_from=date_from,
            date_to=date_to,
            min_amount=min_amount,
            max_amount=max_amount,
            search=search,
        )

        data: Union[List[TransactionSummary], List[Transaction]]

        if summary_only:
            # Return simplified transaction summaries
            data = [
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
            success=True,
            data=data,
            pagination={
                "total": total_transactions,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        )

    except Exception as e:
        logger.error(f"Failed to get transactions from database: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get transactions: {str(e)}"
        ) from e


@router.get("/transactions/stats", response_model=APIResponse)
async def get_transaction_stats(
    days: int = Query(default=30, description="Number of days to include in stats"),
    account_id: Optional[str] = Query(default=None, description="Filter by account ID"),
) -> APIResponse:
    """Get transaction statistics for the last N days from database"""
    try:
        # Date range for stats
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Format dates for database query
        date_from = start_date.isoformat()
        date_to = end_date.isoformat()

        # Get transactions from database
        recent_transactions = await database_service.get_transactions_from_db(
            account_id=account_id,
            date_from=date_from,
            date_to=date_to,
            limit=None,  # Get all matching transactions for stats
        )

        # Calculate stats
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

        # Count by status
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

        # Count unique accounts
        unique_accounts = len({txn["accountId"] for txn in recent_transactions})

        stats = {
            "period_days": days,
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

        return APIResponse(
            success=True,
            data=stats,
            message=f"Transaction statistics for last {days} days",
        )

    except Exception as e:
        logger.error(f"Failed to get transaction stats from database: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get transaction stats: {str(e)}"
        ) from e


@router.get("/transactions/analytics", response_model=APIResponse)
async def get_transactions_for_analytics(
    days: int = Query(default=365, description="Number of days to include"),
    account_id: Optional[str] = Query(default=None, description="Filter by account ID"),
) -> APIResponse:
    """Get all transactions for analytics (no pagination) for the last N days"""
    try:
        # Date range for analytics
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Format dates for database query
        date_from = start_date.isoformat()
        date_to = end_date.isoformat()

        # Get ALL transactions from database (no limit for analytics)
        transactions = await database_service.get_transactions_from_db(
            account_id=account_id,
            date_from=date_from,
            date_to=date_to,
            limit=None,  # No limit - get all transactions
        )

        # Transform for frontend (summary format)
        transaction_summaries = [
            {
                "transaction_id": txn["transactionId"],
                "date": txn["transactionDate"],
                "description": txn["description"],
                "amount": txn["transactionValue"],
                "currency": txn["transactionCurrency"],
                "status": txn["transactionStatus"],
                "account_id": txn["accountId"],
            }
            for txn in transactions
        ]

        return APIResponse(
            success=True,
            data=transaction_summaries,
            message=f"Retrieved {len(transaction_summaries)} transactions for analytics",
        )

    except Exception as e:
        logger.error(f"Failed to get transactions for analytics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get analytics transactions: {str(e)}"
        ) from e


@router.get("/transactions/monthly-stats", response_model=APIResponse)
async def get_monthly_transaction_stats(
    days: int = Query(default=365, description="Number of days to include"),
    account_id: Optional[str] = Query(default=None, description="Filter by account ID"),
) -> APIResponse:
    """Get monthly transaction statistics aggregated by the database"""
    try:
        # Date range for monthly stats
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Format dates for database query
        date_from = start_date.isoformat()
        date_to = end_date.isoformat()

        # Get monthly aggregated stats from database
        monthly_stats = await database_service.get_monthly_transaction_stats_from_db(
            account_id=account_id,
            date_from=date_from,
            date_to=date_to,
        )

        return APIResponse(
            success=True,
            data=monthly_stats,
            message=f"Retrieved monthly stats for last {days} days",
        )

    except Exception as e:
        logger.error(f"Failed to get monthly transaction stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get monthly stats: {str(e)}"
        ) from e
