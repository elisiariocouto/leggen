"""Tests for the notifications a sync sends, on the real temporary database.

Only the EnableBanking boundary is stubbed; the notification service is
spied on, since the test config has no channel configured.
"""

from unittest.mock import patch

import pytest

from leggen.services.sync_service import SyncService
from tests.helpers import account_details, enablebanking_returns, seed_session

EXPIRED = {"valid_until": "2020-01-01T00:00:00+00:00", "aspsp_name": "EXPIRED_BANK"}


@pytest.mark.unit
class TestSyncNotifications:
    async def test_sync_failure_sends_notification(self, mock_db_path):
        seed_session(["account-1"], session_id="sess-123")
        sync_service = SyncService()

        with (
            enablebanking_returns(sync_service, details=Exception("API Error")),
            patch.object(
                sync_service.notifications, "send_sync_failure_notification"
            ) as notify,
        ):
            await sync_service.sync_all_accounts()

        notify.assert_called_once()
        payload = notify.call_args[0][0]
        assert payload["account_id"] == "account-1"
        assert "API Error" in payload["error"]
        assert payload["type"] == "account_sync_failure"

    async def test_expired_session_sends_notification(self, mock_db_path):
        seed_session([], session_id="sess-expired", **EXPIRED)
        sync_service = SyncService()

        with patch.object(
            sync_service.notifications, "send_expiry_notification"
        ) as notify:
            await sync_service.sync_all_accounts()

        notify.assert_called_once()
        payload = notify.call_args[0][0]
        assert payload["session_id"] == "sess-expired"
        assert payload["bank"] == "EXPIRED_BANK"
        assert payload["status"] == "expired"
        assert payload["days_left"] == 0

    async def test_multiple_failures_send_multiple_notifications(self, mock_db_path):
        seed_session(["account-1", "account-2"])
        sync_service = SyncService()

        with (
            enablebanking_returns(sync_service, details=Exception("API Error")),
            patch.object(
                sync_service.notifications, "send_sync_failure_notification"
            ) as notify,
        ):
            await sync_service.sync_all_accounts()

        assert notify.call_count == 2

    async def test_successful_sync_sends_no_failure_notification(self, mock_db_path):
        seed_session(["account-1"])
        sync_service = SyncService()

        with (
            enablebanking_returns(
                sync_service,
                details={"account-1": account_details("account-1", "TEST123")},
                balances={
                    "balances": [
                        {
                            "balance_amount": {"amount": "100", "currency": "EUR"},
                            "balance_type": "interimAvailable",
                        }
                    ]
                },
            ),
            patch.object(
                sync_service.notifications, "send_sync_failure_notification"
            ) as notify,
        ):
            result = await sync_service.sync_all_accounts()

        assert result.success is True
        assert result.accounts_processed == 1
        assert result.balances_updated == 1
        notify.assert_not_called()

    async def test_notification_failure_does_not_stop_sync(self, mock_db_path):
        seed_session(["account-1"])
        sync_service = SyncService()

        with (
            enablebanking_returns(sync_service, details=Exception("API Error")),
            patch.object(
                sync_service.notifications,
                "send_sync_failure_notification",
                side_effect=Exception("Notification Error"),
            ),
        ):
            result = await sync_service.sync_all_accounts()

        # The sync reports the account error; the notification error is only logged.
        assert result.success is False
        assert len(result.errors) == 1
        assert "API Error" in result.errors[0]

    async def test_expired_session_notifies_only_once(self, mock_db_path):
        """Expired sessions must not re-notify on every sync."""
        seed_session([], session_id="sess-expired-dedup", **EXPIRED)
        sync_service = SyncService()

        with patch.object(
            sync_service.notifications, "send_expiry_notification"
        ) as notify:
            await sync_service.sync_all_accounts()
            await sync_service.sync_all_accounts()

        notify.assert_called_once()
