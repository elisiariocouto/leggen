from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from leggen.services.notification_service import NotificationService
from leggen.services.sync_service import SyncService
from leggen.utils.config import config


class BackgroundScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.sync_service = SyncService()
        self.notification_service = NotificationService()
        self.max_retries = 3
        self.retry_delay = 300  # 5 minutes

    def start(self):
        """Start the scheduler and configure sync jobs based on configuration"""
        schedule_config = config.scheduler_config.get("sync", {})

        if not schedule_config.get("enabled", True):
            logger.info("Sync scheduling is disabled in configuration")
            self.scheduler.start()
            return

        # Parse schedule configuration
        trigger = self._parse_cron_config(schedule_config)
        if not trigger:
            return

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
            trigger = self._parse_cron_config(schedule_config)
            if not trigger:
                return

            self.scheduler.add_job(
                self._run_sync,
                trigger,
                id="daily_sync",
                name="Scheduled sync of all transactions",
                max_instances=1,
            )
            logger.info(f"Rescheduled sync job with: {trigger}")

    def _parse_cron_config(self, schedule_config: dict) -> CronTrigger:
        """Parse cron configuration and return CronTrigger"""
        if schedule_config.get("cron"):
            # Parse custom cron expression (e.g., "0 3 * * *" for daily at 3 AM)
            try:
                cron_parts = schedule_config["cron"].split()
                if len(cron_parts) == 5:
                    minute, hour, day, month, day_of_week = cron_parts
                    return CronTrigger(
                        minute=minute,
                        hour=hour,
                        day=day if day != "*" else None,
                        month=month if month != "*" else None,
                        day_of_week=day_of_week if day_of_week != "*" else None,
                    )
                else:
                    logger.error(f"Invalid cron expression: {schedule_config['cron']}")
                    return None
            except Exception as e:
                logger.error(f"Error parsing cron expression: {e}")
                return None
        else:
            # Use hour/minute configuration (default: 3:00 AM daily)
            hour = schedule_config.get("hour", 3)
            minute = schedule_config.get("minute", 0)
            return CronTrigger(hour=hour, minute=minute)

    async def _run_sync(self, retry_count: int = 0):
        """Run sync with enhanced error handling and retry logic"""
        try:
            trigger_type = "retry" if retry_count > 0 else "scheduled"
            logger.info(f"Starting {trigger_type} sync job")
            await self.sync_service.sync_all_accounts(trigger_type=trigger_type)
            logger.info(f"{trigger_type.capitalize()} sync job completed successfully")
        except Exception as e:
            trigger_type = "retry" if retry_count > 0 else "scheduled"
            logger.error(
                f"{trigger_type.capitalize()} sync job failed (attempt {retry_count + 1}/{self.max_retries}): {e}"
            )

            # Send notification about the failure
            try:
                await self.notification_service.send_sync_failure_notification(
                    {
                        "type": "sync_failure",
                        "error": str(e),
                        "retry_count": retry_count + 1,
                        "max_retries": self.max_retries,
                    }
                )
            except Exception as notification_error:
                logger.error(
                    f"Failed to send failure notification: {notification_error}"
                )

            # Implement retry logic for transient failures
            if retry_count < self.max_retries - 1:
                import datetime

                logger.info(f"Retrying sync job in {self.retry_delay} seconds...")
                # Schedule a retry
                retry_time = datetime.datetime.now() + datetime.timedelta(
                    seconds=self.retry_delay
                )
                self.scheduler.add_job(
                    self._run_sync,
                    "date",
                    args=[retry_count + 1],
                    id=f"sync_retry_{retry_count + 1}",
                    run_date=retry_time,
                )
            else:
                logger.error("Maximum retries exceeded for sync job")
                # Send final failure notification
                try:
                    await self.notification_service.send_sync_failure_notification(
                        {
                            "type": "sync_final_failure",
                            "error": str(e),
                            "retry_count": retry_count + 1,
                        }
                    )
                except Exception as notification_error:
                    logger.error(
                        f"Failed to send final failure notification: {notification_error}"
                    )

    def get_next_sync_time(self):
        """Get the next scheduled sync time"""
        job = self.scheduler.get_job("daily_sync")
        if job:
            return job.next_run_time
        return None


scheduler = BackgroundScheduler()
