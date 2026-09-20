from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from leggen.models.config import S3BackupConfig
from leggen.services.backup_service import BackupService
from leggen.services.notification_service import NotificationService
from leggen.services.sync_service import SyncService
from leggen.utils.config import config
from leggen.utils.paths import path_manager


class BackgroundScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.max_retries = 3
        self.retry_delay = 300  # 5 minutes
        self._sync_service: SyncService | None = None
        self._notification_service: NotificationService | None = None

    # Services are created lazily: this module's singleton is imported by
    # route modules and the CLI, and constructing the services reads the
    # config file and touches the database.
    @property
    def sync_service(self) -> SyncService:
        if self._sync_service is None:
            self._sync_service = SyncService()
        return self._sync_service

    @sync_service.setter
    def sync_service(self, value: SyncService) -> None:
        self._sync_service = value

    @property
    def notification_service(self) -> NotificationService:
        if self._notification_service is None:
            self._notification_service = NotificationService()
        return self._notification_service

    @notification_service.setter
    def notification_service(self, value: NotificationService) -> None:
        self._notification_service = value

    def start(self):
        """Start the scheduler and configure jobs based on configuration"""
        scheduler_config = config.scheduler_config

        # Parse schedule configuration. The scheduler must start even when a
        # configured cron is invalid, otherwise reschedule_sync() can never
        # recover (it only adds jobs to a running scheduler).
        sync_config = scheduler_config.get("sync", {})
        if not sync_config.get("enabled", True):
            logger.info("Sync scheduling is disabled in configuration")
        else:
            trigger = self._parse_cron_config(sync_config)
            if trigger:
                self.scheduler.add_job(
                    self._run_sync,
                    trigger,
                    id="daily_sync",
                    name="Scheduled sync of all transactions",
                    max_instances=1,
                )
            else:
                logger.error(
                    "Invalid sync schedule configuration; no sync job scheduled. "
                    "Fix it via PUT /api/v1/sync/schedule or the config file."
                )

        # The backup job is scheduled unconditionally (unless disabled) and
        # checks the live S3 config at run time, so enabling S3 backups via
        # PUT /api/v1/backup/settings takes effect without a restart.
        backup_config = scheduler_config.get("backup", {})
        if not backup_config.get("enabled", True):
            logger.info("Backup scheduling is disabled in configuration")
        else:
            trigger = self._parse_cron_config(
                backup_config, default_hour=4, default_minute=0
            )
            if trigger:
                self.scheduler.add_job(
                    self._run_backup,
                    trigger,
                    id="daily_backup",
                    name="Scheduled S3 database backup",
                    max_instances=1,
                )
            else:
                logger.error(
                    "Invalid backup schedule configuration; no backup job scheduled."
                )

        self.scheduler.start()
        logger.info(
            f"Background scheduler started with jobs: "
            f"{[job.id for job in self.scheduler.get_jobs()]}"
        )

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

    @staticmethod
    def _convert_day_of_week(day_of_week: str) -> str:
        """Convert a standard cron day-of-week field to APScheduler numbering.

        Standard cron uses 0/7=Sunday..6=Saturday; APScheduler uses
        0=Monday..6=Sunday. Numeric values, ranges, and steps are expanded and
        remapped; day names pass through unchanged (both use mon..sun).
        """

        def remap(value: str) -> int:
            std = int(value)
            if not 0 <= std <= 7:
                raise ValueError(f"day-of-week value out of range: {value}")
            return (std - 1) % 7

        converted = []
        for token in day_of_week.split(","):
            spec, _, step_str = token.partition("/")
            step = int(step_str) if step_str else 1
            if spec == "*":
                values = list(range(0, 7, step))
            elif "-" in spec:
                start, end = spec.split("-", 1)
                if not (start.isdigit() and end.isdigit()):
                    converted.append(token)  # named range, e.g. mon-fri
                    continue
                values = list(range(int(start), int(end) + 1, step))
            elif spec.isdigit():
                values = [int(spec)]
            else:
                converted.append(token)  # day name, e.g. sun
                continue
            converted.extend(str(v) for v in sorted({remap(str(v)) for v in values}))
        return ",".join(converted)

    def _parse_cron_config(
        self, schedule_config: dict, default_hour: int = 3, default_minute: int = 0
    ) -> CronTrigger | None:
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
                        day_of_week=self._convert_day_of_week(day_of_week)
                        if day_of_week != "*"
                        else None,
                    )
                else:
                    logger.error(f"Invalid cron expression: {schedule_config['cron']}")
                    return None
            except Exception as e:
                logger.error(f"Error parsing cron expression: {e}")
                return None
        else:
            # Use hour/minute configuration
            hour = schedule_config.get("hour", default_hour)
            minute = schedule_config.get("minute", default_minute)
            return CronTrigger(hour=hour, minute=minute)

    async def _run_sync(self, retry_count: int = 0):
        """Run sync with enhanced error handling and retry logic"""
        try:
            trigger_type = "retry" if retry_count > 0 else "scheduled"
            logger.info(f"Starting {trigger_type} sync job")
            await self.sync_service.sync_all_accounts(
                full_sync=False, trigger_type=trigger_type
            )
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

    async def _run_backup(self):
        """Run the scheduled S3 database backup.

        Reads the S3 configuration live on every run and silently skips when
        S3 backups are not configured or disabled, so the job can stay
        scheduled while settings change at runtime.
        """
        s3_settings = config.backup_config.get("s3", {})
        if not s3_settings.get("bucket_name"):
            logger.debug("Scheduled backup skipped: S3 backup is not configured")
            return
        if not s3_settings.get("enabled", True):
            logger.debug("Scheduled backup skipped: S3 backup is disabled")
            return

        try:
            s3_config = S3BackupConfig(**s3_settings)
            backup_service = BackupService(s3_config)
            logger.info("Starting scheduled database backup")
            success = await backup_service.backup_database(
                path_manager.get_database_path()
            )
            if success:
                logger.info("Scheduled database backup completed successfully")
            else:
                logger.error("Scheduled database backup failed")
        except Exception as e:
            logger.error(f"Scheduled database backup failed: {e}")

    def get_next_sync_time(self):
        """Get the next scheduled sync time"""
        job = self.scheduler.get_job("daily_sync")
        if job:
            return job.next_run_time
        return None


scheduler = BackgroundScheduler()
