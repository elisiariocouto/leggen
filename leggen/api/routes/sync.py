from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from leggen.api.models.common import PaginatedResponse
from leggen.api.models.sync import (
    SyncOperation,
    SyncRequest,
    SyncResult,
    SyncScheduleRequest,
    SyncScheduleResponse,
)
from leggen.background.scheduler import scheduler
from leggen.repositories import AccountRepository, SyncRepository
from leggen.utils.config import config

router = APIRouter()


@router.post("/sync")
async def trigger_sync(
    account_repo: Annotated[AccountRepository, Depends()],
    sync_request: Optional[SyncRequest] = None,
) -> SyncResult:
    """Run sync synchronously and return results"""
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

    # SyncAlreadyRunningError is a ConflictError; the global handler
    # renders it as a 409 with its own code.
    return await scheduler.sync_service.sync_all_accounts(
        full_sync, "api", account_ids=account_ids or None
    )


@router.get("/sync/schedule")
async def get_sync_schedule() -> SyncScheduleResponse:
    """Get current sync schedule configuration"""
    schedule_config = config.scheduler_config.get("sync", {})
    next_sync = scheduler.get_next_sync_time()

    return SyncScheduleResponse(
        enabled=schedule_config.get("enabled", True),
        hour=schedule_config.get("hour", 3),
        minute=schedule_config.get("minute", 0),
        cron=schedule_config.get("cron"),
        next_sync_time=next_sync.isoformat() if next_sync else None,
    )


@router.put("/sync/schedule")
async def update_sync_schedule(request: SyncScheduleRequest) -> SyncScheduleResponse:
    """Update sync schedule configuration"""
    sync_config: dict[str, object] = {
        "enabled": request.enabled,
        "hour": request.hour,
        "minute": request.minute,
    }
    if request.cron:
        sync_config["cron"] = request.cron

    # Merge into the existing section: replacing it wholesale would reset
    # the backup schedule to defaults.
    scheduler_section = dict(config.scheduler_config)
    scheduler_section["sync"] = sync_config
    config.update_section("scheduler", scheduler_section)
    scheduler.reschedule_sync(sync_config)

    next_sync = scheduler.get_next_sync_time()

    return SyncScheduleResponse(
        enabled=request.enabled,
        hour=request.hour,
        minute=request.minute,
        cron=request.cron,
        next_sync_time=next_sync.isoformat() if next_sync else None,
    )


@router.get("/sync/operations")
async def get_sync_operations(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(default=50, ge=1, le=500, description="Items per page"),
) -> PaginatedResponse[SyncOperation]:
    """Get sync operations history"""
    sync_repo = SyncRepository()
    operations = sync_repo.get_operations(limit=per_page, offset=(page - 1) * per_page)
    total = sync_repo.get_operations_count()
    total_pages = (total + per_page - 1) // per_page

    return PaginatedResponse(
        data=[SyncOperation(**operation) for operation in operations],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
