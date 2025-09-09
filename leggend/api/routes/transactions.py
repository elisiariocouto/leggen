from typing import Optional, List, Union
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from leggend.api.models.common import APIResponse
from leggend.api.models.accounts import Transaction, TransactionSummary
from leggend.services.database_service import DatabaseService

router = APIRouter()
database_service = DatabaseService()


@router.get("/transactions", response_model=APIResponse)
async def get_all_transactions(
    limit: Optional[int] = Query(default=100, le=500),
    offset: Optional[int] = Query(default=0, ge=0),
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
) -> APIResponse:
    """Get all transactions from database with filtering options"""
    try:
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

        # Get total count for pagination info
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
                    internal_transaction_id=txn["internalTransactionId"],
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
                    internal_transaction_id=txn["internalTransactionId"],
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

        actual_offset = offset or 0
        return APIResponse(
            success=True,
            data=data,
            message=f"Retrieved {len(data)} transactions (showing {actual_offset + 1}-{actual_offset + len(data)} of {total_transactions})",
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
