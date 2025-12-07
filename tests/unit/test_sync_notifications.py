"""Tests for sync service notification functionality."""

from unittest.mock import patch

import pytest

from leggen.services.sync_service import SyncService


@pytest.mark.unit
class TestSyncNotifications:
    """Test sync service notification functionality."""

    @pytest.mark.asyncio
    async def test_sync_failure_sends_notification(self):
        """Test that sync failures trigger notifications."""
        sync_service = SyncService()

        # Mock the dependencies
        with (
            patch.object(
                sync_service.gocardless, "get_requisitions"
            ) as mock_get_requisitions,
            patch.object(
                sync_service.gocardless, "get_account_details"
            ) as mock_get_details,
            patch.object(
                sync_service.notifications, "send_sync_failure_notification"
            ) as mock_send_notification,
            patch.object(
                sync_service.database, "persist_sync_operation", return_value=1
            ),
        ):
            # Setup: One requisition with one account that will fail
            mock_get_requisitions.return_value = {
                "results": [
                    {
                        "id": "req-123",
                        "institution_id": "TEST_BANK",
                        "status": "LN",
                        "accounts": ["account-1"],
                    }
                ]
            }

            # Make account details fail
            mock_get_details.side_effect = Exception("API Error")

            # Execute: Run sync which should fail for the account
            await sync_service.sync_all_accounts()

            # Assert: Notification should be sent for the failed account
            mock_send_notification.assert_called_once()
            call_args = mock_send_notification.call_args[0][0]
            assert call_args["account_id"] == "account-1"
            assert "API Error" in call_args["error"]
            assert call_args["type"] == "account_sync_failure"

    @pytest.mark.asyncio
    async def test_expired_requisition_sends_notification(self):
        """Test that expired requisitions trigger expiry notifications."""
        sync_service = SyncService()

        # Mock the dependencies
        with (
            patch.object(
                sync_service.gocardless, "get_requisitions"
            ) as mock_get_requisitions,
            patch.object(
                sync_service.notifications, "send_expiry_notification"
            ) as mock_send_expiry,
            patch.object(
                sync_service.database, "persist_sync_operation", return_value=1
            ),
        ):
            # Setup: One expired requisition
            mock_get_requisitions.return_value = {
                "results": [
                    {
                        "id": "req-expired",
                        "institution_id": "EXPIRED_BANK",
                        "status": "EX",
                        "accounts": [],
                    }
                ]
            }

            # Execute: Run sync
            await sync_service.sync_all_accounts()

            # Assert: Expiry notification should be sent
            mock_send_expiry.assert_called_once()
            call_args = mock_send_expiry.call_args[0][0]
            assert call_args["requisition_id"] == "req-expired"
            assert call_args["bank"] == "EXPIRED_BANK"
            assert call_args["status"] == "expired"
            assert call_args["days_left"] == 0

    @pytest.mark.asyncio
    async def test_multiple_failures_send_multiple_notifications(self):
        """Test that multiple account failures send multiple notifications."""
        sync_service = SyncService()

        # Mock the dependencies
        with (
            patch.object(
                sync_service.gocardless, "get_requisitions"
            ) as mock_get_requisitions,
            patch.object(
                sync_service.gocardless, "get_account_details"
            ) as mock_get_details,
            patch.object(
                sync_service.notifications, "send_sync_failure_notification"
            ) as mock_send_notification,
            patch.object(
                sync_service.database, "persist_sync_operation", return_value=1
            ),
        ):
            # Setup: One requisition with two accounts that will fail
            mock_get_requisitions.return_value = {
                "results": [
                    {
                        "id": "req-123",
                        "institution_id": "TEST_BANK",
                        "status": "LN",
                        "accounts": ["account-1", "account-2"],
                    }
                ]
            }

            # Make all account details fail
            mock_get_details.side_effect = Exception("API Error")

            # Execute: Run sync
            await sync_service.sync_all_accounts()

            # Assert: Two notifications should be sent
            assert mock_send_notification.call_count == 2

    @pytest.mark.asyncio
    async def test_successful_sync_no_failure_notification(self):
        """Test that successful syncs don't send failure notifications."""
        sync_service = SyncService()

        # Mock the dependencies
        with (
            patch.object(
                sync_service.gocardless, "get_requisitions"
            ) as mock_get_requisitions,
            patch.object(
                sync_service.gocardless, "get_account_details"
            ) as mock_get_details,
            patch.object(
                sync_service.gocardless, "get_account_balances"
            ) as mock_get_balances,
            patch.object(
                sync_service.gocardless, "get_account_transactions"
            ) as mock_get_transactions,
            patch.object(
                sync_service.notifications, "send_sync_failure_notification"
            ) as mock_send_notification,
            patch.object(sync_service.notifications, "send_transaction_notifications"),
            patch.object(sync_service.database, "persist_account_details"),
            patch.object(sync_service.database, "persist_balance"),
            patch.object(
                sync_service.database, "process_transactions", return_value=[]
            ),
            patch.object(
                sync_service.database, "persist_transactions", return_value=[]
            ),
            patch.object(
                sync_service.database, "persist_sync_operation", return_value=1
            ),
        ):
            # Setup: One requisition with one account that succeeds
            mock_get_requisitions.return_value = {
                "results": [
                    {
                        "id": "req-123",
                        "institution_id": "TEST_BANK",
                        "status": "LN",
                        "accounts": ["account-1"],
                    }
                ]
            }

            mock_get_details.return_value = {
                "id": "account-1",
                "institution_id": "TEST_BANK",
                "status": "READY",
                "iban": "TEST123",
            }

            mock_get_balances.return_value = {
                "balances": [{"balanceAmount": {"amount": "100", "currency": "EUR"}}]
            }

            mock_get_transactions.return_value = {"transactions": {"booked": []}}

            # Execute: Run sync
            await sync_service.sync_all_accounts()

            # Assert: No failure notification should be sent
            mock_send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_notification_failure_does_not_stop_sync(self):
        """Test that notification failures don't stop the sync process."""
        sync_service = SyncService()

        # Mock the dependencies
        with (
            patch.object(
                sync_service.gocardless, "get_requisitions"
            ) as mock_get_requisitions,
            patch.object(
                sync_service.gocardless, "get_account_details"
            ) as mock_get_details,
            patch.object(
                sync_service.notifications, "_send_discord_sync_failure"
            ) as mock_discord_notification,
            patch.object(
                sync_service.notifications, "_send_telegram_sync_failure"
            ) as mock_telegram_notification,
            patch.object(
                sync_service.database, "persist_sync_operation", return_value=1
            ),
        ):
            # Setup: One requisition with one account that will fail
            mock_get_requisitions.return_value = {
                "results": [
                    {
                        "id": "req-123",
                        "institution_id": "TEST_BANK",
                        "status": "LN",
                        "accounts": ["account-1"],
                    }
                ]
            }

            # Make account details fail
            mock_get_details.side_effect = Exception("API Error")

            # Make both notification methods fail
            mock_discord_notification.side_effect = Exception("Discord Error")
            mock_telegram_notification.side_effect = Exception("Telegram Error")

            # Execute: Run sync - should not raise exception from notification
            result = await sync_service.sync_all_accounts()

            # The sync should complete with errors but not crash from notifications
            assert result.success is False
            assert len(result.errors) > 0
            assert "API Error" in result.errors[0]
