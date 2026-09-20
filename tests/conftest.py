"""Pytest configuration and shared fixtures.

Config loads lazily, so nothing here has to run before the app modules are
imported: the test config is written by a fixture, not at import time.
"""

import copy
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import tomli_w
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from leggen.commands.server import create_app
from leggen.repositories import run_migrations
from leggen.utils.config import config
from leggen.utils.paths import path_manager

# bcrypt hash of "testpassword"
TEST_PASSWORD_HASH = "$2b$12$VNxOF9xF676elZu5M9pW7eYZ.p.qVJsh/n6jIsHE3iNnHWBtUxr/y"
TEST_API_KEY = "lgn_test-api-key-for-testing"


def reset_config_singleton() -> None:
    """Clear the config singleton so the next access reloads from
    LEGGEN_CONFIG_FILE.

    `Config()` is a process-global singleton that other modules hold by
    reference, so its fields are cleared in place rather than replacing the
    instance.
    """
    config._config = None
    config._config_model = None
    config._config_path = None


@pytest.fixture(scope="session")
def test_key_path(tmp_path_factory) -> Path:
    """An RSA private key for the EnableBanking section of the test config.

    Config validation only checks that the file exists, but the sync service
    signs its API JWT with it, so it is a real key rather than a placeholder.
    """
    key_path = tmp_path_factory.mktemp("keys") / "enablebanking.pem"
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    return key_path


@pytest.fixture(scope="session")
def base_config(test_key_path) -> dict:
    """The canonical test configuration, copied fresh for every test."""
    return {
        "auth": {
            "username": "testuser",
            "password_hash": TEST_PASSWORD_HASH,
            "api_key": TEST_API_KEY,
            "jwt_secret": "test-jwt-secret-for-testing-only",
            "jwt_expiry_minutes": 60,
        },
        "enablebanking": {
            "application_id": "test-app-id",
            "key_path": str(test_key_path),
            "url": "https://api.enablebanking.com",
        },
        "scheduler": {"sync": {"enabled": True, "hour": 3, "minute": 0}},
    }


@pytest.fixture(autouse=True)
def test_config(base_config, tmp_path_factory, monkeypatch):
    """Give every test its own copy of the config, on disk and in the singleton.

    Tests may mutate `test_config._config` or save through `update_section`;
    both touch only this test's copy. The singleton is cleared afterwards so
    nothing leaks into the next test. The file lives outside `tmp_path`, which
    some CLI tests assert stays empty.
    """
    data = copy.deepcopy(base_config)
    config_file = tmp_path_factory.mktemp("config") / "config.toml"
    config_file.write_bytes(tomli_w.dumps(data).encode())
    monkeypatch.setenv("LEGGEN_CONFIG_FILE", str(config_file))

    config._config = data
    config._config_model = None
    config._config_path = str(config_file)
    try:
        yield config
    finally:
        reset_config_singleton()


@pytest.fixture
def mock_db_path(tmp_path) -> Path:
    """Point the path manager at a fresh, migrated SQLite database."""
    db_path = tmp_path / "leggen.db"
    original_database_path = path_manager._database_path
    path_manager.set_database_path(db_path)
    run_migrations()
    try:
        yield db_path
    finally:
        path_manager._database_path = original_database_path


@pytest.fixture
def fastapi_app(mock_db_path):
    """The FastAPI application, wired to the temporary database."""
    return create_app()


@pytest.fixture
def api_client(fastapi_app):
    """Authenticated test client."""
    client = TestClient(fastapi_app)
    client.headers["X-API-Key"] = TEST_API_KEY
    return client


@pytest.fixture
def raw_api_client(fastapi_app):
    """Authenticated test client that returns 500 responses instead of
    re-raising unhandled route exceptions — for testing the global handlers."""
    client = TestClient(fastapi_app, raise_server_exceptions=False)
    client.headers["X-API-Key"] = TEST_API_KEY
    return client


@pytest.fixture
def override(fastapi_app):
    """Replace a FastAPI dependency for the duration of one test.

    For the external boundary (EnableBanking) and for injecting failures;
    repositories are otherwise exercised against the real temporary database.
    """

    def _override(dependency, replacement):
        fastapi_app.dependency_overrides[dependency] = lambda: replacement
        return replacement

    try:
        yield _override
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.fixture
def mock_account_repo():
    return MagicMock()


@pytest.fixture
def mock_balance_repo():
    return MagicMock()


@pytest.fixture
def mock_transaction_repo():
    return MagicMock()


@pytest.fixture
def sample_bank_data():
    """Sample bank/ASPSP data for testing."""
    return {
        "aspsps": [
            {
                "name": "Revolut",
                "country": "GB",
                "bic": "REVOLT21",
                "logo": "https://example.com/revolut.png",
            },
            {
                "name": "Banco BPI",
                "country": "PT",
                "bic": "BBPIPTPL",
                "logo": "https://example.com/bpi.png",
            },
        ]
    }


@pytest.fixture
def sample_account_data():
    """Sample account data for testing."""
    return {
        "id": "test-account-123",
        "institution_id": "Revolut",
        "status": "READY",
        "iban": "LT313250081177977789",
        "created": "2024-02-13T23:56:00Z",
        "last_accessed": "2025-09-01T09:30:00Z",
    }
