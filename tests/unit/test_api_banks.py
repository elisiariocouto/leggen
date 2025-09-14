"""Tests for banks API endpoints."""

from unittest.mock import patch

import httpx
import pytest
import respx


@pytest.mark.api
class TestBanksAPI:
    """Test bank-related API endpoints."""

    @respx.mock
    def test_get_institutions_success(
        self, api_client, mock_config, mock_auth_token, sample_bank_data
    ):
        """Test successful retrieval of bank institutions."""
        # Mock GoCardless token creation/refresh
        respx.post("https://bankaccountdata.gocardless.com/api/v2/token/new/").mock(
            return_value=httpx.Response(
                200, json={"access": "test-token", "refresh": "test-refresh"}
            )
        )

        # Mock GoCardless institutions API
        respx.get("https://bankaccountdata.gocardless.com/api/v2/institutions/").mock(
            return_value=httpx.Response(200, json=sample_bank_data)
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/banks/institutions?country=PT")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]["id"] == "REVOLUT_REVOLT21"
        assert data["data"][1]["id"] == "BANCOBPI_BBPIPTPL"

    @respx.mock
    def test_get_institutions_invalid_country(self, api_client, mock_config):
        """Test institutions endpoint with invalid country code."""
        # Mock GoCardless token creation
        respx.post("https://bankaccountdata.gocardless.com/api/v2/token/new/").mock(
            return_value=httpx.Response(
                200, json={"access": "test-token", "refresh": "test-refresh"}
            )
        )

        # Mock empty institutions response for invalid country
        respx.get("https://bankaccountdata.gocardless.com/api/v2/institutions/").mock(
            return_value=httpx.Response(200, json=[])
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/banks/institutions?country=XX")

        # Should still work but return empty or filtered results
        assert response.status_code in [200, 404]

    @respx.mock
    def test_connect_to_bank_success(self, api_client, mock_config, mock_auth_token):
        """Test successful bank connection creation."""
        requisition_data = {
            "id": "req-123",
            "institution_id": "REVOLUT_REVOLT21",
            "status": "CR",
            "created": "2025-09-02T00:00:00Z",
            "link": "https://example.com/auth",
        }

        # Mock GoCardless token creation
        respx.post("https://bankaccountdata.gocardless.com/api/v2/token/new/").mock(
            return_value=httpx.Response(
                200, json={"access": "test-token", "refresh": "test-refresh"}
            )
        )

        # Mock GoCardless requisitions API
        respx.post("https://bankaccountdata.gocardless.com/api/v2/requisitions/").mock(
            return_value=httpx.Response(200, json=requisition_data)
        )

        request_data = {
            "institution_id": "REVOLUT_REVOLT21",
            "redirect_url": "http://localhost:8000/",
        }

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.post("/api/v1/banks/connect", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == "req-123"
        assert data["data"]["institution_id"] == "REVOLUT_REVOLT21"

    @respx.mock
    def test_get_bank_status_success(self, api_client, mock_config, mock_auth_token):
        """Test successful retrieval of bank connection status."""
        requisitions_data = {
            "results": [
                {
                    "id": "req-123",
                    "institution_id": "REVOLUT_REVOLT21",
                    "status": "LN",
                    "created": "2025-09-02T00:00:00Z",
                    "accounts": ["acc-123"],
                }
            ]
        }

        # Mock GoCardless token creation
        respx.post("https://bankaccountdata.gocardless.com/api/v2/token/new/").mock(
            return_value=httpx.Response(
                200, json={"access": "test-token", "refresh": "test-refresh"}
            )
        )

        # Mock GoCardless requisitions API
        respx.get("https://bankaccountdata.gocardless.com/api/v2/requisitions/").mock(
            return_value=httpx.Response(200, json=requisitions_data)
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/banks/status")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["bank_id"] == "REVOLUT_REVOLT21"
        assert data["data"][0]["status_display"] == "LINKED"

    def test_get_supported_countries(self, api_client):
        """Test supported countries endpoint."""
        response = api_client.get("/api/v1/banks/countries")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) > 0

        # Check some expected countries
        country_codes = [country["code"] for country in data["data"]]
        assert "PT" in country_codes
        assert "GB" in country_codes
        assert "DE" in country_codes

    @respx.mock
    def test_authentication_failure(self, api_client, mock_config):
        """Test handling of authentication failures."""
        # Mock token creation failure
        respx.post("https://bankaccountdata.gocardless.com/api/v2/token/new/").mock(
            return_value=httpx.Response(401, json={"detail": "Invalid credentials"})
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/banks/institutions")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to get institutions" in data["detail"]
