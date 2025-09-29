from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Query
from loguru import logger

from leggen.api.models.accounts import TransactionEnrichmentUpdate
from leggen.api.models.common import APIResponse
from leggen.services.database_service import DatabaseService

router = APIRouter()
database_service = DatabaseService()


@router.put("/transactions/enrichments", response_model=APIResponse)
async def update_transaction_enrichment(
    enrichment: Annotated[TransactionEnrichmentUpdate, Body()],
    account_id: str = Query(..., description="Account ID"),
    transaction_id: str = Query(..., description="Transaction ID"),
) -> APIResponse:
    """Update or create transaction enrichment"""
    try:
        # Validate that at least one field is provided
        if not any(
            [
                enrichment.clean_name,
                enrichment.category,
                enrichment.logo_url,
            ]
        ):
            raise HTTPException(
                status_code=400,
                detail="At least one enrichment field must be provided",
            )

        # Upsert enrichment
        result = await database_service.upsert_transaction_enrichment(
            account_id, transaction_id, enrichment.dict(exclude_none=True)
        )

        return APIResponse(
            success=True,
            data=result,
            message="Transaction enrichment updated successfully",
        )

    except ValueError as e:
        logger.error(f"Failed to update transaction enrichment: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to update transaction enrichment: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update enrichment: {str(e)}"
        ) from e


@router.delete("/transactions/enrichments", response_model=APIResponse)
async def delete_transaction_enrichment(
    account_id: str = Query(..., description="Account ID"),
    transaction_id: str = Query(..., description="Transaction ID"),
) -> APIResponse:
    """Delete transaction enrichment"""
    try:
        deleted = await database_service.delete_transaction_enrichment(
            account_id, transaction_id
        )

        if not deleted:
            raise HTTPException(
                status_code=404, detail="Transaction enrichment not found"
            )

        return APIResponse(
            success=True,
            data={"deleted": True},
            message="Transaction enrichment deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete transaction enrichment: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete enrichment: {str(e)}"
        ) from e


@router.get("/transactions/enrichments", response_model=APIResponse)
async def get_transaction_enrichment(
    account_id: str = Query(..., description="Account ID"),
    transaction_id: str = Query(..., description="Transaction ID"),
) -> APIResponse:
    """Get transaction enrichment"""
    try:
        enrichment = await database_service.get_transaction_enrichment(
            account_id, transaction_id
        )

        if not enrichment:
            raise HTTPException(
                status_code=404, detail="Transaction enrichment not found"
            )

        return APIResponse(
            success=True,
            data=enrichment,
            message="Transaction enrichment retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get transaction enrichment: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get enrichment: {str(e)}"
        ) from e
