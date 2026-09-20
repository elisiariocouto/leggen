"""Tests for banks API endpoints."""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from leggen.services.enablebanking_service import (
    AuthState,
    get_enablebanking_service,
)


@pytest.mark.api
class TestBanksAPI:
    """Test bank-related API endpoints."""

    def test_get_institutions_success(self, api_client, override, sample_bank_data):
        """Test successful retrieval of bank institutions."""
        mock_eb = AsyncMock()
        mock_eb.get_aspsps.return_value = sample_bank_data["aspsps"]
        override(get_enablebanking_service, mock_eb)

        response = api_client.get("/api/v1/banks/institutions?country=PT")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Banco BPI"
        assert data[1]["name"] == "Revolut"

    def test_get_institutions_invalid_country(self, api_client, override):
        """Test institutions endpoint with invalid country code."""
        mock_eb = AsyncMock()
        mock_eb.get_aspsps.return_value = []
        override(get_enablebanking_service, mock_eb)

        response = api_client.get("/api/v1/banks/institutions?country=XX")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_connect_to_bank_success(self, api_client, override):
        """Test successful bank authorization start."""
        mock_eb = AsyncMock()
        mock_eb.get_aspsps.return_value = [
            {"name": "Revolut", "country": "GB", "maximum_consent_validity": 15552000}
        ]
        mock_eb.start_auth.return_value = {
            "url": "https://bank.example.com/auth?state=abc"
        }
        override(get_enablebanking_service, mock_eb)

        request_data = {
            "aspsp_name": "Revolut",
            "aspsp_country": "GB",
            "redirect_url": "http://localhost:8000/bank-connected",
        }
        response = api_client.post("/api/v1/banks/connect", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://bank.example.com/auth?state=abc"
        # The bank's maximum consent validity must be forwarded to start_auth
        call_kwargs = mock_eb.start_auth.call_args.kwargs
        assert call_kwargs["maximum_consent_validity"] == 15552000

    def test_connect_to_bank_without_consent_validity(self, api_client, override):
        """Banks that don't report a maximum consent validity fall back to None."""
        mock_eb = AsyncMock()
        mock_eb.get_aspsps.return_value = [{"name": "Revolut", "country": "GB"}]
        mock_eb.start_auth.return_value = {
            "url": "https://bank.example.com/auth?state=abc"
        }
        override(get_enablebanking_service, mock_eb)

        request_data = {"aspsp_name": "Revolut", "aspsp_country": "GB"}
        response = api_client.post("/api/v1/banks/connect", json=request_data)

        assert response.status_code == 200
        assert mock_eb.start_auth.call_args.kwargs["maximum_consent_validity"] is None

    def test_bank_callback_success(self, api_client, override):
        """Test successful auth code exchange."""
        session_response = {
            "session_id": "sess-123",
            "aspsp": {"name": "Revolut", "country": "GB"},
            "access": {"valid_until": "2026-03-24T00:00:00Z"},
            "accounts": [{"uid": "acc-1"}, {"uid": "acc-2"}],
        }

        mock_eb = AsyncMock()
        mock_eb.create_session.return_value = session_response
        mock_eb.claim_auth_state = MagicMock(
            return_value=AuthState(issued_at=time.time())
        )
        mock_eb.mark_auth_state_redeemed = MagicMock()
        override(get_enablebanking_service, mock_eb)

        response = api_client.post(
            "/api/v1/banks/callback",
            json={"code": "test-auth-code", "state": "test-state"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "sess-123"
        assert data["aspsp_name"] == "Revolut"
        assert data["aspsp_country"] == "GB"

    def test_bank_callback_replays_session_on_repeat(self, api_client, override):
        """A redirect delivered twice returns the session the first call made.

        The page can be remounted by a reload -- a service worker taking
        control after an update, or the user refreshing -- and the second
        exchange must not look like a failed connection.
        """
        session_response = {
            "session_id": "sess-replay",
            "aspsp": {"name": "Revolut", "country": "GB"},
            "access": {"valid_until": "2026-03-24T00:00:00Z"},
            "accounts": [{"uid": "acc-1"}],
        }

        state = AuthState(issued_at=time.time())
        mock_eb = AsyncMock()
        mock_eb.create_session.return_value = session_response
        mock_eb.claim_auth_state = MagicMock(return_value=state)
        mock_eb.mark_auth_state_redeemed = MagicMock(
            side_effect=lambda _s, session_id: setattr(state, "session_id", session_id)
        )
        override(get_enablebanking_service, mock_eb)

        payload = {"code": "test-auth-code", "state": "test-state"}
        first = api_client.post("/api/v1/banks/callback", json=payload)
        second = api_client.post("/api/v1/banks/callback", json=payload)

        assert first.status_code == 200
        assert second.status_code == 200
        assert second.json()["session_id"] == "sess-replay"
        # The upstream code is single-use, so it must only be exchanged once.
        assert mock_eb.create_session.await_count == 1

    def test_bank_callback_rejects_unknown_state(self, api_client, override):
        """Callback rejects a state that was never issued by start_auth."""
        mock_eb = AsyncMock()
        mock_eb.claim_auth_state = MagicMock(return_value=None)
        override(get_enablebanking_service, mock_eb)

        response = api_client.post(
            "/api/v1/banks/callback",
            json={"code": "test-auth-code", "state": "forged-state"},
        )

        assert response.status_code == 400
        mock_eb.create_session.assert_not_called()

    def test_get_bank_status_success(self, api_client, override):
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
        mock_eb.claim_auth_state = MagicMock(
            return_value=AuthState(issued_at=time.time())
        )
        mock_eb.mark_auth_state_redeemed = MagicMock()
        override(get_enablebanking_service, mock_eb)

        api_client.post(
            "/api/v1/banks/callback",
            json={"code": "test-code", "state": "test-state"},
        )

        # Now get status
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

    def test_delete_bank_connection(self, api_client, override):
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
        mock_eb.claim_auth_state = MagicMock(
            return_value=AuthState(issued_at=time.time())
        )
        mock_eb.mark_auth_state_redeemed = MagicMock()
        override(get_enablebanking_service, mock_eb)

        api_client.post(
            "/api/v1/banks/callback",
            json={"code": "test-code", "state": "test-state"},
        )

        # Delete the session
        response = api_client.delete("/api/v1/banks/connections/sess-delete-test")

        assert response.status_code == 200
        assert response.json()["deleted"] == "sess-delete-test"

    def test_delete_nonexistent_connection(self, api_client):
        """Test deleting a non-existent connection returns 404."""
        response = api_client.delete("/api/v1/banks/connections/nonexistent-id")

        assert response.status_code == 404
