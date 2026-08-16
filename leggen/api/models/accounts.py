from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AccountBalance(BaseModel):
    """Account balance model"""

    amount: float
    currency: str
    balance_type: str
    last_change_date: datetime | None = None


class AccountDetails(BaseModel):
    """Account details model"""

    id: str
    institution_id: str
    status: str
    iban: str | None = None
    name: str | None = None
    display_name: str | None = None
    currency: str | None = None
    logo: str | None = None
    created: datetime
    last_accessed: datetime | None = None
    balances: list[AccountBalance] = []


class AccountUpdate(BaseModel):
    """Account update model"""

    display_name: str | None = None


class Balance(BaseModel):
    """A single balance entry as returned by /balances and /balances/history"""

    id: str
    account_id: str
    # Nullable: history points derive from the balances table, whose amount
    # column legacy rows may hold as NULL.
    balance_amount: float | None = None
    balance_type: str
    currency: str | None = None
    reference_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Transaction(BaseModel):
    """Transaction model"""

    transaction_id: str  # NEW: stable bank-provided transaction ID
    internal_transaction_id: str | None = None
    institution_id: str
    iban: str | None = None
    account_id: str
    transaction_date: datetime
    description: str
    transaction_value: float
    transaction_currency: str
    transaction_status: str  # "booked" or "pending"
    raw_transaction: dict[str, Any]
    category_id: int | None = None
    category_name: str | None = None
    category_color: str | None = None


class TransactionSummary(BaseModel):
    """Transaction summary for lists"""

    transaction_id: str  # NEW: stable bank-provided transaction ID
    internal_transaction_id: str | None = None
    date: datetime
    description: str
    amount: float
    currency: str
    status: str
    account_id: str
    category_id: int | None = None
    category_name: str | None = None
    category_color: str | None = None
