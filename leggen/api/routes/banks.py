import httpx
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from leggen.api.models.banks import (
    BankConnectionRequest,
    BankConnectionStatus,
    BankInstitution,
    BankRequisition,
)
from leggen.api.models.common import APIResponse
from leggen.services.gocardless_service import GoCardlessService
from leggen.utils.gocardless import REQUISITION_STATUS

router = APIRouter()
gocardless_service = GoCardlessService()


@router.get("/banks/institutions", response_model=APIResponse)
async def get_bank_institutions(
    country: str = Query(default="PT", description="Country code (e.g., PT, ES, FR)"),
) -> APIResponse:
    """Get available bank institutions for a country"""
    try:
        institutions_response = await gocardless_service.get_institutions(country)
        # Handle both list and dict responses
        if isinstance(institutions_response, list):
            institutions_data = institutions_response
        else:
            institutions_data = institutions_response.get("results", [])

        institutions = [
            BankInstitution(
                id=inst["id"],
                name=inst["name"],
                bic=inst.get("bic"),
                transaction_total_days=int(inst["transaction_total_days"]),
                countries=inst["countries"],
                logo=inst.get("logo"),
            )
            for inst in institutions_data
        ]

        return APIResponse(
            success=True,
            data=institutions,
            message=f"Found {len(institutions)} institutions for {country}",
        )

    except Exception as e:
        logger.error(f"Failed to get institutions for {country}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get institutions: {str(e)}"
        ) from e


@router.post("/banks/connect", response_model=APIResponse)
async def connect_to_bank(request: BankConnectionRequest) -> APIResponse:
    """Create a connection to a bank (requisition)"""
    try:
        redirect_url = request.redirect_url or "http://localhost:8000/"
        requisition_data = await gocardless_service.create_requisition(
            request.institution_id, redirect_url
        )

        requisition = BankRequisition(
            id=requisition_data["id"],
            institution_id=requisition_data["institution_id"],
            status=requisition_data["status"],
            created=requisition_data["created"],
            link=requisition_data["link"],
            accounts=requisition_data.get("accounts", []),
        )

        return APIResponse(
            success=True,
            data=requisition,
            message="Bank connection created. Please visit the link to authorize.",
        )

    except Exception as e:
        logger.error(f"Failed to connect to bank {request.institution_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to connect to bank: {str(e)}"
        ) from e


@router.get("/banks/status", response_model=APIResponse)
async def get_bank_connections_status() -> APIResponse:
    """Get status of all bank connections"""
    try:
        requisitions_data = await gocardless_service.get_requisitions()

        connections = []
        for req in requisitions_data.get("results", []):
            status = req["status"]
            status_display = REQUISITION_STATUS.get(status, "UNKNOWN")

            connections.append(
                BankConnectionStatus(
                    bank_id=req["institution_id"],
                    bank_name=req[
                        "institution_id"
                    ],  # Could be enhanced with actual bank names
                    status=status,
                    status_display=status_display,
                    created_at=req["created"],
                    requisition_id=req["id"],
                    accounts_count=len(req.get("accounts", [])),
                )
            )

        return APIResponse(
            success=True,
            data=connections,
            message=f"Found {len(connections)} bank connections",
        )

    except Exception as e:
        logger.error(f"Failed to get bank connection status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get bank status: {str(e)}"
        ) from e


@router.delete("/banks/connections/{requisition_id}", response_model=APIResponse)
async def delete_bank_connection(requisition_id: str) -> APIResponse:
    """Delete a bank connection"""
    try:
        # Delete the requisition from GoCardless
        result = await gocardless_service.delete_requisition(requisition_id)

        # GoCardless returns different responses for successful deletes
        # We should check if the operation was actually successful
        logger.info(f"GoCardless delete response for {requisition_id}: {result}")

        return APIResponse(
            success=True,
            message=f"Bank connection {requisition_id} deleted successfully",
        )

    except httpx.HTTPStatusError as http_err:
        logger.error(
            f"HTTP error deleting bank connection {requisition_id}: {http_err}"
        )
        if http_err.response.status_code == 404:
            raise HTTPException(
                status_code=404, detail=f"Bank connection {requisition_id} not found"
            ) from http_err
        elif http_err.response.status_code == 400:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request to delete connection {requisition_id}",
            ) from http_err
        else:
            raise HTTPException(
                status_code=http_err.response.status_code,
                detail=f"GoCardless API error: {http_err}",
            ) from http_err
    except Exception as e:
        logger.error(f"Failed to delete bank connection {requisition_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete connection: {str(e)}"
        ) from e


@router.get("/banks/countries", response_model=APIResponse)
async def get_supported_countries() -> APIResponse:
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

    return APIResponse(
        success=True,
        data=countries,
        message="Supported countries retrieved successfully",
    )
