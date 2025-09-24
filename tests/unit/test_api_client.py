"""Tests for CLI API client."""

from unittest.mock import patch

import pytest
import requests
import requests_mock

from leggen.api_client import LeggenAPIClient


@pytest.mark.cli
class TestLeggenAPIClient:
    """Test the CLI API client."""

    def test_health_check_success(self):
        """Test successful health check."""
        client = LeggenAPIClient("http://localhost:8000")

        with requests_mock.Mocker() as m:
            m.get("http://localhost:8000/health", json={"status": "healthy"})

            result = client.health_check()
            assert result is True

    def test_health_check_failure(self):
        """Test health check failure."""
        client = LeggenAPIClient("http://localhost:8000")

        with requests_mock.Mocker() as m:
            m.get("http://localhost:8000/health", status_code=500)

            result = client.health_check()
            assert result is False

    def test_get_institutions_success(self, sample_bank_data):
        """Test getting institutions via API client."""
        client = LeggenAPIClient("http://localhost:8000")

        # The API returns processed institutions, not raw GoCardless data
        processed_institutions = sample_bank_data["results"]

        api_response = {
            "success": True,
            "data": processed_institutions,
            "message": "Found 2 institutions for PT",
        }

        with requests_mock.Mocker() as m:
            m.get("http://localhost:8000/api/v1/banks/institutions", json=api_response)

            result = client.get_institutions("PT")
            assert len(result) == 2
            assert result[0]["id"] == "REVOLUT_REVOLT21"

    def test_get_accounts_success(self, sample_account_data):
        """Test getting accounts via API client."""
        client = LeggenAPIClient("http://localhost:8000")

        api_response = {
            "success": True,
            "data": [sample_account_data],
            "message": "Retrieved 1 accounts",
        }

        with requests_mock.Mocker() as m:
            m.get("http://localhost:8000/api/v1/accounts", json=api_response)

            result = client.get_accounts()
            assert len(result) == 1
            assert result[0]["id"] == "test-account-123"

    def test_trigger_sync_success(self):
        """Test triggering sync via API client."""
        client = LeggenAPIClient("http://localhost:8000")

        api_response = {
            "success": True,
            "data": {"sync_started": True, "force": False},
            "message": "Started sync for all accounts",
        }

        with requests_mock.Mocker() as m:
            m.post("http://localhost:8000/api/v1/sync", json=api_response)

            result = client.trigger_sync()
            assert result["sync_started"] is True

    def test_connection_error_handling(self):
        """Test handling of connection errors."""
        client = LeggenAPIClient("http://localhost:9999")  # Non-existent service

        with pytest.raises((requests.ConnectionError, requests.RequestException)):
            client.get_accounts()

    def test_http_error_handling(self):
        """Test handling of HTTP errors."""
        client = LeggenAPIClient("http://localhost:8000")

        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8000/api/v1/accounts",
                status_code=500,
                json={"detail": "Internal server error"},
            )

            with pytest.raises((requests.HTTPError, requests.RequestException)):
                client.get_accounts()

    def test_custom_api_url(self):
        """Test using custom API URL."""
        custom_url = "http://custom-host:9000"
        client = LeggenAPIClient(custom_url)

        assert client.base_url == custom_url

    def test_environment_variable_url(self):
        """Test using environment variable for API URL."""
        with patch.dict("os.environ", {"LEGGEN_API_URL": "http://env-host:7000"}):
            client = LeggenAPIClient()
            assert client.base_url == "http://env-host:7000"

    def test_sync_with_options(self):
        """Test sync with various options."""
        client = LeggenAPIClient("http://localhost:8000")

        api_response = {
            "success": True,
            "data": {"sync_started": True, "force": True},
            "message": "Started sync for 2 specific accounts",
        }

        with requests_mock.Mocker() as m:
            m.post("http://localhost:8000/api/v1/sync", json=api_response)

            result = client.trigger_sync(account_ids=["acc1", "acc2"], force=True)
            assert result["sync_started"] is True
            assert result["force"] is True

    def test_get_scheduler_config(self):
        """Test getting scheduler configuration."""
        client = LeggenAPIClient("http://localhost:8000")

        api_response = {
            "success": True,
            "data": {
                "enabled": True,
                "hour": 3,
                "minute": 0,
                "next_scheduled_sync": "2025-09-03T03:00:00Z",
            },
        }

        with requests_mock.Mocker() as m:
            m.get("http://localhost:8000/api/v1/sync/scheduler", json=api_response)

            result = client.get_scheduler_config()
            assert result["enabled"] is True
            assert result["hour"] == 3
