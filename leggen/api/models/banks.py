from datetime import datetime

from pydantic import BaseModel


class BankInstitution(BaseModel):
    """Bank institution (ASPSP) model"""

    name: str
    country: str
    bic: str | None = None
    logo: str | None = None
    psu_types: list[str] = ["personal"]
    maximum_consent_validity: int | None = None


class BankConnectionRequest(BaseModel):
    """Request to start bank authorization"""

    aspsp_name: str
    aspsp_country: str
    redirect_url: str | None = None
    psu_type: str = "personal"


class BankAuthResponse(BaseModel):
    """Response with authorization URL"""

    url: str


class BankCallbackRequest(BaseModel):
    """Request to exchange authorization code for a session"""

    code: str
    state: str


class Country(BaseModel):
    """A supported country"""

    code: str
    name: str


class BankConnectionStatus(BaseModel):
    """Bank connection status response"""

    session_id: str
    aspsp_name: str
    aspsp_country: str
    accounts_count: int
    created_at: datetime
    valid_until: datetime | None = None
    status: str
    days_until_expiry: int | None = None
