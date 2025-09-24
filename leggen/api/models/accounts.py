from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AccountBalance(BaseModel):
    """Account balance model"""

    amount: float
    currency: str
    balance_type: str
    last_change_date: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class AccountDetails(BaseModel):
    """Account details model"""

    id: str
    institution_id: str
    status: str
    iban: Optional[str] = None
    name: Optional[str] = None
    display_name: Optional[str] = None
    currency: Optional[str] = None
    logo: Optional[str] = None
    created: datetime
    last_accessed: Optional[datetime] = None
    balances: List[AccountBalance] = []

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class AccountUpdate(BaseModel):
    """Account update model"""

    display_name: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class Transaction(BaseModel):
    """Transaction model"""

    transaction_id: str  # NEW: stable bank-provided transaction ID
    internal_transaction_id: Optional[str] = None  # OLD: unstable GoCardless ID
    institution_id: str
    iban: Optional[str] = None
    account_id: str
    transaction_date: datetime
    description: str
    transaction_value: float
    transaction_currency: str
    transaction_status: str  # "booked" or "pending"
    raw_transaction: Dict[str, Any]

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TransactionSummary(BaseModel):
    """Transaction summary for lists"""

    transaction_id: str  # NEW: stable bank-provided transaction ID
    internal_transaction_id: Optional[str] = None
    date: datetime
    description: str
    amount: float
    currency: str
    status: str
    account_id: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
