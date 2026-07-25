"""Tests for the unified error envelope and its exception handlers."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from leggen.repositories import SessionRepository


def _assert_envelope(body: dict, status: int, code: str) -> None:
    """Every error body carries a string detail, a code and the status."""
    assert isinstance(body["detail"], str)
    assert body["detail"]
    assert body["code"] == code
    assert body["status"] == status


@pytest.mark.api
class TestErrorEnvelope:
    def test_not_found_uses_envelope(self, fastapi_app, api_client, mock_db_path):
        response = api_client.delete("/api/v1/accounts/does-not-exist")

        assert response.status_code == 404
        _assert_envelope(response.json(), 404, "NOT_FOUND")

    def test_sanitized_500_keeps_route_message(
        self, fastapi_app, api_client, mock_db_path
    ):
        """A route's own 500 message survives; the code is filled in for it."""
        from leggen.background.scheduler import scheduler

        mock_service = MagicMock()
        mock_service.sync_all_accounts.side_effect = Exception("db is locked")
        scheduler.sync_service = mock_service
        try:
            response = api_client.post("/api/v1/sync")
        finally:
            scheduler._sync_service = None

        assert response.status_code == 500
        body = response.json()
        _assert_envelope(body, 500, "INTERNAL_ERROR")
        assert body["detail"] == "Failed to run sync."

    def test_unhandled_exception_returns_json_not_plain_text(
        self, fastapi_app, mock_db_path
    ):
        """Routes without a try/except used to fall through to a plain-text 500."""
        # raise_server_exceptions=False so TestClient returns the handler's
        # response instead of re-raising the original exception.
        client = TestClient(fastapi_app, raise_server_exceptions=False)
        client.headers["X-API-Key"] = "lgn_test-api-key-for-testing"

        with patch.object(
            SessionRepository,
            "delete_session",
            side_effect=Exception("connection to /secret/path/leggen.db failed"),
        ):
            response = client.delete("/api/v1/banks/connections/some-session")

        assert response.status_code == 500
        assert response.headers["content-type"].startswith("application/json")
        body = response.json()
        _assert_envelope(body, 500, "INTERNAL_ERROR")
        assert "/secret/path" not in response.text

    def test_unauthorized_preserves_www_authenticate_header(
        self, fastapi_app, mock_db_path
    ):
        """The auth dependency's WWW-Authenticate header must survive the handler."""
        client = TestClient(fastapi_app)

        response = client.get("/api/v1/accounts")

        assert response.status_code == 401
        _assert_envelope(response.json(), 401, "UNAUTHORIZED")
        assert response.headers["www-authenticate"] == "Bearer"

    def test_unknown_route_returns_envelope(self, fastapi_app, mock_db_path):
        """Starlette's own 404 for an unrouted path is shaped like the rest."""
        client = TestClient(fastapi_app)

        response = client.get("/api/v1/no-such-endpoint")

        assert response.status_code == 404
        _assert_envelope(response.json(), 404, "NOT_FOUND")


@pytest.mark.api
class TestValidationErrors:
    def test_validation_error_has_string_detail_and_field_errors(
        self, fastapi_app, api_client, mock_db_path
    ):
        """FastAPI puts a list in `detail`; we keep it a string and add `errors`."""
        response = api_client.get("/api/v1/transactions?per_page=0")

        assert response.status_code == 422
        body = response.json()
        _assert_envelope(body, 422, "VALIDATION_ERROR")
        assert len(body["errors"]) == 1
        field_error = body["errors"][0]
        assert "per_page" in field_error["field"]
        assert field_error["message"]
        assert field_error["type"]
        # `input` and `ctx` are deliberately dropped, see the handler.
        assert set(field_error) == {"field", "message", "type"}

    def test_validation_error_does_not_echo_submitted_secrets(
        self, fastapi_app, api_client, mock_db_path
    ):
        """Pydantic reports the offending input; that must not reach the client."""
        secret = "AKIAsupersecretvalue123"

        response = api_client.put(
            "/api/v1/backup/settings",
            json={
                "s3": {
                    "access_key_id": "some-key",
                    "secret_access_key": secret,
                    # bucket_name omitted, so the whole s3 object is the input
                }
            },
        )

        assert response.status_code == 422
        assert secret not in response.text
