"""Tests for notification settings API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.api
class TestNotificationSettingsAPI:
    """Test notification settings endpoints, especially secret masking."""

    def test_get_settings_no_config(self, api_client, mock_config):
        """Settings without configured services return null services."""
        mock_config._config["notifications"] = {}

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/notifications/settings")

        assert response.status_code == 200
        data = response.json()
        assert data["discord"] is None
        assert data["telegram"] is None

    def test_get_settings_masks_secrets(self, api_client, mock_config):
        """Stored webhook and token are masked in responses."""
        mock_config._config["notifications"] = {
            "discord": {
                "webhook": "https://discord.com/api/webhooks/123/real-secret",
                "enabled": True,
            },
            "telegram": {"token": "123456:real-token", "chat_id": 42, "enabled": True},
        }

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/notifications/settings")

        assert response.status_code == 200
        data = response.json()
        assert data["discord"]["webhook"] == "***"
        assert data["telegram"]["token"] == "***"
        assert data["telegram"]["chat_id"] == 42

    def test_update_with_masked_secrets_keeps_stored_values(
        self, api_client, mock_config
    ):
        """Echoing masked secrets back (e.g. a filters-only save) must not
        overwrite the stored webhook/token."""
        real_webhook = "https://discord.com/api/webhooks/123/real-secret"
        real_token = "123456:real-token"
        mock_config._config["notifications"] = {
            "discord": {"webhook": real_webhook, "enabled": True},
            "telegram": {"token": real_token, "chat_id": 42, "enabled": True},
        }

        request_data = {
            "discord": {"webhook": "***", "enabled": True},
            "telegram": {"token": "***", "chat_id": 42, "enabled": True},
            "filters": {"case_insensitive": ["rent"], "case_sensitive": None},
        }

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.put(
                "/api/v1/notifications/settings", json=request_data
            )

        assert response.status_code == 200
        assert response.json()["updated"] is True

        notifications = mock_config._config["notifications"]
        assert notifications["discord"]["webhook"] == real_webhook
        assert notifications["telegram"]["token"] == real_token
        assert mock_config._config["filters"]["case_insensitive"] == ["rent"]

    def test_update_with_new_secrets_replaces_stored_values(
        self, api_client, mock_config
    ):
        """Sending a real new value replaces the stored secret."""
        mock_config._config["notifications"] = {
            "discord": {
                "webhook": "https://discord.com/api/webhooks/123/old-secret",
                "enabled": True,
            },
        }

        new_webhook = "https://discord.com/api/webhooks/456/new-secret"
        request_data = {
            "discord": {"webhook": new_webhook, "enabled": False},
            "filters": {"case_insensitive": [], "case_sensitive": None},
        }

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.put(
                "/api/v1/notifications/settings", json=request_data
            )

        assert response.status_code == 200
        notifications = mock_config._config["notifications"]
        assert notifications["discord"]["webhook"] == new_webhook
        assert notifications["discord"]["enabled"] is False

    def test_update_with_masked_secret_but_nothing_stored_fails(
        self, api_client, mock_config
    ):
        """A masked placeholder with no stored secret is a client error."""
        mock_config._config["notifications"] = {}

        request_data = {
            "discord": {"webhook": "***", "enabled": True},
            "filters": {"case_insensitive": [], "case_sensitive": None},
        }

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.put(
                "/api/v1/notifications/settings", json=request_data
            )

        assert response.status_code == 400
        assert "no existing value" in response.json()["detail"]
        assert "notifications" not in mock_config._config or not mock_config._config[
            "notifications"
        ].get("discord")


@pytest.fixture
def enabled_notifications(mock_config):
    """Enable both notification services for the duration of a test.

    `mock_config` mutates the process-global `config` singleton rather than
    replacing it, so the `notifications` key has to be restored afterwards or it
    leaks into later tests.
    """
    previous = mock_config._config.get("notifications")
    mock_config._config["notifications"] = {
        "discord": {
            "webhook": "https://discord.com/api/webhooks/123/secret",
            "enabled": True,
        },
        "telegram": {"token": "123456:token", "chat_id": 42, "enabled": True},
    }

    yield mock_config

    if previous is None:
        mock_config._config.pop("notifications", None)
    else:
        mock_config._config["notifications"] = previous


@pytest.mark.api
class TestNotificationTestAPI:
    """Test POST /notifications/test."""

    def test_discord_sends_test_payload(self, api_client, enabled_notifications):
        """The Discord test sends a notification that identifies itself as a
        test, not a fake account-expiry notice."""
        with patch(
            "leggen.notifications.discord._post_embed", new_callable=AsyncMock
        ) as post_embed:
            response = api_client.post(
                "/api/v1/notifications/test", json={"service": "discord"}
            )

        assert response.status_code == 200
        assert response.json() == {"sent": True}

        embed = post_embed.call_args[0][1]
        assert embed["description"] == "Leggen notifications are configured correctly."
        assert embed["title"] == "🔔 Test Notification"

        # The old implementation sent a hardcoded expiry payload instead.
        serialized = str(embed)
        assert "test-123" not in serialized
        assert "Days left" not in serialized

    def test_telegram_sends_test_payload(self, api_client, enabled_notifications):
        """The Telegram test sends the escaped test message."""
        with patch(
            "leggen.notifications.telegram._send_message", new_callable=AsyncMock
        ) as send_message:
            response = api_client.post(
                "/api/v1/notifications/test", json={"service": "telegram"}
            )

        assert response.status_code == 200

        token, chat_id, message = send_message.call_args[0]
        assert token == "123456:token"
        assert chat_id == 42
        # The trailing period is escaped for MarkdownV2.
        assert "Leggen notifications are configured correctly\\." in message
        assert "test-123" not in message

    def test_disabled_service_returns_400(self, api_client, mock_config):
        """Testing an unconfigured service is a client error."""
        previous = mock_config._config.get("notifications")
        mock_config._config["notifications"] = {}
        try:
            response = api_client.post(
                "/api/v1/notifications/test", json={"service": "discord"}
            )
        finally:
            if previous is None:
                mock_config._config.pop("notifications", None)
            else:
                mock_config._config["notifications"] = previous

        assert response.status_code == 400
        assert "discord" in response.json()["detail"]

    def test_unknown_service_returns_422(self, api_client, enabled_notifications):
        """An unsupported service name fails request validation."""
        response = api_client.post(
            "/api/v1/notifications/test", json={"service": "slack"}
        )

        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "VALIDATION_ERROR"
        assert any("service" in error["field"] for error in body["errors"])

    def test_extra_message_field_is_ignored(self, api_client, enabled_notifications):
        """A stale client still sending the removed `message` field succeeds."""
        with patch(
            "leggen.notifications.discord._post_embed", new_callable=AsyncMock
        ) as post_embed:
            response = api_client.post(
                "/api/v1/notifications/test",
                json={"service": "discord", "message": "custom text"},
            )

        assert response.status_code == 200
        assert "custom text" not in str(post_embed.call_args[0][1])
