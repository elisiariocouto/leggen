"""Tests for background scheduler."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from leggen.background.scheduler import BackgroundScheduler


@pytest.mark.unit
class TestBackgroundScheduler:
    """Test background job scheduler."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for scheduler tests."""
        return {
            "sync": {"enabled": True, "hour": 3, "minute": 0, "cron": None},
            "backup": {"enabled": True, "hour": 4, "minute": 0, "cron": None},
        }

    @pytest.fixture
    def scheduler(self):
        """Create scheduler instance for testing."""
        with (
            patch("leggen.background.scheduler.SyncService"),
            patch("leggen.background.scheduler.config") as mock_config,
        ):
            mock_config.scheduler_config = {
                "sync": {"enabled": True, "hour": 3, "minute": 0}
            }

            # Create scheduler and replace its AsyncIO scheduler with a mock
            scheduler = BackgroundScheduler()
            mock_scheduler = MagicMock()
            mock_scheduler.running = False
            mock_scheduler.get_jobs.return_value = []
            scheduler.scheduler = mock_scheduler
            return scheduler

    def test_scheduler_start_default_config(self, scheduler, mock_config):
        """Test starting scheduler with default configuration."""
        with patch("leggen.background.scheduler.config") as mock_config_obj:
            mock_config_obj.scheduler_config = mock_config

            scheduler.start()

            # Verify scheduler.start() was called
            scheduler.scheduler.start.assert_called_once()
            # Both the sync and backup jobs are scheduled
            job_ids = {
                call.kwargs["id"] for call in scheduler.scheduler.add_job.call_args_list
            }
            assert job_ids == {"daily_sync", "daily_backup"}

    def test_scheduler_start_disabled(self, scheduler):
        """Test scheduler behavior when sync and backup are disabled."""
        disabled_config = {"sync": {"enabled": False}, "backup": {"enabled": False}}

        with (
            patch.object(scheduler, "scheduler") as mock_scheduler,
            patch("leggen.background.scheduler.config") as mock_config_obj,
        ):
            mock_config_obj.scheduler_config = disabled_config
            mock_scheduler.running = False

            scheduler.start()

            # Verify scheduler.start() was called
            mock_scheduler.start.assert_called_once()
            # Verify add_job was NOT called for disabled jobs
            mock_scheduler.add_job.assert_not_called()

    def test_scheduler_start_with_cron(self, scheduler):
        """Test starting scheduler with custom cron expression."""
        cron_config = {
            "sync": {
                "enabled": True,
                "cron": "0 6 * * 1-5",  # 6 AM on weekdays
            },
            "backup": {"enabled": False},
        }

        with patch("leggen.background.scheduler.config") as mock_config_obj:
            mock_config_obj.scheduler_config = cron_config

            scheduler.start()

            # Verify scheduler.start() and add_job were called
            scheduler.scheduler.start.assert_called_once()
            scheduler.scheduler.add_job.assert_called_once()
            # Verify job was added with correct ID
            call_args = scheduler.scheduler.add_job.call_args
            assert call_args.kwargs["id"] == "daily_sync"

    def test_scheduler_start_invalid_cron(self, scheduler):
        """Test handling of invalid cron expressions."""
        invalid_cron_config = {
            "sync": {"enabled": True, "cron": "invalid cron"},
            "backup": {"enabled": True, "cron": "invalid cron"},
        }

        with (
            patch.object(scheduler, "scheduler") as mock_scheduler,
            patch("leggen.background.scheduler.config") as mock_config_obj,
        ):
            mock_config_obj.scheduler_config = invalid_cron_config
            mock_scheduler.running = False

            scheduler.start()

            # With invalid cron, no job is scheduled but the scheduler still
            # starts so a later reschedule_sync() can recover
            mock_scheduler.start.assert_called_once()
            mock_scheduler.add_job.assert_not_called()

    def test_scheduler_backup_job_scheduled_by_default(self, scheduler):
        """The backup job is scheduled even without a [scheduler.backup] section."""
        with patch("leggen.background.scheduler.config") as mock_config_obj:
            mock_config_obj.scheduler_config = {"sync": {"enabled": False}}

            scheduler.start()

            scheduler.scheduler.add_job.assert_called_once()
            assert scheduler.scheduler.add_job.call_args.kwargs["id"] == "daily_backup"

    def test_convert_day_of_week(self):
        """Standard cron day-of-week (0=Sunday) maps to APScheduler (0=Monday)."""
        convert = BackgroundScheduler._convert_day_of_week

        assert convert("0") == "6"  # Sunday
        assert convert("7") == "6"  # Sunday (alternate form)
        assert convert("1") == "0"  # Monday
        assert convert("1-5") == "0,1,2,3,4"  # weekdays
        assert convert("0,3") == "6,2"
        assert convert("*/2") == "1,3,5,6"  # Sun,Tue,Thu,Sat
        assert convert("mon-fri") == "mon-fri"  # names pass through
        assert convert("sun") == "sun"

    def test_scheduler_shutdown(self, scheduler):
        """Test scheduler shutdown."""
        scheduler.scheduler.running = True

        scheduler.shutdown()

        scheduler.scheduler.shutdown.assert_called_once()

    def test_reschedule_sync(self, scheduler, mock_config):
        """Test rescheduling sync job."""
        scheduler.scheduler.running = True

        # Reschedule with new config
        new_config = {"enabled": True, "hour": 6, "minute": 30}

        scheduler.reschedule_sync(new_config)

        # Verify remove_job and add_job were called
        scheduler.scheduler.remove_job.assert_called_once_with("daily_sync")
        scheduler.scheduler.add_job.assert_called_once()

    def test_reschedule_sync_disable(self, scheduler, mock_config):
        """Test disabling sync via reschedule."""
        scheduler.scheduler.running = True

        # Disable sync
        disabled_config = {"enabled": False}
        scheduler.reschedule_sync(disabled_config)

        # Job should be removed but not re-added
        scheduler.scheduler.remove_job.assert_called_once_with("daily_sync")
        scheduler.scheduler.add_job.assert_not_called()

    def test_get_next_sync_time(self, scheduler, mock_config):
        """Test getting next scheduled sync time."""
        mock_job = MagicMock()
        mock_job.next_run_time = datetime(2025, 9, 2, 3, 0)
        scheduler.scheduler.get_job.return_value = mock_job

        next_time = scheduler.get_next_sync_time()

        assert next_time is not None
        assert isinstance(next_time, datetime)
        scheduler.scheduler.get_job.assert_called_once_with("daily_sync")

    def test_get_next_sync_time_no_job(self, scheduler):
        """Test getting next sync time when no job is scheduled."""
        scheduler.scheduler.get_job.return_value = None

        next_time = scheduler.get_next_sync_time()

        assert next_time is None
        scheduler.scheduler.get_job.assert_called_once_with("daily_sync")

    @pytest.mark.asyncio
    async def test_run_sync_success(self, scheduler):
        """Test successful sync job execution."""
        mock_sync_service = AsyncMock()
        scheduler.sync_service = mock_sync_service

        await scheduler._run_sync()

        mock_sync_service.sync_all_accounts.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_sync_failure(self, scheduler):
        """Test sync job execution with failure."""
        mock_sync_service = AsyncMock()
        mock_sync_service.sync_all_accounts.side_effect = Exception("Sync failed")
        scheduler.sync_service = mock_sync_service

        # Should not raise exception, just log error
        await scheduler._run_sync()

        mock_sync_service.sync_all_accounts.assert_called_once()

    def test_scheduler_job_max_instances(self, scheduler, mock_config):
        """Test that scheduled jobs have max_instances=1."""
        with patch("leggen.background.scheduler.config") as mock_config_obj:
            mock_config_obj.scheduler_config = mock_config
            scheduler.start()

            # Verify every job was added with max_instances=1
            assert scheduler.scheduler.add_job.call_args_list
            for call in scheduler.scheduler.add_job.call_args_list:
                assert call.kwargs["max_instances"] == 1

    @pytest.mark.asyncio
    async def test_run_backup_success(self, scheduler):
        """A scheduled backup runs against the live S3 configuration."""
        s3_settings = {
            "access_key_id": "key",
            "secret_access_key": "secret",
            "bucket_name": "bucket",
            "enabled": True,
        }

        with (
            patch("leggen.background.scheduler.config") as mock_config_obj,
            patch("leggen.background.scheduler.BackupService") as mock_service_cls,
        ):
            mock_config_obj.backup_config = {"s3": s3_settings}
            mock_service = mock_service_cls.return_value
            mock_service.backup_database = AsyncMock(return_value=True)

            await scheduler._run_backup()

            s3_config = mock_service_cls.call_args.args[0]
            assert s3_config.bucket_name == "bucket"
            mock_service.backup_database.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_backup_skips_when_unconfigured_or_disabled(self, scheduler):
        """The backup job no-ops when S3 is unconfigured or disabled."""
        disabled_s3 = {
            "access_key_id": "key",
            "secret_access_key": "secret",
            "bucket_name": "bucket",
            "enabled": False,
        }

        for backup_config in [{}, {"s3": {}}, {"s3": disabled_s3}]:
            with (
                patch("leggen.background.scheduler.config") as mock_config_obj,
                patch("leggen.background.scheduler.BackupService") as mock_service_cls,
            ):
                mock_config_obj.backup_config = backup_config

                await scheduler._run_backup()

                mock_service_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_backup_failure_does_not_raise(self, scheduler):
        """A failed scheduled backup logs the error instead of raising."""
        s3_settings = {
            "access_key_id": "key",
            "secret_access_key": "secret",
            "bucket_name": "bucket",
            "enabled": True,
        }

        with (
            patch("leggen.background.scheduler.config") as mock_config_obj,
            patch("leggen.background.scheduler.BackupService") as mock_service_cls,
        ):
            mock_config_obj.backup_config = {"s3": s3_settings}
            mock_service = mock_service_cls.return_value
            mock_service.backup_database = AsyncMock(side_effect=Exception("S3 down"))

            await scheduler._run_backup()

            mock_service.backup_database.assert_called_once()
