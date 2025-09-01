from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel


class AccountBalance(BaseModel):
    """Account balance model"""
    amount: float
    currency: str
    balance_type: str
    last_change_date: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class AccountDetails(BaseModel):
    """Account details model"""
    id: str
    institution_id: str
    status: str
    iban: Optional[str] = None
    name: Optional[str] = None
    currency: Optional[str] = None
    created: datetime
    last_accessed: Optional[datetime] = None
    balances: List[AccountBalance] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class Transaction(BaseModel):
    """Transaction model"""
    internal_transaction_id: str
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
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TransactionSummary(BaseModel):
    """Transaction summary for lists"""
    internal_transaction_id: str
    date: datetime
    description: str
    amount: float
    currency: str
    status: str
    account_id: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }