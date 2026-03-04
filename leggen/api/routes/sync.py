from typing import Optional

from fastapi import APIRouter, HTTPException
from loguru import logger

from leggen.api.models.sync import (
    SyncRequest,
    SyncResult,
    SyncScheduleRequest,
    SyncScheduleResponse,
)
from leggen.background.scheduler import scheduler
from leggen.services.sync_service import SyncService
from leggen.utils.config import config

router = APIRouter()
sync_service = SyncService()


@router.post("/sync")
async def trigger_sync(sync_request: Optional[SyncRequest] = None) -> SyncResult:
    """Run sync synchronously and return results"""
    try:
        full_sync = sync_request.full_sync if sync_request else False
        result = await sync_service.sync_all_accounts(full_sync, "api")

        return result

    except Exception as e:
        logger.error(f"Failed to run sync: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to run sync: {str(e)}"
        ) from e


@router.get("/sync/schedule")
async def get_sync_schedule() -> SyncScheduleResponse:
    """Get current sync schedule configuration"""
    try:
        schedule_config = config.scheduler_config.get("sync", {})
        next_sync = scheduler.get_next_sync_time()

        return SyncScheduleResponse(
            enabled=schedule_config.get("enabled", True),
            hour=schedule_config.get("hour", 3),
            minute=schedule_config.get("minute", 0),
            cron=schedule_config.get("cron"),
            next_sync_time=next_sync.isoformat() if next_sync else None,
        )
    except Exception as e:
        logger.error(f"Failed to get sync schedule: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get sync schedule: {str(e)}"
        ) from e


@router.put("/sync/schedule")
async def update_sync_schedule(request: SyncScheduleRequest) -> SyncScheduleResponse:
    """Update sync schedule configuration"""
    try:
        sync_config: dict[str, object] = {
            "enabled": request.enabled,
            "hour": request.hour,
            "minute": request.minute,
        }
        if request.cron:
            sync_config["cron"] = request.cron

        config.update_section("scheduler", {"sync": sync_config})
        scheduler.reschedule_sync(sync_config)

        next_sync = scheduler.get_next_sync_time()

        return SyncScheduleResponse(
            enabled=request.enabled,
            hour=request.hour,
            minute=request.minute,
            cron=request.cron,
            next_sync_time=next_sync.isoformat() if next_sync else None,
        )
    except Exception as e:
        logger.error(f"Failed to update sync schedule: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update sync schedule: {str(e)}"
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
