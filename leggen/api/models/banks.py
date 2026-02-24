from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BankInstitution(BaseModel):
    """Bank institution (ASPSP) model"""

    name: str
    country: str
    bic: Optional[str] = None
    logo: Optional[str] = None


class BankConnectionRequest(BaseModel):
    """Request to start bank authorization"""

    aspsp_name: str
    aspsp_country: str
    redirect_url: Optional[str] = None


class BankAuthResponse(BaseModel):
    """Response with authorization URL"""

    url: str


class BankCallbackRequest(BaseModel):
    """Request to exchange authorization code for a session"""

    code: str


class BankConnectionStatus(BaseModel):
    """Bank connection status response"""

    session_id: str
    aspsp_name: str
    aspsp_country: str
    accounts_count: int
    created_at: datetime
    valid_until: Optional[datetime] = None
    status: str
