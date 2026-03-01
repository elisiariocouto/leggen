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
            m.get(
                "http://localhost:8000/api/v1/health",
                json={"status": "healthy"},
            )

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

        processed_institutions = sample_bank_data["aspsps"]

        api_response = processed_institutions

        with requests_mock.Mocker() as m:
            m.get("http://localhost:8000/api/v1/banks/institutions", json=api_response)

            result = client.get_institutions("PT")
            assert len(result) == 2
            assert result[0]["name"] == "Revolut"

    def test_connect_to_bank_success(self):
        """Test connecting to a bank via API client."""
        client = LeggenAPIClient("http://localhost:8000")

        api_response = {"url": "https://bank.example.com/auth"}

        with requests_mock.Mocker() as m:
            m.post("http://localhost:8000/api/v1/banks/connect", json=api_response)

            result = client.connect_to_bank("Revolut", "GB")
            assert result["url"] == "https://bank.example.com/auth"

    def test_exchange_auth_code_success(self):
        """Test exchanging auth code via API client."""
        client = LeggenAPIClient("http://localhost:8000")

        api_response = {
            "session_id": "sess-123",
            "aspsp_name": "Revolut",
            "aspsp_country": "GB",
        }

        with requests_mock.Mocker() as m:
            m.post("http://localhost:8000/api/v1/banks/callback", json=api_response)

            result = client.exchange_auth_code("test-code")
            assert result["session_id"] == "sess-123"

    def test_get_accounts_success(self, sample_account_data):
        """Test getting accounts via API client."""
        client = LeggenAPIClient("http://localhost:8000")

        api_response = [sample_account_data]

        with requests_mock.Mocker() as m:
            m.get("http://localhost:8000/api/v1/accounts", json=api_response)

            result = client.get_accounts()
            assert len(result) == 1
            assert result[0]["id"] == "test-account-123"

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

        assert client.base_url == f"{custom_url}/api/v1"

    def test_environment_variable_url(self):
        """Test using environment variable for API URL."""
        with patch.dict("os.environ", {"LEGGEN_API_URL": "http://env-host:7000"}):
            client = LeggenAPIClient()
            assert client.base_url == "http://env-host:7000/api/v1"

    def test_trigger_sync_default(self):
        """Test triggering sync with default options."""
        client = LeggenAPIClient("http://localhost:8000")

        api_response = {
            "success": True,
            "accounts_processed": 2,
            "transactions_added": 10,
            "transactions_updated": 0,
            "balances_updated": 2,
            "duration_seconds": 5.3,
            "errors": [],
            "started_at": "2025-09-01T09:30:00Z",
            "completed_at": "2025-09-01T09:30:05Z",
        }

        with requests_mock.Mocker() as m:
            m.post("http://localhost:8000/api/v1/sync", json=api_response)

            result = client.trigger_sync()
            assert result["success"] is True
            assert result["accounts_processed"] == 2

    def test_trigger_sync_full(self):
        """Test triggering sync with full_sync option."""
        client = LeggenAPIClient("http://localhost:8000")

        api_response = {
            "success": True,
            "accounts_processed": 2,
            "transactions_added": 50,
            "transactions_updated": 5,
            "balances_updated": 2,
            "duration_seconds": 12.1,
            "errors": [],
            "started_at": "2025-09-01T09:30:00Z",
            "completed_at": "2025-09-01T09:30:12Z",
        }

        with requests_mock.Mocker() as m:
            m.post("http://localhost:8000/api/v1/sync", json=api_response)

            result = client.trigger_sync(account_ids=["acc1", "acc2"], full_sync=True)
            assert result["success"] is True
            assert result["transactions_added"] == 50
