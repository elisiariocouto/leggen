from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from leggen.api.models.accounts import (
    AccountBalance,
    AccountDetails,
    AccountUpdate,
)
from leggen.repositories import AccountRepository, BalanceRepository
from leggen.services.data_processors import calculate_historical_balances

router = APIRouter()


@router.get("/accounts")
async def get_all_accounts(
    account_repo: Annotated[AccountRepository, Depends()],
    balance_repo: Annotated[BalanceRepository, Depends()],
) -> List[AccountDetails]:
    """Get all connected accounts from database"""
    try:
        accounts = []

        # Get all account details from database
        db_accounts = account_repo.get_accounts()

        # Process accounts found in database
        for db_account in db_accounts:
            try:
                # Get latest balances from database for this account
                balances_data = balance_repo.get_balances(db_account["id"])

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

        return accounts

    except Exception as e:
        logger.error(f"Failed to get accounts: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get accounts: {str(e)}"
        ) from e


@router.get("/balances")
async def get_all_balances(
    account_repo: Annotated[AccountRepository, Depends()],
    balance_repo: Annotated[BalanceRepository, Depends()],
) -> List[dict]:
    """Get all balances from all accounts in database"""
    try:
        # Get all accounts first to iterate through them
        db_accounts = account_repo.get_accounts()

        all_balances = []
        for db_account in db_accounts:
            try:
                # Get balances for this account
                db_balances = balance_repo.get_balances(account_id=db_account["id"])

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

        return all_balances

    except Exception as e:
        logger.error(f"Failed to get all balances: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get balances: {str(e)}"
        ) from e


@router.get("/balances/history")
async def get_historical_balances(
    date_from: str = Query(description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(description="End date (YYYY-MM-DD)"),
    account_id: Optional[str] = Query(
        default=None, description="Filter by specific account ID"
    ),
) -> List[dict]:
    """Get historical balance progression calculated from transaction history"""
    try:
        from leggen.utils.paths import path_manager

        db_path = path_manager.get_database_path()
        historical_balances = calculate_historical_balances(
            db_path, account_id=account_id, date_from=date_from, date_to=date_to
        )

        return historical_balances

    except Exception as e:
        logger.error(f"Failed to get historical balances: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get historical balances: {str(e)}"
        ) from e


@router.put("/accounts/{account_id}")
async def update_account_details(
    account_id: str,
    update_data: AccountUpdate,
    account_repo: Annotated[AccountRepository, Depends()],
) -> dict:
    """Update account details (currently only display_name)"""
    try:
        # Get current account details
        current_account = account_repo.get_account(account_id)

        if not current_account:
            raise HTTPException(
                status_code=404, detail=f"Account {account_id} not found"
            )

        # Prepare updated account data
        updated_account_data = current_account.copy()
        if update_data.display_name is not None:
            updated_account_data["display_name"] = update_data.display_name

        # Persist updated account details
        account_repo.persist(updated_account_data)

        return {"id": account_id, "display_name": update_data.display_name}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update account {account_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update account: {str(e)}"
        ) from e
