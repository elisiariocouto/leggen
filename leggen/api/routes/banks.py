from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from leggen.api.dependencies import EnableBanking, SessionRepo
from leggen.api.models.banks import (
    BankAuthResponse,
    BankCallbackRequest,
    BankConnectionRequest,
    BankConnectionStatus,
    BankInstitution,
)

router = APIRouter()


@router.get("/banks/institutions")
async def get_bank_institutions(
    enablebanking_service: EnableBanking,
    country: str = Query(default="PT", description="Country code (e.g., PT, ES, FR)"),
) -> list[BankInstitution]:
    """Get available bank institutions (ASPSPs) for a country"""
    try:
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
    except Exception as e:
        logger.error(f"Failed to get institutions for {country}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get institutions: {str(e)}"
        ) from e


@router.post("/banks/connect")
async def connect_to_bank(
    request: BankConnectionRequest,
    enablebanking_service: EnableBanking,
) -> BankAuthResponse:
    """Start bank authorization flow"""
    try:
        redirect_url = request.redirect_url or "http://localhost:8000/"
        result = await enablebanking_service.start_auth(
            aspsp_name=request.aspsp_name,
            aspsp_country=request.aspsp_country,
            redirect_url=redirect_url,
            psu_type=request.psu_type,
        )
        return BankAuthResponse(url=result["url"])
    except Exception as e:
        logger.error(
            f"Failed to start auth for {request.aspsp_name} ({request.aspsp_country}): {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to connect to bank: {str(e)}"
        ) from e


@router.post("/banks/callback")
async def bank_auth_callback(
    request: BankCallbackRequest,
    enablebanking_service: EnableBanking,
    session_repo: SessionRepo,
) -> dict:
    """Exchange authorization code for a session"""
    try:
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
            "created_at": datetime.now().isoformat(),
            "status": "active",
        }
        session_repo.persist(session_record)

        return session_record
    except Exception as e:
        logger.error(f"Failed to exchange auth code: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create session: {str(e)}"
        ) from e


@router.get("/banks/status")
async def get_bank_connections_status(
    session_repo: SessionRepo,
) -> list[BankConnectionStatus]:
    """Get status of all bank connections"""
    try:
        sessions = session_repo.get_sessions()
        connections = []
        now = datetime.now()

        for session in sessions:
            # Determine status based on valid_until
            status = session.get("status", "active")
            valid_until_str = session.get("valid_until")
            if valid_until_str and status == "active":
                try:
                    valid_until = datetime.fromisoformat(valid_until_str)
                    if valid_until < now:
                        status = "expired"
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
                )
            )

        return connections
    except Exception as e:
        logger.error(f"Failed to get bank connection status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get bank status: {str(e)}"
        ) from e


@router.delete("/banks/connections/{session_id}")
async def delete_bank_connection(
    session_id: str,
    session_repo: SessionRepo,
) -> dict:
    """Delete a bank connection session"""
    deleted = session_repo.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return {"deleted": session_id}


@router.get("/banks/countries")
async def get_supported_countries() -> list[dict]:
    """Get list of supported countries"""
    countries = [
        {"code": "AT", "name": "Austria"},
        {"code": "BE", "name": "Belgium"},
        {"code": "BG", "name": "Bulgaria"},
        {"code": "HR", "name": "Croatia"},
        {"code": "CY", "name": "Cyprus"},
        {"code": "CZ", "name": "Czech Republic"},
        {"code": "DK", "name": "Denmark"},
        {"code": "EE", "name": "Estonia"},
        {"code": "FI", "name": "Finland"},
        {"code": "FR", "name": "France"},
        {"code": "DE", "name": "Germany"},
        {"code": "GR", "name": "Greece"},
        {"code": "HU", "name": "Hungary"},
        {"code": "IS", "name": "Iceland"},
        {"code": "IE", "name": "Ireland"},
        {"code": "IT", "name": "Italy"},
        {"code": "LV", "name": "Latvia"},
        {"code": "LI", "name": "Liechtenstein"},
        {"code": "LT", "name": "Lithuania"},
        {"code": "LU", "name": "Luxembourg"},
        {"code": "MT", "name": "Malta"},
        {"code": "NL", "name": "Netherlands"},
        {"code": "NO", "name": "Norway"},
        {"code": "PL", "name": "Poland"},
        {"code": "PT", "name": "Portugal"},
        {"code": "RO", "name": "Romania"},
        {"code": "SK", "name": "Slovakia"},
        {"code": "SI", "name": "Slovenia"},
        {"code": "ES", "name": "Spain"},
        {"code": "SE", "name": "Sweden"},
        {"code": "GB", "name": "United Kingdom"},
    ]

    return countries
