from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from loguru import logger

from leggen.api.models.sync import SchedulerConfig, SyncRequest, SyncResult, SyncStatus
from leggen.background.scheduler import scheduler
from leggen.services.sync_service import SyncService
from leggen.utils.config import config

router = APIRouter()
sync_service = SyncService()


@router.get("/sync/status")
async def get_sync_status() -> SyncStatus:
    """Get current sync status"""
    try:
        status = await sync_service.get_sync_status()

        # Add scheduler information
        next_sync_time = scheduler.get_next_sync_time()
        if next_sync_time:
            status.next_sync = next_sync_time

        return status

    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get sync status: {str(e)}"
        ) from e


@router.post("/sync")
async def trigger_sync(
    background_tasks: BackgroundTasks, sync_request: Optional[SyncRequest] = None
) -> dict:
    """Trigger a manual sync operation"""
    try:
        # Check if sync is already running
        status = await sync_service.get_sync_status()
        if status.is_running and not (sync_request and sync_request.force):
            raise HTTPException(
                status_code=409,
                detail="Sync is already running. Use 'force: true' to override.",
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
        else:
            # Sync all accounts in background
            background_tasks.add_task(
                sync_service.sync_all_accounts,
                sync_request.force if sync_request else False,
                "api",  # trigger_type
            )

        return {
            "sync_started": True,
            "force": sync_request.force if sync_request else False,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger sync: {str(e)}"
        ) from e


@router.post("/sync/now")
async def sync_now(sync_request: Optional[SyncRequest] = None) -> SyncResult:
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

        return result

    except Exception as e:
        logger.error(f"Failed to run sync: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to run sync: {str(e)}"
        ) from e


@router.get("/sync/scheduler")
async def get_scheduler_config() -> dict:
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

        return response_data

    except Exception as e:
        logger.error(f"Failed to get scheduler config: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get scheduler config: {str(e)}"
        ) from e


@router.put("/sync/scheduler")
async def update_scheduler_config(scheduler_config: SchedulerConfig) -> dict:
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

        return schedule_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update scheduler config: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update scheduler config: {str(e)}"
        ) from e


@router.post("/sync/scheduler/start")
async def start_scheduler() -> dict:
    """Start the background scheduler"""
    try:
        if not scheduler.scheduler.running:
            scheduler.start()
            return {"started": True}
        else:
            return {"started": False, "message": "Scheduler is already running"}

    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start scheduler: {str(e)}"
        ) from e


@router.post("/sync/scheduler/stop")
async def stop_scheduler() -> dict:
    """Stop the background scheduler"""
    try:
        if scheduler.scheduler.running:
            scheduler.shutdown()
            return {"stopped": True}
        else:
            return {"stopped": False, "message": "Scheduler is already stopped"}

    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to stop scheduler: {str(e)}"
        ) from e


@router.get("/sync/operations")
async def get_sync_operations(limit: int = 50, offset: int = 0) -> dict:
    """Get sync operations history"""
    try:
        operations = await sync_service.database.get_sync_operations(
            limit=limit, offset=offset
        )

        return {"operations": operations, "count": len(operations)}

    except Exception as e:
        logger.error(f"Failed to get sync operations: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get sync operations: {str(e)}"
        ) from e
