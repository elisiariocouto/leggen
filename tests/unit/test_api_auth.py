"""Tests for auth API endpoints and authentication dependency."""

import pytest
from fastapi.testclient import TestClient

from leggen.utils.auth import create_access_token


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
class TestAuthStatus:
    """Test GET /api/v1/auth/status endpoint."""

    def test_auth_status_returns_enabled(self, fastapi_app, mock_db_path):
        """Test auth status endpoint returns auth_enabled: true without credentials."""
        client = TestClient(fastapi_app)
        response = client.get("/api/v1/auth/status")
        assert response.status_code == 200
        assert response.json() == {"auth_enabled": True}


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
        """Test that an invalid JWT token returns 401."""
        client = TestClient(fastapi_app)
        response = client.get(
            "/api/v1/accounts",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_expired_jwt(self, fastapi_app, mock_db_path):
        """Test that an expired JWT token returns 401."""
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
