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

    def test_unhandled_route_error_uses_sanitized_500(self, fastapi_app, mock_db_path):
        """Routes have no blanket handlers; the global handler renders the
        sanitized 500 with a full traceback in the log."""
        from leggen.background.scheduler import scheduler

        client = TestClient(fastapi_app, raise_server_exceptions=False)
        client.headers["X-API-Key"] = "lgn_test-api-key-for-testing"

        mock_service = MagicMock()
        mock_service.sync_all_accounts.side_effect = Exception("db is locked")
        scheduler.sync_service = mock_service
        try:
            response = client.post("/api/v1/sync")
        finally:
            scheduler._sync_service = None

        assert response.status_code == 500
        body = response.json()
        _assert_envelope(body, 500, "INTERNAL_ERROR")
        assert body["detail"] == "Internal server error."
        assert "db is locked" not in response.text

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
class TestOpenAPISchema:
    def test_error_schema_documented_on_operations(self, fastapi_app, mock_db_path):
        schema = fastapi_app.openapi()

        assert "ErrorResponse" in schema["components"]["schemas"]

        protected = schema["paths"]["/api/v1/accounts"]["get"]["responses"]
        for status in ("401", "500"):
            ref = protected[status]["content"]["application/json"]["schema"]["$ref"]
            assert ref.endswith("/ErrorResponse")

    def test_public_paths_document_no_401(self, fastapi_app, mock_db_path):
        schema = fastapi_app.openapi()

        assert "401" not in schema["paths"]["/api/v1/auth/login"]["post"]["responses"]
        assert "401" not in schema["paths"]["/api/v1/health"]["get"]["responses"]

    def test_public_paths_match_the_routes_that_skip_auth(
        self, fastapi_app, mock_db_path
    ):
        """Guards against the hardcoded set drifting if a route moves."""
        from leggen.api.errors import _PUBLIC_PATHS

        client = TestClient(fastapi_app)
        for path in _PUBLIC_PATHS:
            # Unauthenticated: reachable, so never 401. A 4xx other than 401
            # (bad body, unhealthy) still proves auth was not required.
            method = "post" if path.endswith("login") else "get"
            response = client.request(method, path, json={})
            assert response.status_code != 401, path

    def test_validation_responses_use_the_error_schema(self, fastapi_app, mock_db_path):
        """FastAPI documents a list-shaped 422; ours is the envelope."""
        schema = fastapi_app.openapi()

        responses = schema["paths"]["/api/v1/transactions"]["get"]["responses"]
        ref = responses["422"]["content"]["application/json"]["schema"]["$ref"]
        assert ref.endswith("/ErrorResponse")


@pytest.mark.api
class TestHealthEndpoint:
    def test_healthy(self, fastapi_app, mock_db_path):
        client = TestClient(fastapi_app)

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_unhealthy_returns_503_without_exception_details(
        self, fastapi_app, mock_db_path
    ):
        """The endpoint is unauthenticated, so it must not echo the failure."""
        client = TestClient(fastapi_app)

        with patch(
            "leggen.commands.server.metadata.version",
            side_effect=Exception("/secret/path/leggen.db unreadable"),
        ):
            response = client.get("/api/v1/health")

        assert response.status_code == 503
        assert response.json() == {"status": "unhealthy"}
        assert "/secret/path" not in response.text


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

    def test_bad_category_id_reports_the_field(
        self, fastapi_app, api_client, mock_db_path
    ):
        """This filter used to hand-raise a 422 with no field information."""
        response = api_client.get("/api/v1/transactions?category_id=bogus")

        assert response.status_code == 422
        body = response.json()
        _assert_envelope(body, 422, "VALIDATION_ERROR")
        assert body["errors"][0]["field"] == "query.category_id"

    def test_valid_category_id_values_are_accepted(
        self, fastapi_app, api_client, mock_db_path
    ):
        for value in ("7", "uncategorized"):
            response = api_client.get(f"/api/v1/transactions?category_id={value}")
            assert response.status_code == 200, value

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
