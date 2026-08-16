from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from leggen.api.models.banks import (
    BankAuthResponse,
    BankCallbackRequest,
    BankConnectionRequest,
    BankConnectionStatus,
    BankInstitution,
    Country,
)
from leggen.repositories import SessionRepository
from leggen.services.enablebanking_service import (
    EnableBankingService,
    get_enablebanking_service,
)

router = APIRouter()


@router.get("/banks/institutions")
async def get_bank_institutions(
    enablebanking_service: Annotated[
        EnableBankingService, Depends(get_enablebanking_service)
    ],
    country: str = Query(default="PT", description="Country code (e.g., PT, ES, FR)"),
) -> list[BankInstitution]:
    """Get available bank institutions (ASPSPs) for a country"""
    aspsps = await enablebanking_service.get_aspsps(country)
    institutions = [
        BankInstitution(
            name=aspsp["name"],
            country=aspsp.get("country", country),
            bic=aspsp.get("bic"),
            logo=aspsp.get("logo"),
            psu_types=aspsp.get("psu_types", ["personal"]),
            maximum_consent_validity=aspsp.get("maximum_consent_validity"),
        )
        for aspsp in aspsps
    ]
    return sorted(institutions, key=lambda institution: institution.name.casefold())


@router.post("/banks/connect")
async def connect_to_bank(
    request: BankConnectionRequest,
    enablebanking_service: Annotated[
        EnableBankingService, Depends(get_enablebanking_service)
    ],
) -> BankAuthResponse:
    """Start bank authorization flow"""
    redirect_url = request.redirect_url or "http://localhost:8000/"

    # Ask for the longest consent the bank supports; start_auth falls back
    # to 90 days when the ASPSP doesn't report a maximum.
    maximum_consent_validity = None
    aspsps = await enablebanking_service.get_aspsps(request.aspsp_country)
    for aspsp in aspsps:
        if aspsp.get("name") == request.aspsp_name:
            validity = aspsp.get("maximum_consent_validity")
            if validity:
                maximum_consent_validity = int(validity)
            break

    result = await enablebanking_service.start_auth(
        aspsp_name=request.aspsp_name,
        aspsp_country=request.aspsp_country,
        redirect_url=redirect_url,
        psu_type=request.psu_type,
        maximum_consent_validity=maximum_consent_validity,
    )
    return BankAuthResponse(url=result["url"])


@router.post("/banks/callback")
async def bank_auth_callback(
    request: BankCallbackRequest,
    enablebanking_service: Annotated[
        EnableBankingService, Depends(get_enablebanking_service)
    ],
    session_repo: Annotated[SessionRepository, Depends()],
) -> dict:
    """Exchange authorization code for a session"""
    if not enablebanking_service.consume_auth_state(request.state):
        raise HTTPException(
            status_code=400,
            detail="Unknown or expired authorization state. Restart the bank connection flow.",
        )

    session_data = await enablebanking_service.create_session(request.code)

    # Store session locally
    aspsp = session_data.get("aspsp", {})
    access = session_data.get("access", {})
    session_record = {
        "session_id": session_data["session_id"],
        "aspsp_name": aspsp.get("name", ""),
        "aspsp_country": aspsp.get("country", ""),
        "accounts": session_data.get("accounts"),
        "valid_until": access.get("valid_until"),
        "created_at": datetime.now(UTC).isoformat(),
        "status": "active",
    }
    session_repo.persist(session_record)

    return session_record


@router.get("/banks/status")
async def get_bank_connections_status(
    session_repo: Annotated[SessionRepository, Depends()],
) -> list[BankConnectionStatus]:
    """Get status of all bank connections"""
    sessions = session_repo.get_sessions()
    connections = []
    now = datetime.now(UTC)

    for session in sessions:
        # Determine status based on valid_until
        status = session.get("status", "active")
        valid_until_str = session.get("valid_until")
        days_until_expiry = None
        if valid_until_str and status == "active":
            try:
                valid_until = datetime.fromisoformat(valid_until_str)
                # Timestamps stored without an offset are UTC
                if valid_until.tzinfo is None:
                    valid_until = valid_until.replace(tzinfo=UTC)
                days_until_expiry = (valid_until - now).days
                if valid_until < now:
                    status = "expired"
                    days_until_expiry = None
            except (ValueError, TypeError):
                pass

        accounts = session.get("accounts", []) or []

        connections.append(
            BankConnectionStatus(
                session_id=session["session_id"],
                aspsp_name=session["aspsp_name"],
                aspsp_country=session["aspsp_country"],
                accounts_count=len(accounts),
                created_at=session["created_at"],
                valid_until=valid_until_str,
                status=status,
                days_until_expiry=days_until_expiry,
            )
        )

    return connections


@router.delete("/banks/connections/{session_id}")
async def delete_bank_connection(
    session_id: str,
    session_repo: Annotated[SessionRepository, Depends()],
) -> dict:
    """Delete a bank connection session"""
    deleted = session_repo.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return {"deleted": session_id}


_COUNTRIES = [
    Country(code="AT", name="Austria"),
    Country(code="BE", name="Belgium"),
    Country(code="BG", name="Bulgaria"),
    Country(code="HR", name="Croatia"),
    Country(code="CY", name="Cyprus"),
    Country(code="CZ", name="Czech Republic"),
    Country(code="DK", name="Denmark"),
    Country(code="EE", name="Estonia"),
    Country(code="FI", name="Finland"),
    Country(code="FR", name="France"),
    Country(code="DE", name="Germany"),
    Country(code="GR", name="Greece"),
    Country(code="HU", name="Hungary"),
    Country(code="IS", name="Iceland"),
    Country(code="IE", name="Ireland"),
    Country(code="IT", name="Italy"),
    Country(code="LV", name="Latvia"),
    Country(code="LI", name="Liechtenstein"),
    Country(code="LT", name="Lithuania"),
    Country(code="LU", name="Luxembourg"),
    Country(code="MT", name="Malta"),
    Country(code="NL", name="Netherlands"),
    Country(code="NO", name="Norway"),
    Country(code="PL", name="Poland"),
    Country(code="PT", name="Portugal"),
    Country(code="RO", name="Romania"),
    Country(code="SK", name="Slovakia"),
    Country(code="SI", name="Slovenia"),
    Country(code="ES", name="Spain"),
    Country(code="SE", name="Sweden"),
    Country(code="GB", name="United Kingdom"),
]


@router.get("/banks/countries")
async def get_supported_countries() -> list[Country]:
    """Get list of supported countries"""
    return _COUNTRIES
