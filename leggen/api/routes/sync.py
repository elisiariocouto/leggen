from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from loguru import logger

from leggen.api.models.common import APIResponse
from leggen.api.models.sync import SchedulerConfig, SyncRequest
from leggen.background.scheduler import scheduler
from leggen.services.sync_service import SyncService
from leggen.utils.config import config

router = APIRouter()
sync_service = SyncService()


@router.get("/sync/status", response_model=APIResponse)
async def get_sync_status() -> APIResponse:
    """Get current sync status"""
    try:
        status = await sync_service.get_sync_status()

        # Add scheduler information
        next_sync_time = scheduler.get_next_sync_time()
        if next_sync_time:
            status.next_sync = next_sync_time

        return APIResponse(
            success=True, data=status, message="Sync status retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get sync status: {str(e)}"
        ) from e


@router.post("/sync", response_model=APIResponse)
async def trigger_sync(
    background_tasks: BackgroundTasks, sync_request: Optional[SyncRequest] = None
) -> APIResponse:
    """Trigger a manual sync operation"""
    try:
        # Check if sync is already running
        status = await sync_service.get_sync_status()
        if status.is_running and not (sync_request and sync_request.force):
            return APIResponse(
                success=False,
                message="Sync is already running. Use 'force: true' to override.",
            )

        # Determine what to sync
        if sync_request and sync_request.account_ids:
            # Sync specific accounts in background
            background_tasks.add_task(
                sync_service.sync_specific_accounts,
                sync_request.account_ids,
                sync_request.force if sync_request else False,
                "api",  # trigger_type
            )
            message = (
                f"Started sync for {len(sync_request.account_ids)} specific accounts"
            )
        else:
            # Sync all accounts in background
            background_tasks.add_task(
                sync_service.sync_all_accounts,
                sync_request.force if sync_request else False,
                "api",  # trigger_type
            )
            message = "Started sync for all accounts"

        return APIResponse(
            success=True,
            data={
                "sync_started": True,
                "force": sync_request.force if sync_request else False,
            },
            message=message,
        )

    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger sync: {str(e)}"
        ) from e


@router.post("/sync/now", response_model=APIResponse)
async def sync_now(sync_request: Optional[SyncRequest] = None) -> APIResponse:
    """Run sync synchronously and return results (slower, for testing)"""
    try:
        if sync_request and sync_request.account_ids:
            result = await sync_service.sync_specific_accounts(
                sync_request.account_ids, sync_request.force, "api"
            )
        else:
            result = await sync_service.sync_all_accounts(
                sync_request.force if sync_request else False, "api"
            )

        return APIResponse(
            success=result.success,
            data=result,
            message="Sync completed"
            if result.success
            else f"Sync failed with {len(result.errors)} errors",
        )

    except Exception as e:
        logger.error(f"Failed to run sync: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to run sync: {str(e)}"
        ) from e


@router.get("/sync/scheduler", response_model=APIResponse)
async def get_scheduler_config() -> APIResponse:
    """Get current scheduler configuration"""
    try:
        scheduler_config = config.scheduler_config
        next_sync_time = scheduler.get_next_sync_time()

        response_data = {
            **scheduler_config,
            "next_scheduled_sync": next_sync_time.isoformat()
            if next_sync_time
            else None,
            "is_running": scheduler.scheduler.running
            if hasattr(scheduler, "scheduler")
            else False,
        }

        return APIResponse(
            success=True,
            data=response_data,
            message="Scheduler configuration retrieved successfully",
        )

    except Exception as e:
        logger.error(f"Failed to get scheduler config: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get scheduler config: {str(e)}"
        ) from e


@router.put("/sync/scheduler", response_model=APIResponse)
async def update_scheduler_config(scheduler_config: SchedulerConfig) -> APIResponse:
    """Update scheduler configuration"""
    try:
        # Validate cron expression if provided
        if scheduler_config.cron:
            try:
                cron_parts = scheduler_config.cron.split()
                if len(cron_parts) != 5:
                    raise ValueError(
                        "Cron expression must have 5 parts: minute hour day month day_of_week"
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid cron expression: {str(e)}"
                ) from e

        # Update configuration
        schedule_data = scheduler_config.dict(exclude_none=True)
        config.update_section("scheduler", {"sync": schedule_data})

        # Reschedule the job
        scheduler.reschedule_sync(schedule_data)

        return APIResponse(
            success=True,
            data=schedule_data,
            message="Scheduler configuration updated successfully",
        )

    except Exception as e:
        logger.error(f"Failed to update scheduler config: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update scheduler config: {str(e)}"
        ) from e


@router.post("/sync/scheduler/start", response_model=APIResponse)
async def start_scheduler() -> APIResponse:
    """Start the background scheduler"""
    try:
        if not scheduler.scheduler.running:
            scheduler.start()
            return APIResponse(success=True, message="Scheduler started successfully")
        else:
            return APIResponse(success=True, message="Scheduler is already running")

    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start scheduler: {str(e)}"
        ) from e


@router.post("/sync/scheduler/stop", response_model=APIResponse)
async def stop_scheduler() -> APIResponse:
    """Stop the background scheduler"""
    try:
        if scheduler.scheduler.running:
            scheduler.shutdown()
            return APIResponse(success=True, message="Scheduler stopped successfully")
        else:
            return APIResponse(success=True, message="Scheduler is already stopped")

    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to stop scheduler: {str(e)}"
        ) from e


@router.get("/sync/operations", response_model=APIResponse)
async def get_sync_operations(limit: int = 50, offset: int = 0) -> APIResponse:
    """Get sync operations history"""
    try:
        operations = await sync_service.database.get_sync_operations(
            limit=limit, offset=offset
        )

        return APIResponse(
            success=True,
            data={"operations": operations, "count": len(operations)},
            message="Sync operations retrieved successfully",
        )

    except Exception as e:
        logger.error(f"Failed to get sync operations: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get sync operations: {str(e)}"
        ) from e
