"""Tests for banks API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest

from leggen.api.dependencies import get_enablebanking_service


@pytest.mark.api
class TestBanksAPI:
    """Test bank-related API endpoints."""

    def test_get_institutions_success(
        self, fastapi_app, api_client, mock_config, sample_bank_data
    ):
        """Test successful retrieval of bank institutions."""
        mock_eb = AsyncMock()
        mock_eb.get_aspsps.return_value = sample_bank_data["aspsps"]
        fastapi_app.dependency_overrides[get_enablebanking_service] = lambda: mock_eb

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/banks/institutions?country=PT")

        fastapi_app.dependency_overrides.pop(get_enablebanking_service, None)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Revolut"
        assert data[1]["name"] == "Banco BPI"

    def test_get_institutions_invalid_country(
        self, fastapi_app, api_client, mock_config
    ):
        """Test institutions endpoint with invalid country code."""
        mock_eb = AsyncMock()
        mock_eb.get_aspsps.return_value = []
        fastapi_app.dependency_overrides[get_enablebanking_service] = lambda: mock_eb

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/banks/institutions?country=XX")

        fastapi_app.dependency_overrides.pop(get_enablebanking_service, None)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_connect_to_bank_success(self, fastapi_app, api_client, mock_config):
        """Test successful bank authorization start."""
        mock_eb = AsyncMock()
        mock_eb.start_auth.return_value = {
            "url": "https://bank.example.com/auth?state=abc"
        }
        fastapi_app.dependency_overrides[get_enablebanking_service] = lambda: mock_eb

        with patch("leggen.utils.config.config", mock_config):
            request_data = {
                "aspsp_name": "Revolut",
                "aspsp_country": "GB",
                "redirect_url": "http://localhost:8000/bank-connected",
            }
            response = api_client.post("/api/v1/banks/connect", json=request_data)

        fastapi_app.dependency_overrides.pop(get_enablebanking_service, None)

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://bank.example.com/auth?state=abc"

    def test_bank_callback_success(self, api_client, mock_config, mock_db_path):
        """Test successful auth code exchange."""
        session_response = {
            "session_id": "sess-123",
            "aspsp": {"name": "Revolut", "country": "GB"},
            "access": {"valid_until": "2026-03-24T00:00:00Z"},
            "accounts": [{"uid": "acc-1"}, {"uid": "acc-2"}],
        }

        mock_eb = AsyncMock()
        mock_eb.create_session.return_value = session_response
        api_client.app.dependency_overrides[get_enablebanking_service] = lambda: mock_eb

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.post(
                "/api/v1/banks/callback", json={"code": "test-auth-code"}
            )

        api_client.app.dependency_overrides.pop(get_enablebanking_service, None)

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "sess-123"
        assert data["aspsp_name"] == "Revolut"
        assert data["aspsp_country"] == "GB"

    def test_get_bank_status_success(self, api_client, mock_config, mock_db_path):
        """Test successful retrieval of bank connection status."""
        # First create a session via callback
        session_response = {
            "session_id": "sess-status-test",
            "aspsp": {"name": "Revolut", "country": "GB"},
            "access": {"valid_until": "2026-12-31T00:00:00Z"},
            "accounts": [{"uid": "acc-1"}],
        }

        mock_eb = AsyncMock()
        mock_eb.create_session.return_value = session_response
        api_client.app.dependency_overrides[get_enablebanking_service] = lambda: mock_eb

        with patch("leggen.utils.config.config", mock_config):
            api_client.post("/api/v1/banks/callback", json={"code": "test-code"})

        api_client.app.dependency_overrides.pop(get_enablebanking_service, None)

        # Now get status
        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/banks/status")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        session = next(s for s in data if s["session_id"] == "sess-status-test")
        assert session["aspsp_name"] == "Revolut"
        assert session["status"] == "active"

    def test_get_supported_countries(self, api_client):
        """Test supported countries endpoint."""
        response = api_client.get("/api/v1/banks/countries")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

        country_codes = [country["code"] for country in data]
        assert "PT" in country_codes
        assert "GB" in country_codes
        assert "DE" in country_codes

    def test_delete_bank_connection(self, api_client, mock_config, mock_db_path):
        """Test deleting a bank connection."""
        # First create a session
        session_response = {
            "session_id": "sess-delete-test",
            "aspsp": {"name": "Banco BPI", "country": "PT"},
            "access": {},
            "accounts": [],
        }

        mock_eb = AsyncMock()
        mock_eb.create_session.return_value = session_response
        api_client.app.dependency_overrides[get_enablebanking_service] = lambda: mock_eb

        with patch("leggen.utils.config.config", mock_config):
            api_client.post("/api/v1/banks/callback", json={"code": "test-code"})

        api_client.app.dependency_overrides.pop(get_enablebanking_service, None)

        # Delete the session
        with patch("leggen.utils.config.config", mock_config):
            response = api_client.delete("/api/v1/banks/connections/sess-delete-test")

        assert response.status_code == 200
        assert response.json()["deleted"] == "sess-delete-test"

    def test_delete_nonexistent_connection(self, api_client, mock_config, mock_db_path):
        """Test deleting a non-existent connection returns 404."""
        with patch("leggen.utils.config.config", mock_config):
            response = api_client.delete("/api/v1/banks/connections/nonexistent-id")

        assert response.status_code == 404
