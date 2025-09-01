from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from leggend.config import config
from leggend.services.sync_service import SyncService


class BackgroundScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.sync_service = SyncService()

    def start(self):
        """Start the scheduler and configure sync jobs based on configuration"""
        schedule_config = config.scheduler_config.get("sync", {})
        
        if not schedule_config.get("enabled", True):
            logger.info("Sync scheduling is disabled in configuration")
            self.scheduler.start()
            return

        # Use custom cron expression if provided, otherwise use hour/minute
        if schedule_config.get("cron"):
            # Parse custom cron expression (e.g., "0 3 * * *" for daily at 3 AM)
            try:
                cron_parts = schedule_config["cron"].split()
                if len(cron_parts) == 5:
                    minute, hour, day, month, day_of_week = cron_parts
                    trigger = CronTrigger(
                        minute=minute,
                        hour=hour,
                        day=day if day != "*" else None,
                        month=month if month != "*" else None,
                        day_of_week=day_of_week if day_of_week != "*" else None,
                    )
                else:
                    logger.error(f"Invalid cron expression: {schedule_config['cron']}")
                    return
            except Exception as e:
                logger.error(f"Error parsing cron expression: {e}")
                return
        else:
            # Use hour/minute configuration (default: 3:00 AM daily)
            hour = schedule_config.get("hour", 3)
            minute = schedule_config.get("minute", 0)
            trigger = CronTrigger(hour=hour, minute=minute)

        self.scheduler.add_job(
            self._run_sync,
            trigger,
            id="daily_sync",
            name="Scheduled sync of all transactions",
            max_instances=1,
        )
        
        self.scheduler.start()
        logger.info(f"Background scheduler started with sync job: {trigger}")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Background scheduler shutdown")

    def reschedule_sync(self, schedule_config: dict):
        """Reschedule the sync job with new configuration"""
        if self.scheduler.running:
            try:
                self.scheduler.remove_job("daily_sync")
                logger.info("Removed existing sync job")
            except Exception:
                pass  # Job might not exist

            if not schedule_config.get("enabled", True):
                logger.info("Sync scheduling disabled")
                return

            # Configure new schedule
            if schedule_config.get("cron"):
                try:
                    cron_parts = schedule_config["cron"].split()
                    if len(cron_parts) == 5:
                        minute, hour, day, month, day_of_week = cron_parts
                        trigger = CronTrigger(
                            minute=minute,
                            hour=hour,
                            day=day if day != "*" else None,
                            month=month if month != "*" else None,
                            day_of_week=day_of_week if day_of_week != "*" else None,
                        )
                    else:
                        logger.error(f"Invalid cron expression: {schedule_config['cron']}")
                        return
                except Exception as e:
                    logger.error(f"Error parsing cron expression: {e}")
                    return
            else:
                hour = schedule_config.get("hour", 3)
                minute = schedule_config.get("minute", 0)
                trigger = CronTrigger(hour=hour, minute=minute)

            self.scheduler.add_job(
                self._run_sync,
                trigger,
                id="daily_sync",
                name="Scheduled sync of all transactions",
                max_instances=1,
            )
            logger.info(f"Rescheduled sync job with: {trigger}")

    async def _run_sync(self):
        try:
            logger.info("Starting scheduled sync job")
            await self.sync_service.sync_all_accounts()
            logger.info("Scheduled sync job completed successfully")
        except Exception as e:
            logger.error(f"Scheduled sync job failed: {e}")

    def get_next_sync_time(self):
        """Get the next scheduled sync time"""
        job = self.scheduler.get_job("daily_sync")
        if job:
            return job.next_run_time
        return None


scheduler = BackgroundScheduler()