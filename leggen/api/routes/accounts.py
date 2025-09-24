from typing import List, Optional, Union

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from leggen.api.models.accounts import (
    AccountBalance,
    AccountDetails,
    AccountUpdate,
    Transaction,
    TransactionSummary,
)
from leggen.api.models.common import APIResponse
from leggen.services.database_service import DatabaseService

router = APIRouter()
database_service = DatabaseService()


@router.get("/accounts", response_model=APIResponse)
async def get_all_accounts() -> APIResponse:
    """Get all connected accounts from database"""
    try:
        accounts = []

        # Get all account details from database
        db_accounts = await database_service.get_accounts_from_db()

        # Process accounts found in database
        for db_account in db_accounts:
            try:
                # Get latest balances from database for this account
                balances_data = await database_service.get_balances_from_db(
                    db_account["id"]
                )

                # Process balances
                balances = []
                for balance in balances_data:
                    balances.append(
                        AccountBalance(
                            amount=balance["amount"],
                            currency=balance["currency"],
                            balance_type=balance["type"],
                            last_change_date=balance.get("timestamp"),
                        )
                    )

                accounts.append(
                    AccountDetails(
                        id=db_account["id"],
                        institution_id=db_account["institution_id"],
                        status=db_account["status"],
                        iban=db_account.get("iban"),
                        name=db_account.get("name"),
                        display_name=db_account.get("display_name"),
                        currency=db_account.get("currency"),
                        logo=db_account.get("logo"),
                        created=db_account["created"],
                        last_accessed=db_account.get("last_accessed"),
                        balances=balances,
                    )
                )

            except Exception as e:
                logger.error(
                    f"Failed to process database account {db_account['id']}: {e}"
                )
                continue

        return APIResponse(
            success=True,
            data=accounts,
            message=f"Retrieved {len(accounts)} accounts from database",
        )

    except Exception as e:
        logger.error(f"Failed to get accounts: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get accounts: {str(e)}"
        ) from e


@router.get("/accounts/{account_id}", response_model=APIResponse)
async def get_account_details(account_id: str) -> APIResponse:
    """Get details for a specific account from database"""
    try:
        # Get account details from database
        db_account = await database_service.get_account_details_from_db(account_id)

        if not db_account:
            raise HTTPException(
                status_code=404, detail=f"Account {account_id} not found in database"
            )

        # Get latest balances from database for this account
        balances_data = await database_service.get_balances_from_db(account_id)

        # Process balances
        balances = []
        for balance in balances_data:
            balances.append(
                AccountBalance(
                    amount=balance["amount"],
                    currency=balance["currency"],
                    balance_type=balance["type"],
                    last_change_date=balance.get("timestamp"),
                )
            )

        account = AccountDetails(
            id=db_account["id"],
            institution_id=db_account["institution_id"],
            status=db_account["status"],
            iban=db_account.get("iban"),
            name=db_account.get("name"),
            display_name=db_account.get("display_name"),
            currency=db_account.get("currency"),
            logo=db_account.get("logo"),
            created=db_account["created"],
            last_accessed=db_account.get("last_accessed"),
            balances=balances,
        )

        return APIResponse(
            success=True,
            data=account,
            message=f"Account details retrieved from database for {account_id}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get account details for {account_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get account details: {str(e)}"
        ) from e


@router.get("/accounts/{account_id}/balances", response_model=APIResponse)
async def get_account_balances(account_id: str) -> APIResponse:
    """Get balances for a specific account from database"""
    try:
        # Get balances from database instead of GoCardless API
        db_balances = await database_service.get_balances_from_db(account_id=account_id)

        balances = []
        for balance in db_balances:
            balances.append(
                AccountBalance(
                    amount=balance["amount"],
                    currency=balance["currency"],
                    balance_type=balance["type"],
                    last_change_date=balance.get("timestamp"),
                )
            )

        return APIResponse(
            success=True,
            data=balances,
            message=f"Retrieved {len(balances)} balances for account {account_id}",
        )

    except Exception as e:
        logger.error(
            f"Failed to get balances from database for account {account_id}: {e}"
        )
        raise HTTPException(
            status_code=404, detail=f"Failed to get balances: {str(e)}"
        ) from e


@router.get("/balances", response_model=APIResponse)
async def get_all_balances() -> APIResponse:
    """Get all balances from all accounts in database"""
    try:
        # Get all accounts first to iterate through them
        db_accounts = await database_service.get_accounts_from_db()

        all_balances = []
        for db_account in db_accounts:
            try:
                # Get balances for this account
                db_balances = await database_service.get_balances_from_db(
                    account_id=db_account["id"]
                )

                # Process balances and add account info
                for balance in db_balances:
                    balance_data = {
                        "id": f"{db_account['id']}_{balance['type']}",  # Create unique ID
                        "account_id": db_account["id"],
                        "balance_amount": balance["amount"],
                        "balance_type": balance["type"],
                        "currency": balance["currency"],
                        "reference_date": balance.get(
                            "timestamp", db_account.get("last_accessed")
                        ),
                        "created_at": db_account.get("created"),
                        "updated_at": db_account.get("last_accessed"),
                    }
                    all_balances.append(balance_data)

            except Exception as e:
                logger.error(
                    f"Failed to get balances for account {db_account['id']}: {e}"
                )
                continue

        return APIResponse(
            success=True,
            data=all_balances,
            message=f"Retrieved {len(all_balances)} balances from {len(db_accounts)} accounts",
        )

    except Exception as e:
        logger.error(f"Failed to get all balances: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get balances: {str(e)}"
        ) from e


@router.get("/balances/history", response_model=APIResponse)
async def get_historical_balances(
    days: Optional[int] = Query(
        default=365, le=1095, ge=1, description="Number of days of history to retrieve"
    ),
    account_id: Optional[str] = Query(
        default=None, description="Filter by specific account ID"
    ),
) -> APIResponse:
    """Get historical balance progression calculated from transaction history"""
    try:
        # Get historical balances from database
        historical_balances = await database_service.get_historical_balances_from_db(
            account_id=account_id, days=days or 365
        )

        return APIResponse(
            success=True,
            data=historical_balances,
            message=f"Retrieved {len(historical_balances)} historical balance points over {days} days",
        )

    except Exception as e:
        logger.error(f"Failed to get historical balances: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get historical balances: {str(e)}"
        ) from e


@router.get("/accounts/{account_id}/transactions", response_model=APIResponse)
async def get_account_transactions(
    account_id: str,
    limit: Optional[int] = Query(default=100, le=500),
    offset: Optional[int] = Query(default=0, ge=0),
    summary_only: bool = Query(
        default=False, description="Return transaction summaries only"
    ),
) -> APIResponse:
    """Get transactions for a specific account from database"""
    try:
        # Get transactions from database instead of GoCardless API
        db_transactions = await database_service.get_transactions_from_db(
            account_id=account_id,
            limit=limit,
            offset=offset,
        )

        # Get total count for pagination info
        total_transactions = await database_service.get_transaction_count_from_db(
            account_id=account_id,
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

        actual_offset = offset or 0
        return APIResponse(
            success=True,
            data=data,
            message=f"Retrieved {len(data)} transactions (showing {actual_offset + 1}-{actual_offset + len(data)} of {total_transactions})",
        )

    except Exception as e:
        logger.error(
            f"Failed to get transactions from database for account {account_id}: {e}"
        )
        raise HTTPException(
            status_code=404, detail=f"Failed to get transactions: {str(e)}"
        ) from e


@router.put("/accounts/{account_id}", response_model=APIResponse)
async def update_account_details(
    account_id: str, update_data: AccountUpdate
) -> APIResponse:
    """Update account details (currently only display_name)"""
    try:
        # Get current account details
        current_account = await database_service.get_account_details_from_db(account_id)

        if not current_account:
            raise HTTPException(
                status_code=404, detail=f"Account {account_id} not found"
            )

        # Prepare updated account data
        updated_account_data = current_account.copy()
        if update_data.display_name is not None:
            updated_account_data["display_name"] = update_data.display_name

        # Persist updated account details
        await database_service.persist_account_details(updated_account_data)

        return APIResponse(
            success=True,
            data={"id": account_id, "display_name": update_data.display_name},
            message=f"Account {account_id} display name updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update account {account_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update account: {str(e)}"
        ) from e
