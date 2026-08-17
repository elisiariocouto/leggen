"""API routes for the analytics dashboard."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from leggen.api.models.stats import (
    CashFlow,
    Merchants,
    NetWorth,
    RecurringPayment,
)
from leggen.repositories.balance_repository import BalanceRepository
from leggen.repositories.transaction_repository import TransactionRepository
from leggen.services import analytics_service

router = APIRouter()


@router.get("/analytics/cash-flow", response_model=CashFlow)
async def get_cash_flow(
    transaction_repo: Annotated[TransactionRepository, Depends()],
    date_from: str = Query(description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(description="End date (YYYY-MM-DD)"),
    account_id: str | None = Query(default=None, description="Filter by account ID"),
) -> dict:
    """Monthly income, expenses and cumulative net for the period."""
    return transaction_repo.get_cash_flow(date_from, date_to, account_id=account_id)


@router.get("/analytics/net-worth", response_model=NetWorth)
async def get_net_worth(
    balance_repo: Annotated[BalanceRepository, Depends()],
    date_from: str = Query(description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(description="End date (YYYY-MM-DD)"),
    account_id: str | None = Query(default=None, description="Filter by account ID"),
) -> dict:
    """Total balance over time, from recorded balance snapshots.

    Snapshots are written at sync time, so the series starts at the first sync
    and its resolution follows sync frequency.
    """
    return analytics_service.get_net_worth(
        balance_repo, date_from, date_to, account_id=account_id
    )


@router.get("/analytics/merchants", response_model=Merchants)
async def get_merchants(
    transaction_repo: Annotated[TransactionRepository, Depends()],
    date_from: str = Query(description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(description="End date (YYYY-MM-DD)"),
    account_id: str | None = Query(default=None, description="Filter by account ID"),
    limit: int = Query(default=15, ge=1, le=100, description="Merchants to return"),
) -> dict:
    """Top merchants by spend, compared with the preceding window."""
    return analytics_service.get_merchants(
        transaction_repo, date_from, date_to, account_id=account_id, limit=limit
    )


@router.get("/analytics/recurring", response_model=list[RecurringPayment])
async def get_recurring(
    transaction_repo: Annotated[TransactionRepository, Depends()],
    date_from: str = Query(description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(description="End date (YYYY-MM-DD)"),
    account_id: str | None = Query(default=None, description="Filter by account ID"),
) -> list[dict]:
    """Charges that repeat on a regular cadence.

    Detection is heuristic; each result carries its cadence, typical amount and
    last-seen date so a mis-grouped merchant is visible to the caller.
    """
    return analytics_service.get_recurring(
        transaction_repo, date_from, date_to, account_id=account_id
    )
