"""Tests for notification settings API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.api
class TestNotificationSettingsAPI:
    """Test notification settings endpoints, especially secret masking."""

    def test_get_settings_no_config(self, api_client, mock_config):
        """Settings without configured services return null services."""
        mock_config._config["notifications"] = {}

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

        response = api_client.put("/api/v1/notifications/settings", json=request_data)

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

        response = api_client.put("/api/v1/notifications/settings", json=request_data)

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

        response = api_client.put("/api/v1/notifications/settings", json=request_data)

        assert response.status_code == 400
        assert "no existing value" in response.json()["detail"]
        assert "notifications" not in mock_config._config or not mock_config._config[
            "notifications"
        ].get("discord")


@pytest.fixture
def clean_notification_sections(mock_config):
    """Drop the sections these tests write.

    `mock_config` mutates the process-global `config` singleton rather than
    replacing it, so `filters`/`notifications` have to be removed afterwards or
    they leak into later tests.
    """
    yield mock_config

    mock_config._config.pop("filters", None)
    mock_config._config.pop("notifications", None)


@pytest.mark.api
@pytest.mark.usefixtures("clean_notification_sections")
class TestNotificationFiltersUpdateAPI:
    """Test that filters can be cleared and that a partial body merges."""

    def test_empty_filter_lists_clear_stored_filters(self, api_client, mock_config):
        """Removing the last filter in the UI must persist as no filters."""
        mock_config._config["filters"] = {
            "case_insensitive": ["rent"],
            "case_sensitive": ["ACME"],
        }

        request_data = {"filters": {"case_insensitive": [], "case_sensitive": []}}

        response = api_client.put("/api/v1/notifications/settings", json=request_data)

        assert response.status_code == 200
        assert mock_config._config["filters"]["case_insensitive"] == []
        assert mock_config._config["filters"]["case_sensitive"] == []

    def test_omitted_filter_list_is_left_alone(self, api_client, mock_config):
        """A body that mentions one list must not clear the other."""
        mock_config._config["filters"] = {
            "case_insensitive": ["rent"],
            "case_sensitive": ["ACME"],
        }

        request_data = {"filters": {"case_insensitive": ["rent", "gym"]}}

        response = api_client.put("/api/v1/notifications/settings", json=request_data)

        assert response.status_code == 200
        assert mock_config._config["filters"]["case_insensitive"] == ["rent", "gym"]
        assert mock_config._config["filters"]["case_sensitive"] == ["ACME"]

    def test_omitted_filters_leave_the_section_untouched(self, api_client, mock_config):
        """Saving a service must not disturb stored filters."""
        mock_config._config["filters"] = {"case_insensitive": ["rent"]}
        mock_config._config["notifications"] = {}

        request_data = {
            "discord": {
                "webhook": "https://discord.com/api/webhooks/123/secret",
                "enabled": True,
            }
        }

        response = api_client.put("/api/v1/notifications/settings", json=request_data)

        assert response.status_code == 200
        assert mock_config._config["filters"]["case_insensitive"] == ["rent"]

    def test_omitted_service_survives_an_update_to_the_other(
        self, api_client, mock_config
    ):
        """`update_section` replaces wholesale, so the handler has to merge."""
        real_token = "123456:real-token"
        mock_config._config["notifications"] = {
            "telegram": {"token": real_token, "chat_id": 42, "enabled": True},
        }

        request_data = {
            "discord": {
                "webhook": "https://discord.com/api/webhooks/123/secret",
                "enabled": True,
            }
        }

        response = api_client.put("/api/v1/notifications/settings", json=request_data)

        assert response.status_code == 200
        notifications = mock_config._config["notifications"]
        assert notifications["telegram"]["token"] == real_token
        assert notifications["discord"]["enabled"] is True

    def test_null_service_removes_it(self, api_client, mock_config):
        """An explicit null means "remove this service"."""
        mock_config._config["notifications"] = {
            "discord": {
                "webhook": "https://discord.com/api/webhooks/123/secret",
                "enabled": True,
            },
            "telegram": {"token": "123456:token", "chat_id": 42, "enabled": True},
        }

        request_data = {"telegram": None}

        response = api_client.put("/api/v1/notifications/settings", json=request_data)

        assert response.status_code == 200
        notifications = mock_config._config["notifications"]
        assert "telegram" not in notifications
        assert notifications["discord"]["enabled"] is True

    def test_delete_filters_clears_the_section(self, api_client, mock_config):
        """The filters DELETE must not be shadowed by the /{service} route."""
        mock_config._config["filters"] = {
            "case_insensitive": ["rent"],
            "case_sensitive": ["ACME"],
        }

        response = api_client.delete("/api/v1/notifications/settings/filters")

        assert response.status_code == 200
        assert response.json() == {"deleted": "filters"}
        assert not mock_config._config["filters"].get("case_insensitive")
        assert not mock_config._config["filters"].get("case_sensitive")


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

    def test_unconfigured_service_returns_not_enabled(self, api_client, mock_config):
        """A service with no credentials is a configuration error, not a
        delivery failure."""
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
        body = response.json()
        assert body["code"] == "NOTIFICATION_NOT_ENABLED"
        assert body["status"] == 400
        assert "discord" in body["detail"]

    def test_switched_off_service_returns_not_enabled(
        self, api_client, enabled_notifications
    ):
        """Credentials present but `enabled = false` is still not enabled."""
        enabled_notifications._config["notifications"]["telegram"]["enabled"] = False

        response = api_client.post(
            "/api/v1/notifications/test", json={"service": "telegram"}
        )

        assert response.status_code == 400
        assert response.json()["code"] == "NOTIFICATION_NOT_ENABLED"

    def test_provider_failure_returns_502(self, api_client, enabled_notifications):
        """A provider that refuses the message is an upstream failure, kept
        distinct from a misconfiguration."""
        with patch(
            "leggen.notifications.discord._post_embed",
            new_callable=AsyncMock,
            side_effect=RuntimeError("webhook rejected"),
        ):
            response = api_client.post(
                "/api/v1/notifications/test", json={"service": "discord"}
            )

        assert response.status_code == 502
        body = response.json()
        assert body["code"] == "UPSTREAM_ERROR"
        assert body["status"] == 502
        assert "discord" in body["detail"]

    def test_timeout_without_a_message_still_names_the_cause(
        self, api_client, enabled_notifications
    ):
        """An exception with an empty str() still yields an identifiable detail."""
        with patch(
            "leggen.notifications.telegram._send_message",
            new_callable=AsyncMock,
            side_effect=TimeoutError(),
        ):
            response = api_client.post(
                "/api/v1/notifications/test", json={"service": "telegram"}
            )

        assert response.status_code == 502
        assert "TimeoutError" in response.json()["detail"]

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


@pytest.mark.api
class TestNotificationServiceDeletionAPI:
    """Test DELETE /notifications/settings/{service}."""

    def test_delete_removes_the_service(self, api_client, enabled_notifications):
        """Deleting a service drops its whole section from the config."""
        response = api_client.delete("/api/v1/notifications/settings/discord")

        assert response.status_code == 200
        assert response.json() == {"deleted": "discord"}
        assert "discord" not in enabled_notifications._config["notifications"]
        # The other service is untouched.
        assert "telegram" in enabled_notifications._config["notifications"]

    def test_unknown_service_returns_422(self, api_client, enabled_notifications):
        """An unsupported service name fails path validation, matching the
        envelope the test endpoint returns rather than a hand-rolled 400."""
        response = api_client.delete("/api/v1/notifications/settings/slack")

        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "VALIDATION_ERROR"
        assert any("service" in error["field"] for error in body["errors"])

    def test_filters_route_still_wins_over_the_service_route(
        self, api_client, mock_config
    ):
        """`/settings/filters` must not be swallowed by the service path."""
        mock_config._config["filters"] = {"case_insensitive": ["rent"]}

        response = api_client.delete("/api/v1/notifications/settings/filters")

        assert response.status_code == 200
        assert response.json() == {"deleted": "filters"}


@pytest.mark.api
class TestNotificationServicesStatusAPI:
    """Test GET /notifications/services."""

    def test_configured_and_switched_on_is_active(
        self, api_client, enabled_notifications
    ):
        response = api_client.get("/api/v1/notifications/services")

        assert response.status_code == 200
        discord = response.json()["discord"]
        assert discord == {
            "name": "Discord",
            "enabled": True,
            "configured": True,
            "active": True,
        }

    def test_missing_credentials_are_not_configured(self, api_client, mock_config):
        """`enabled` reflects the config switch, so an unconfigured service is
        reported as enabled-but-not-configured and is not active."""
        previous = mock_config._config.get("notifications")
        mock_config._config["notifications"] = {}
        try:
            response = api_client.get("/api/v1/notifications/services")
        finally:
            if previous is None:
                mock_config._config.pop("notifications", None)
            else:
                mock_config._config["notifications"] = previous

        telegram = response.json()["telegram"]
        assert telegram["enabled"] is True
        assert telegram["configured"] is False
        assert telegram["active"] is False

    def test_switched_off_service_is_configured_but_inactive(
        self, api_client, enabled_notifications
    ):
        enabled_notifications._config["notifications"]["discord"]["enabled"] = False

        response = api_client.get("/api/v1/notifications/services")

        discord = response.json()["discord"]
        assert discord["enabled"] is False
        assert discord["configured"] is True
        assert discord["active"] is False
