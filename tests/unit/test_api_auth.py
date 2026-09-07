"""Tests for auth API endpoints and authentication dependency."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from leggen.errors import AuthenticationError, TokenExpiredError
from leggen.utils.auth import create_access_token, decode_access_token


@pytest.mark.api
class TestAuthLogin:
    """Test POST /api/v1/auth/login endpoint."""

    def test_login_valid_credentials(self, fastapi_app, mock_db_path):
        """Test login with valid username and password returns a token."""
        client = TestClient(fastapi_app)
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpassword"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, fastapi_app, mock_db_path):
        """Test login with wrong password returns 401."""
        client = TestClient(fastapi_app)
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_wrong_username(self, fastapi_app, mock_db_path):
        """Test login with wrong username returns 401."""
        client = TestClient(fastapi_app)
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "wronguser", "password": "testpassword"},
        )
        assert response.status_code == 401

    def test_login_token_authenticates(self, fastapi_app, mock_db_path):
        """Test that a token obtained from login can authenticate a protected endpoint."""
        client = TestClient(fastapi_app)
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpassword"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Use the token to access a protected endpoint
        response = client.get(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


@pytest.mark.api
class TestAuthDependency:
    """Test authentication dependency via protected endpoints."""

    def test_no_credentials_returns_401(self, fastapi_app, mock_db_path):
        """Test that requests without credentials return 401."""
        client = TestClient(fastapi_app)
        response = client.get("/api/v1/accounts")
        assert response.status_code == 401

    def test_valid_api_key(self, api_client, mock_db_path):
        """Test that a valid API key authenticates successfully."""
        response = api_client.get("/api/v1/accounts")
        assert response.status_code == 200

    def test_invalid_api_key(self, fastapi_app, mock_db_path):
        """Test that an invalid API key returns 401."""
        client = TestClient(fastapi_app)
        response = client.get(
            "/api/v1/accounts",
            headers={"X-API-Key": "lgn_invalid-key"},
        )
        assert response.status_code == 401

    def test_valid_jwt(self, fastapi_app, mock_db_path):
        """Test that a valid JWT token authenticates successfully."""
        token = create_access_token(
            username="testuser",
            secret="test-jwt-secret-for-testing-only",
        )
        client = TestClient(fastapi_app)
        response = client.get(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_invalid_jwt(self, fastapi_app, mock_db_path):
        """A malformed JWT is reported as an invalid credential, not an expiry."""
        client = TestClient(fastapi_app)
        response = client.get(
            "/api/v1/accounts",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
        assert response.json()["code"] == "INVALID_CREDENTIALS"

    def test_jwt_signed_with_wrong_secret(self, fastapi_app, mock_db_path):
        """A well-formed token signed by someone else is invalid, not expired."""
        token = create_access_token(username="testuser", secret="not-the-secret")
        client = TestClient(fastapi_app)
        response = client.get(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        assert response.json()["code"] == "INVALID_CREDENTIALS"

    def test_expired_jwt(self, fastapi_app, mock_db_path):
        """An expired JWT is reported with its own code, so the UI can explain it."""
        token = create_access_token(
            username="testuser",
            secret="test-jwt-secret-for-testing-only",
            expires_minutes=-1,
        )
        client = TestClient(fastapi_app)
        response = client.get(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        body = response.json()
        assert body["code"] == "TOKEN_EXPIRED"
        assert "expired" in body["detail"].lower()
        assert response.headers["www-authenticate"] == "Bearer"

    def test_expired_jwt_does_not_block_valid_api_key(self, fastapi_app, mock_db_path):
        """A stale bearer token must not shadow a valid X-API-Key on the same request."""
        token = create_access_token(
            username="testuser",
            secret="test-jwt-secret-for-testing-only",
            expires_minutes=-1,
        )
        client = TestClient(fastapi_app)
        response = client.get(
            "/api/v1/accounts",
            headers={
                "Authorization": f"Bearer {token}",
                "X-API-Key": "lgn_test-api-key-for-testing",
            },
        )
        assert response.status_code == 200

    def test_expired_jwt_with_invalid_api_key_reports_expiry(
        self, fastapi_app, mock_db_path
    ):
        """With neither credential usable, the bearer token's reason is the one shown."""
        token = create_access_token(
            username="testuser",
            secret="test-jwt-secret-for-testing-only",
            expires_minutes=-1,
        )
        client = TestClient(fastapi_app)
        response = client.get(
            "/api/v1/accounts",
            headers={
                "Authorization": f"Bearer {token}",
                "X-API-Key": "lgn_invalid-key",
            },
        )
        assert response.status_code == 401
        assert response.json()["code"] == "TOKEN_EXPIRED"

    def test_no_credentials_code(self, fastapi_app, mock_db_path):
        """A request with nothing at all is an invalid credential, not an expiry."""
        client = TestClient(fastapi_app)
        response = client.get("/api/v1/accounts")
        assert response.status_code == 401
        assert response.json()["code"] == "INVALID_CREDENTIALS"


@pytest.mark.unit
class TestDecodeAccessToken:
    """Test the token decoder's typed failure modes directly."""

    SECRET = "test-jwt-secret-for-testing-only"

    def test_valid_token_returns_username(self):
        token = create_access_token(username="alice", secret=self.SECRET)
        assert decode_access_token(token, self.SECRET) == "alice"

    def test_expired_token_raises_token_expired(self):
        token = create_access_token(
            username="alice", secret=self.SECRET, expires_minutes=-1
        )
        with pytest.raises(TokenExpiredError) as exc_info:
            decode_access_token(token, self.SECRET)
        assert exc_info.value.code == "TOKEN_EXPIRED"
        assert exc_info.value.status_code == 401

    def test_malformed_token_raises_authentication_error(self):
        with pytest.raises(AuthenticationError) as exc_info:
            decode_access_token("not-a-jwt", self.SECRET)
        assert exc_info.value.code == "INVALID_CREDENTIALS"
        assert not isinstance(exc_info.value, TokenExpiredError)

    def test_wrong_secret_raises_authentication_error(self):
        token = create_access_token(username="alice", secret=self.SECRET)
        with pytest.raises(AuthenticationError) as exc_info:
            decode_access_token(token, "a-different-secret")
        assert exc_info.value.code == "INVALID_CREDENTIALS"

    def test_token_without_subject_raises_authentication_error(self):
        """A signed token carrying no `sub` identifies nobody."""
        token = jwt.encode(
            {"exp": datetime.now(UTC) + timedelta(minutes=5)},
            self.SECRET,
            algorithm="HS256",
        )
        with pytest.raises(AuthenticationError) as exc_info:
            decode_access_token(token, self.SECRET)
        assert exc_info.value.code == "INVALID_CREDENTIALS"
