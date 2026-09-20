"""Tests for NotificationService: filter matching and channel dispatch.

The channel modules are patched at the functions the service calls, so the
tests cover everything up to the point a message would leave the process.
"""

from unittest.mock import AsyncMock, patch

import pytest

from leggen.errors import NotificationNotEnabledError, UpstreamServiceError
from leggen.services.notification_service import NotificationService

DISCORD = {"webhook": "https://discord.com/api/webhooks/1/secret", "enabled": True}
TELEGRAM = {"token": "123456:token", "chat_id": 42, "enabled": True}


def _transaction(description: str, value: float = -10.0) -> dict:
    return {
        "description": description,
        "transactionValue": value,
        "transactionCurrency": "EUR",
        "transactionDate": "2025-09-01T10:00:00",
    }


def _discord(function: str, **kwargs):
    return patch(
        f"leggen.notifications.discord.{function}", new_callable=AsyncMock, **kwargs
    )


def _telegram(function: str, **kwargs):
    return patch(
        f"leggen.notifications.telegram.{function}", new_callable=AsyncMock, **kwargs
    )


@pytest.mark.unit
class TestFilterTransactions:
    def test_case_insensitive_filters_match_any_case(self, test_config):
        test_config._config["filters"] = {"case_insensitive": ["rent"]}

        matching = NotificationService()._filter_transactions(
            [_transaction("Monthly RENT payment"), _transaction("Groceries")]
        )

        assert [m["name"] for m in matching] == ["Monthly RENT payment"]

    def test_case_sensitive_filters_respect_case(self, test_config):
        test_config._config["filters"] = {"case_sensitive": ["ACME"]}

        matching = NotificationService()._filter_transactions(
            [_transaction("ACME LDA"), _transaction("acme lda")]
        )

        assert [m["name"] for m in matching] == ["ACME LDA"]

    def test_either_filter_list_is_enough(self, test_config):
        test_config._config["filters"] = {
            "case_insensitive": ["rent"],
            "case_sensitive": ["ACME"],
        }

        matching = NotificationService()._filter_transactions(
            [_transaction("Rent"), _transaction("ACME"), _transaction("Other")]
        )

        assert [m["name"] for m in matching] == ["Rent", "ACME"]

    def test_matches_are_shaped_for_the_channels(self, test_config):
        test_config._config["filters"] = {"case_insensitive": ["rent"]}

        [match] = NotificationService()._filter_transactions(
            [_transaction("Rent", -750.0)]
        )

        assert match == {
            "name": "Rent",
            "value": -750.0,
            "currency": "EUR",
            "date": "2025-09-01T10:00:00",
        }


@pytest.mark.unit
class TestTransactionNotifications:
    async def test_without_filters_nothing_is_sent(self, test_config):
        test_config._config["notifications"] = {"discord": DISCORD}

        with _discord("send_transactions_message") as send:
            await NotificationService().send_transaction_notifications(
                [_transaction("RENT")]
            )

        send.assert_not_called()

    async def test_without_matches_nothing_is_sent(self, test_config):
        test_config._config["filters"] = {"case_insensitive": ["rent"]}
        test_config._config["notifications"] = {"discord": DISCORD}

        with _discord("send_transactions_message") as send:
            await NotificationService().send_transaction_notifications(
                [_transaction("Coffee")]
            )

        send.assert_not_called()

    async def test_matches_go_to_every_enabled_channel(self, test_config):
        test_config._config["filters"] = {"case_insensitive": ["rent"]}
        test_config._config["notifications"] = {
            "discord": DISCORD,
            "telegram": TELEGRAM,
        }

        with (
            _discord("send_transactions_message") as discord_send,
            _telegram("send_transaction_message") as telegram_send,
        ):
            await NotificationService().send_transaction_notifications(
                [_transaction("RENT"), _transaction("Coffee")]
            )

        webhook, sent = discord_send.call_args.args
        assert webhook == DISCORD["webhook"]
        assert [t["name"] for t in sent] == ["RENT"]
        token, chat_id, sent = telegram_send.call_args.args
        assert (token, chat_id) == (TELEGRAM["token"], TELEGRAM["chat_id"])
        assert [t["name"] for t in sent] == ["RENT"]

    async def test_switched_off_channel_is_skipped(self, test_config):
        test_config._config["filters"] = {"case_insensitive": ["rent"]}
        test_config._config["notifications"] = {
            "discord": DISCORD,
            "telegram": {**TELEGRAM, "enabled": False},
        }

        with (
            _discord("send_transactions_message") as discord_send,
            _telegram("send_transaction_message") as telegram_send,
        ):
            await NotificationService().send_transaction_notifications(
                [_transaction("RENT")]
            )

        discord_send.assert_awaited_once()
        telegram_send.assert_not_called()

    async def test_channel_failure_does_not_stop_the_others(self, test_config):
        """A failing channel is logged; the sync that called us must not fail."""
        test_config._config["filters"] = {"case_insensitive": ["rent"]}
        test_config._config["notifications"] = {
            "discord": DISCORD,
            "telegram": TELEGRAM,
        }

        with (
            _discord("send_transactions_message", side_effect=RuntimeError("rejected")),
            _telegram("send_transaction_message") as telegram_send,
        ):
            await NotificationService().send_transaction_notifications(
                [_transaction("RENT")]
            )

        telegram_send.assert_awaited_once()


@pytest.mark.unit
class TestEventNotifications:
    PAYLOAD = {"session_id": "sess-1", "bank": "TEST_BANK", "days_left": 3}

    async def test_expiry_goes_to_every_enabled_channel(self, test_config):
        test_config._config["notifications"] = {
            "discord": DISCORD,
            "telegram": TELEGRAM,
        }

        with (
            _discord("send_expire_notification") as discord_send,
            _telegram("send_expire_notification") as telegram_send,
        ):
            await NotificationService().send_expiry_notification(self.PAYLOAD)

        discord_send.assert_awaited_once_with(DISCORD["webhook"], self.PAYLOAD)
        telegram_send.assert_awaited_once_with(
            TELEGRAM["token"], TELEGRAM["chat_id"], self.PAYLOAD
        )

    async def test_sync_failure_goes_to_every_enabled_channel(self, test_config):
        test_config._config["notifications"] = {
            "discord": DISCORD,
            "telegram": TELEGRAM,
        }

        with (
            _discord("send_sync_failure_notification") as discord_send,
            _telegram("send_sync_failure_notification") as telegram_send,
        ):
            await NotificationService().send_sync_failure_notification(self.PAYLOAD)

        discord_send.assert_awaited_once_with(DISCORD["webhook"], self.PAYLOAD)
        telegram_send.assert_awaited_once()

    async def test_unconfigured_channels_send_nothing(self, test_config):
        test_config._config["notifications"] = {}

        with (
            _discord("send_expire_notification") as discord_send,
            _telegram("send_expire_notification") as telegram_send,
        ):
            await NotificationService().send_expiry_notification(self.PAYLOAD)

        discord_send.assert_not_called()
        telegram_send.assert_not_called()

    async def test_delivery_failure_is_logged_not_raised(self, test_config):
        test_config._config["notifications"] = {
            "discord": DISCORD,
            "telegram": TELEGRAM,
        }

        with (
            _discord("send_expire_notification", side_effect=RuntimeError("down")),
            _telegram("send_expire_notification") as telegram_send,
        ):
            await NotificationService().send_expiry_notification(self.PAYLOAD)

        telegram_send.assert_awaited_once()


@pytest.mark.unit
class TestTestNotification:
    async def test_sends_the_test_message(self, test_config):
        test_config._config["notifications"] = {"discord": DISCORD}

        with _discord("send_test_notification") as send:
            await NotificationService().send_test_notification("discord")

        send.assert_awaited_once_with(DISCORD["webhook"])

    async def test_unknown_service_is_not_enabled(self, test_config):
        with pytest.raises(NotificationNotEnabledError):
            await NotificationService().send_test_notification("slack")

    async def test_unconfigured_service_is_not_enabled(self, test_config):
        test_config._config["notifications"] = {}

        with pytest.raises(NotificationNotEnabledError):
            await NotificationService().send_test_notification("telegram")

    async def test_provider_failure_is_an_upstream_error(self, test_config):
        test_config._config["notifications"] = {"telegram": TELEGRAM}

        with (
            _telegram("send_test_notification", side_effect=TimeoutError()),
            pytest.raises(UpstreamServiceError) as exc_info,
        ):
            await NotificationService().send_test_notification("telegram")

        assert "TimeoutError" in str(exc_info.value)
