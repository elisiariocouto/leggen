from typing import Annotated

from fastapi import APIRouter, Depends, Query
from loguru import logger
from pydantic import ValidationError

from leggen.api.models.accounts import (
    AccountBalance,
    AccountDetails,
    AccountUpdate,
    Balance,
)
from leggen.errors import NotFoundError
from leggen.repositories import AccountRepository, BalanceRepository

router = APIRouter()


@router.get("/accounts")
async def get_all_accounts(
    account_repo: Annotated[AccountRepository, Depends()],
    balance_repo: Annotated[BalanceRepository, Depends()],
) -> list[AccountDetails]:
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
) -> list[Balance]:
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


@router.delete("/accounts/{account_id}", status_code=204)
async def delete_account(
    account_id: str,
    account_repo: Annotated[AccountRepository, Depends()],
    delete_data: bool = Query(
        default=True, description="Also delete transactions and balances"
    ),
) -> None:
    """Delete a bank account and optionally its associated data"""
    deleted = account_repo.delete_account(account_id, delete_data)
    if not deleted:
        raise NotFoundError(f"Account {account_id} not found")


@router.put("/accounts/{account_id}", status_code=204)
async def update_account_details(
    account_id: str,
    update_data: AccountUpdate,
    account_repo: Annotated[AccountRepository, Depends()],
) -> None:
    """Update account details (currently only display_name)"""
    current_account = account_repo.get_account(account_id)
    if not current_account:
        raise NotFoundError(f"Account {account_id} not found")

    updated_account_data = current_account.copy()
    if update_data.display_name is not None:
        updated_account_data["display_name"] = update_data.display_name

    account_repo.persist(updated_account_data)
