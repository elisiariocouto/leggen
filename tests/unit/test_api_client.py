"""Tests for CLI API client."""

import pytest
import requests
import requests_mock

from leggen.api_client import LeggenAPIClient, LeggenAPIError


@pytest.mark.cli
class TestLeggenAPIClient:
    """Test the CLI API client."""

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

    def test_connection_error_raises_api_error(self):
        """Connection failures surface as LeggenAPIError (a ClickException)."""
        client = LeggenAPIClient("http://localhost:8000")

        with requests_mock.Mocker() as m:
            m.get(requests_mock.ANY, exc=requests.exceptions.ConnectionError)

            with pytest.raises(LeggenAPIError, match="Could not connect"):
                client.get_accounts()

    def test_http_error_raises_api_error_with_detail(self):
        """HTTP errors surface as LeggenAPIError including the API detail."""
        client = LeggenAPIClient("http://localhost:8000")

        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8000/api/v1/accounts",
                status_code=500,
                json={"detail": "Internal server error"},
            )

            with pytest.raises(LeggenAPIError, match="Internal server error"):
                client.get_accounts()

    def test_custom_api_url(self):
        """Test using custom API URL."""
        custom_url = "http://custom-host:9000"
        client = LeggenAPIClient(custom_url)

        assert client.base_url == f"{custom_url}/api/v1"

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

            request_body = m.last_request.json()
            assert request_body["account_ids"] == ["acc1", "acc2"]
            assert request_body["full_sync"] is True
