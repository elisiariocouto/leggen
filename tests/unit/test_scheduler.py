"""Tests for background scheduler."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

from leggend.background.scheduler import BackgroundScheduler
from leggend.services.sync_service import SyncService


@pytest.mark.unit
class TestBackgroundScheduler:
    """Test background job scheduler."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for scheduler tests."""
        return {"sync": {"enabled": True, "hour": 3, "minute": 0, "cron": None}}

    @pytest.fixture
    def scheduler(self):
        """Create scheduler instance for testing."""
        with (
            patch("leggend.background.scheduler.SyncService"),
            patch("leggend.background.scheduler.config") as mock_config,
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
        with patch("leggend.config.config") as mock_config_obj:
            mock_config_obj.scheduler_config = mock_config

            # Mock the job that gets added
            mock_job = MagicMock()
            mock_job.id = "daily_sync"
            scheduler.scheduler.get_jobs.return_value = [mock_job]

            scheduler.start()

            # Verify scheduler.start() was called
            scheduler.scheduler.start.assert_called_once()
            # Verify add_job was called
            scheduler.scheduler.add_job.assert_called_once()

    def test_scheduler_start_disabled(self, scheduler):
        """Test scheduler behavior when sync is disabled."""
        disabled_config = {"sync": {"enabled": False}}

        with (
            patch.object(scheduler, "scheduler") as mock_scheduler,
            patch("leggend.background.scheduler.config") as mock_config_obj,
        ):
            mock_config_obj.scheduler_config = disabled_config
            mock_scheduler.running = False

            scheduler.start()

            # Verify scheduler.start() was called
            mock_scheduler.start.assert_called_once()
            # Verify add_job was NOT called for disabled sync
            mock_scheduler.add_job.assert_not_called()

    def test_scheduler_start_with_cron(self, scheduler):
        """Test starting scheduler with custom cron expression."""
        cron_config = {
            "sync": {
                "enabled": True,
                "cron": "0 6 * * 1-5",  # 6 AM on weekdays
            }
        }

        with patch("leggend.config.config") as mock_config_obj:
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
        invalid_cron_config = {"sync": {"enabled": True, "cron": "invalid cron"}}

        with (
            patch.object(scheduler, "scheduler") as mock_scheduler,
            patch("leggend.background.scheduler.config") as mock_config_obj,
        ):
            mock_config_obj.scheduler_config = invalid_cron_config
            mock_scheduler.running = False

            scheduler.start()

            # With invalid cron, scheduler.start() should not be called due to early return
            # and add_job should not be called
            mock_scheduler.start.assert_not_called()
            mock_scheduler.add_job.assert_not_called()

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
        """Test that sync jobs have max_instances=1."""
        with patch("leggend.config.config") as mock_config_obj:
            mock_config_obj.scheduler_config = mock_config
            scheduler.start()

            # Verify add_job was called with max_instances=1
            call_args = scheduler.scheduler.add_job.call_args
            assert call_args.kwargs["max_instances"] == 1
