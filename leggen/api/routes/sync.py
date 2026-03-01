from typing import Optional

from fastapi import APIRouter, HTTPException
from loguru import logger

from leggen.api.models.sync import SyncRequest, SyncResult
from leggen.services.sync_service import SyncService

router = APIRouter()
sync_service = SyncService()


@router.post("/sync")
async def trigger_sync(sync_request: Optional[SyncRequest] = None) -> SyncResult:
    """Run sync synchronously and return results"""
    try:
        full_sync = sync_request.full_sync if sync_request else False

        if sync_request and sync_request.account_ids:
            result = await sync_service.sync_specific_accounts(
                sync_request.account_ids, full_sync, "api"
            )
        else:
            result = await sync_service.sync_all_accounts(full_sync, "api")

        return result

    except Exception as e:
        logger.error(f"Failed to run sync: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to run sync: {str(e)}"
        ) from e


@router.get("/sync/operations")
async def get_sync_operations(limit: int = 50, offset: int = 0) -> dict:
    """Get sync operations history"""
    try:
        from leggen.repositories import SyncRepository

        sync_repo = SyncRepository()
        operations = sync_repo.get_operations(limit=limit, offset=offset)

        return {"operations": operations, "count": len(operations)}

    except Exception as e:
        logger.error(f"Failed to get sync operations: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get sync operations: {str(e)}"
        ) from e
