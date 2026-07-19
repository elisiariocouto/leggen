"""Tests for notification settings API endpoints."""

from unittest.mock import patch

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
