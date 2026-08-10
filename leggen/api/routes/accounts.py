from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import ValidationError

from leggen.api.models.accounts import (
    AccountBalance,
    AccountDetails,
    AccountUpdate,
    Balance,
)
from leggen.repositories import AccountRepository, BalanceRepository
from leggen.services.data_processors import calculate_historical_balances
from leggen.utils.paths import path_manager

router = APIRouter()


@router.get("/accounts")
async def get_all_accounts(
    account_repo: Annotated[AccountRepository, Depends()],
    balance_repo: Annotated[BalanceRepository, Depends()],
) -> List[AccountDetails]:
    """Get all connected accounts from database"""
    balances_by_account = balance_repo.get_latest_balances_by_account()

    accounts = []
    for db_account in account_repo.get_accounts():
        try:
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
                    balances=[
                        AccountBalance(
                            amount=balance["amount"],
                            currency=balance["currency"],
                            balance_type=balance["type"],
                            last_change_date=balance.get("timestamp"),
                        )
                        for balance in balances_by_account.get(db_account["id"], [])
                    ],
                )
            )
        except (ValidationError, KeyError) as e:
            # One malformed legacy row must not empty the whole account list
            logger.warning(f"Skipping malformed account {db_account.get('id')}: {e}")

    return accounts


@router.get("/balances")
async def get_all_balances(
    account_repo: Annotated[AccountRepository, Depends()],
    balance_repo: Annotated[BalanceRepository, Depends()],
) -> List[Balance]:
    """Get all balances from all accounts in database"""
    balances_by_account = balance_repo.get_latest_balances_by_account()

    all_balances = []
    for db_account in account_repo.get_accounts():
        for balance in balances_by_account.get(db_account["id"], []):
            all_balances.append(
                Balance(
                    id=f"{db_account['id']}_{balance['type']}",
                    account_id=db_account["id"],
                    balance_amount=balance["amount"],
                    balance_type=balance["type"],
                    currency=balance["currency"],
                    reference_date=balance.get(
                        "timestamp", db_account.get("last_accessed")
                    ),
                    created_at=db_account.get("created"),
                    updated_at=db_account.get("last_accessed"),
                )
            )

    return all_balances


@router.get("/balances/history", response_model=List[Balance])
async def get_historical_balances(
    date_from: str = Query(description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(description="End date (YYYY-MM-DD)"),
    account_id: Optional[str] = Query(
        default=None, description="Filter by specific account ID"
    ),
) -> list[dict]:
    """Get historical balance progression calculated from transaction history"""
    # Returned as dicts; the response_model performs the single validation
    # pass (this is the largest payload the API serves).
    db_path = path_manager.get_database_path()
    return calculate_historical_balances(
        db_path, account_id=account_id, date_from=date_from, date_to=date_to
    )


@router.delete("/accounts/{account_id}")
async def delete_account(
    account_id: str,
    account_repo: Annotated[AccountRepository, Depends()],
    delete_data: bool = Query(
        default=True, description="Also delete transactions and balances"
    ),
) -> dict:
    """Delete a bank account and optionally its associated data"""
    deleted = account_repo.delete_account(account_id, delete_data)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    return {"deleted": account_id}


@router.put("/accounts/{account_id}")
async def update_account_details(
    account_id: str,
    update_data: AccountUpdate,
    account_repo: Annotated[AccountRepository, Depends()],
) -> dict:
    """Update account details (currently only display_name)"""
    current_account = account_repo.get_account(account_id)
    if not current_account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    updated_account_data = current_account.copy()
    if update_data.display_name is not None:
        updated_account_data["display_name"] = update_data.display_name

    account_repo.persist(updated_account_data)

    return {"id": account_id, "display_name": update_data.display_name}
