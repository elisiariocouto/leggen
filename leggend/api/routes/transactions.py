from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from leggend.api.models.common import APIResponse
from leggend.api.models.accounts import Transaction, TransactionSummary
from leggend.services.gocardless_service import GoCardlessService
from leggend.services.database_service import DatabaseService

router = APIRouter()
gocardless_service = GoCardlessService()
database_service = DatabaseService()


@router.get("/transactions", response_model=APIResponse)
async def get_all_transactions(
    limit: Optional[int] = Query(default=100, le=500),
    offset: Optional[int] = Query(default=0, ge=0),
    summary_only: bool = Query(default=True, description="Return transaction summaries only"),
    date_from: Optional[str] = Query(default=None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(default=None, description="Filter to date (YYYY-MM-DD)"),
    min_amount: Optional[float] = Query(default=None, description="Minimum transaction amount"),
    max_amount: Optional[float] = Query(default=None, description="Maximum transaction amount"),
    search: Optional[str] = Query(default=None, description="Search in transaction descriptions"),
    account_id: Optional[str] = Query(default=None, description="Filter by account ID")
) -> APIResponse:
    """Get all transactions across all accounts with filtering options"""
    try:
        # Get all requisitions and accounts
        requisitions_data = await gocardless_service.get_requisitions()
        all_accounts = set()
        
        for req in requisitions_data.get("results", []):
            all_accounts.update(req.get("accounts", []))
        
        # Filter by specific account if requested
        if account_id:
            if account_id not in all_accounts:
                raise HTTPException(status_code=404, detail="Account not found")
            all_accounts = {account_id}
        
        all_transactions = []
        
        # Collect transactions from all accounts
        for acc_id in all_accounts:
            try:
                account_details = await gocardless_service.get_account_details(acc_id)
                transactions_data = await gocardless_service.get_account_transactions(acc_id)
                
                processed_transactions = database_service.process_transactions(
                    acc_id, account_details, transactions_data
                )
                all_transactions.extend(processed_transactions)
                
            except Exception as e:
                logger.error(f"Failed to get transactions for account {acc_id}: {e}")
                continue
        
        # Apply filters
        filtered_transactions = all_transactions
        
        # Date range filter
        if date_from:
            from_date = datetime.fromisoformat(date_from)
            filtered_transactions = [
                txn for txn in filtered_transactions 
                if txn["transactionDate"] >= from_date
            ]
            
        if date_to:
            to_date = datetime.fromisoformat(date_to)
            filtered_transactions = [
                txn for txn in filtered_transactions 
                if txn["transactionDate"] <= to_date
            ]
        
        # Amount filters
        if min_amount is not None:
            filtered_transactions = [
                txn for txn in filtered_transactions 
                if txn["transactionValue"] >= min_amount
            ]
            
        if max_amount is not None:
            filtered_transactions = [
                txn for txn in filtered_transactions 
                if txn["transactionValue"] <= max_amount
            ]
        
        # Search filter
        if search:
            search_lower = search.lower()
            filtered_transactions = [
                txn for txn in filtered_transactions 
                if search_lower in txn["description"].lower()
            ]
        
        # Sort by date (newest first)
        filtered_transactions.sort(
            key=lambda x: x["transactionDate"], 
            reverse=True
        )
        
        # Apply pagination
        total_transactions = len(filtered_transactions)
        paginated_transactions = filtered_transactions[offset:offset + limit]
        
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
                    account_id=txn["accountId"]
                )
                for txn in paginated_transactions
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
                    raw_transaction=txn["rawTransaction"]
                )
                for txn in paginated_transactions
            ]
        
        return APIResponse(
            success=True,
            data=data,
            message=f"Retrieved {len(data)} transactions (showing {offset + 1}-{offset + len(data)} of {total_transactions})"
        )
        
    except Exception as e:
        logger.error(f"Failed to get transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get transactions: {str(e)}")


@router.get("/transactions/stats", response_model=APIResponse)
async def get_transaction_stats(
    days: int = Query(default=30, description="Number of days to include in stats"),
    account_id: Optional[str] = Query(default=None, description="Filter by account ID")
) -> APIResponse:
    """Get transaction statistics for the last N days"""
    try:
        # Date range for stats
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all transactions (reuse the existing endpoint logic)
        # This is a simplified implementation - in practice you might want to optimize this
        requisitions_data = await gocardless_service.get_requisitions()
        all_accounts = set()
        
        for req in requisitions_data.get("results", []):
            all_accounts.update(req.get("accounts", []))
        
        if account_id:
            if account_id not in all_accounts:
                raise HTTPException(status_code=404, detail="Account not found")
            all_accounts = {account_id}
        
        all_transactions = []
        
        for acc_id in all_accounts:
            try:
                account_details = await gocardless_service.get_account_details(acc_id)
                transactions_data = await gocardless_service.get_account_transactions(acc_id)
                
                processed_transactions = database_service.process_transactions(
                    acc_id, account_details, transactions_data
                )
                all_transactions.extend(processed_transactions)
                
            except Exception as e:
                logger.error(f"Failed to get transactions for account {acc_id}: {e}")
                continue
        
        # Filter transactions by date range
        recent_transactions = [
            txn for txn in all_transactions
            if start_date <= txn["transactionDate"] <= end_date
        ]
        
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
        booked_count = len([txn for txn in recent_transactions if txn["transactionStatus"] == "booked"])
        pending_count = len([txn for txn in recent_transactions if txn["transactionStatus"] == "pending"])
        
        stats = {
            "period_days": days,
            "total_transactions": total_transactions,
            "booked_transactions": booked_count,
            "pending_transactions": pending_count,
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "net_change": round(net_change, 2),
            "average_transaction": round(
                sum(txn["transactionValue"] for txn in recent_transactions) / total_transactions, 2
            ) if total_transactions > 0 else 0,
            "accounts_included": len(all_accounts)
        }
        
        return APIResponse(
            success=True,
            data=stats,
            message=f"Transaction statistics for last {days} days"
        )
        
    except Exception as e:
        logger.error(f"Failed to get transaction stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get transaction stats: {str(e)}")