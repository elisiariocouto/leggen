from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from leggen.api.models.common import PaginatedResponse
from leggen.api.models.sync import (
    SyncRequest,
    SyncResult,
    SyncScheduleRequest,
    SyncScheduleResponse,
)
from leggen.background.scheduler import scheduler
from leggen.repositories import AccountRepository, SyncRepository
from leggen.services.sync_service import SyncAlreadyRunningError
from leggen.utils.config import config

router = APIRouter()


@router.post("/sync")
async def trigger_sync(
    account_repo: Annotated[AccountRepository, Depends()],
    sync_request: Optional[SyncRequest] = None,
) -> SyncResult:
    """Run sync synchronously and return results"""
    try:
        full_sync = sync_request.full_sync if sync_request else False
        account_ids = sync_request.account_ids if sync_request else None

        if account_ids:
            known_ids = {
                a["id"] for a in account_repo.get_accounts(account_ids=account_ids)
            }
            unknown_ids = sorted(set(account_ids) - known_ids)
            if unknown_ids:
                raise HTTPException(
                    status_code=404,
                    detail=f"Unknown account IDs: {', '.join(unknown_ids)}",
                )

        result = await scheduler.sync_service.sync_all_accounts(
            full_sync, "api", account_ids=account_ids or None
        )

        return result

    except HTTPException:
        raise
    except SyncAlreadyRunningError as e:
        raise HTTPException(status_code=409, detail="Sync is already running.") from e
    except Exception as e:
        logger.error(f"Failed to run sync: {e}")
        raise HTTPException(status_code=500, detail="Failed to run sync.") from e


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
            status_code=500, detail="Failed to get sync schedule."
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
            status_code=500, detail="Failed to update sync schedule."
        ) from e


@router.get("/sync/operations")
async def get_sync_operations(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(default=50, ge=1, le=500, description="Items per page"),
) -> PaginatedResponse[dict]:
    """Get sync operations history"""
    try:
        sync_repo = SyncRepository()
        operations = sync_repo.get_operations(
            limit=per_page, offset=(page - 1) * per_page
        )
        total = sync_repo.get_operations_count()
        total_pages = (total + per_page - 1) // per_page

        return PaginatedResponse(
            data=operations,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    except Exception as e:
        logger.error(f"Failed to get sync operations: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get sync operations."
        ) from e
