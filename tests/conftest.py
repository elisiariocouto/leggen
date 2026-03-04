"""Pytest configuration and shared fixtures."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import tomli_w
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# Create a test RSA key pair for EnableBanking BEFORE any app imports
_test_config_dir = tempfile.mkdtemp(prefix="leggen_test_")
_test_key_path = Path(_test_config_dir) / "test_key.pem"

_test_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_test_key_path.write_bytes(
    _test_private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
)

_test_config_path = Path(_test_config_dir) / "config.toml"

# Create minimal test config
_config_data = {
    "enablebanking": {
        "application_id": "test-app-id",
        "key_path": str(_test_key_path),
        "url": "https://api.enablebanking.com",
    },
    "database": {"sqlite": True},
    "scheduler": {"sync": {"enabled": True, "hour": 3, "minute": 0}},
}

with open(_test_config_path, "wb") as f:
    tomli_w.dump(_config_data, f)

# Set environment variable BEFORE any app imports that trigger config loading
os.environ["LEGGEN_CONFIG_FILE"] = str(_test_config_path)

# Reset the Config singleton's cached data so it reloads from our test config.
# We must NOT reset _instance itself, because other modules import the `config`
# singleton object by reference — resetting _instance would leave them with a stale ref.
from leggen.utils.config import Config, config  # noqa: E402

config._config = None
config._config_model = None
config._config_path = None

# Now it's safe to import app modules that trigger config loading
from fastapi.testclient import TestClient  # noqa: E402

from leggen.commands.server import create_app  # noqa: E402


def pytest_configure(config):
    """Pytest hook called before test collection."""
    # Ensure test config is set
    os.environ["LEGGEN_CONFIG_FILE"] = str(_test_config_path)


def pytest_unconfigure(config):
    """Pytest hook called after all tests."""
    # Cleanup test config directory
    if Path(_test_config_dir).exists():
        shutil.rmtree(_test_config_dir)


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "leggen"
        config_dir.mkdir(parents=True, exist_ok=True)
        yield config_dir


@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_path = Path(tmp_file.name)
        yield db_path
    # Clean up the temporary database file after test
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def test_key_path():
    """Return the path to the test RSA private key."""
    return _test_key_path


@pytest.fixture
def mock_config(temp_config_dir, test_key_path):
    """Mock configuration for testing."""
    config_data = {
        "enablebanking": {
            "application_id": "test-app-id",
            "key_path": str(test_key_path),
            "url": "https://api.enablebanking.com",
        },
        "database": {"sqlite": True},
        "scheduler": {"sync": {"enabled": True, "hour": 3, "minute": 0}},
    }

    config_file = temp_config_dir / "config.toml"
    with open(config_file, "wb") as f:
        tomli_w.dump(config_data, f)

    # Mock the config path
    with patch.object(Config, "load_config") as mock_load:
        mock_load.return_value = config_data
        config = Config()
        config._config = config_data
        config._config_path = str(config_file)
        yield config


@pytest.fixture
def fastapi_app(mock_db_path):
    """Create FastAPI test application."""
    # Patch the database path for the app
    with patch(
        "leggen.utils.paths.path_manager.get_database_path", return_value=mock_db_path
    ):
        app = create_app()
        yield app


@pytest.fixture
def api_client(fastapi_app):
    """Create FastAPI test client."""
    return TestClient(fastapi_app)


@pytest.fixture
def mock_account_repo():
    """Create mock AccountRepository for testing."""
    from unittest.mock import MagicMock

    return MagicMock()


@pytest.fixture
def mock_balance_repo():
    """Create mock BalanceRepository for testing."""
    from unittest.mock import MagicMock

    return MagicMock()


@pytest.fixture
def mock_transaction_repo():
    """Create mock TransactionRepository for testing."""
    from unittest.mock import MagicMock

    return MagicMock()


@pytest.fixture
def mock_db_path(temp_db_path):
    """Mock the database path to use temporary database for testing."""
    from leggen.utils.paths import path_manager

    # Set the path manager to use the temporary database
    original_database_path = path_manager._database_path
    path_manager.set_database_path(temp_db_path)

    # Create all tables so tests can use them
    from leggen.repositories import ensure_tables

    ensure_tables()

    try:
        yield temp_db_path
    finally:
        # Restore original path
        path_manager._database_path = original_database_path


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


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing (EnableBanking format)."""
    return {
        "transactions": [
            {
                "transaction_id": "txn-123",
                "entry_reference": "ref-123",
                "booking_date": "2025-09-01",
                "value_date": "2025-09-01",
                "transaction_amount": {"amount": "-10.50", "currency": "EUR"},
                "remittance_information": ["Coffee Shop Payment"],
                "status": "BOOK",
            }
        ]
    }
