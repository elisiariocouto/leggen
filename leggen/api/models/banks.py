from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class BankInstitution(BaseModel):
    """Bank institution model"""

    id: str
    name: str
    bic: Optional[str] = None
    transaction_total_days: int
    countries: List[str]
    logo: Optional[str] = None


class BankConnectionRequest(BaseModel):
    """Request to connect to a bank"""

    institution_id: str
    redirect_url: Optional[str] = "http://localhost:8000/"


class BankRequisition(BaseModel):
    """Bank requisition/connection model"""

    id: str
    institution_id: str
    status: str
    status_display: Optional[str] = None
    created: datetime
    link: str
    accounts: List[str] = []

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class BankConnectionStatus(BaseModel):
    """Bank connection status response"""

    bank_id: str
    bank_name: str
    status: str
    status_display: str
    created_at: datetime
    requisition_id: str
    accounts_count: int

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
