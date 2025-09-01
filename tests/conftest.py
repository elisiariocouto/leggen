"""Pytest configuration and shared fixtures."""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from leggend.main import create_app
from leggend.config import Config


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "leggen"
        config_dir.mkdir(parents=True, exist_ok=True)
        yield config_dir


@pytest.fixture 
def mock_config(temp_config_dir):
    """Mock configuration for testing."""
    config_data = {
        "gocardless": {
            "key": "test-key",
            "secret": "test-secret", 
            "url": "https://bankaccountdata.gocardless.com/api/v2"
        },
        "database": {
            "sqlite": True
        },
        "scheduler": {
            "sync": {
                "enabled": True,
                "hour": 3,
                "minute": 0
            }
        }
    }
    
    config_file = temp_config_dir / "config.toml"
    with open(config_file, "wb") as f:
        import tomli_w
        tomli_w.dump(config_data, f)
    
    # Mock the config path
    with patch.object(Config, 'load_config') as mock_load:
        mock_load.return_value = config_data
        config = Config()
        config._config = config_data
        config._config_path = str(config_file)
        yield config


@pytest.fixture
def mock_auth_token(temp_config_dir):
    """Mock GoCardless authentication token."""
    auth_data = {
        "access": "mock-access-token",
        "refresh": "mock-refresh-token"
    }
    
    auth_file = temp_config_dir / "auth.json" 
    with open(auth_file, "w") as f:
        json.dump(auth_data, f)
    
    return auth_data


@pytest.fixture
def fastapi_app():
    """Create FastAPI test application."""
    return create_app()


@pytest.fixture
def api_client(fastapi_app):
    """Create FastAPI test client."""
    return TestClient(fastapi_app)


@pytest.fixture
def sample_bank_data():
    """Sample bank/institution data for testing."""
    return [
        {
            "id": "REVOLUT_REVOLT21",
            "name": "Revolut",
            "bic": "REVOLT21", 
            "transaction_total_days": 90,
            "countries": ["GB", "LT"]
        },
        {
            "id": "BANCOBPI_BBPIPTPL",
            "name": "Banco BPI",
            "bic": "BBPIPTPL",
            "transaction_total_days": 90, 
            "countries": ["PT"]
        }
    ]


@pytest.fixture
def sample_account_data():
    """Sample account data for testing."""
    return {
        "id": "test-account-123",
        "institution_id": "REVOLUT_REVOLT21", 
        "status": "READY",
        "iban": "LT313250081177977789",
        "created": "2024-02-13T23:56:00Z",
        "last_accessed": "2025-09-01T09:30:00Z"
    }


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing.""" 
    return {
        "transactions": {
            "booked": [
                {
                    "internalTransactionId": "txn-123",
                    "bookingDate": "2025-09-01",
                    "valueDate": "2025-09-01", 
                    "transactionAmount": {
                        "amount": "-10.50",
                        "currency": "EUR"
                    },
                    "remittanceInformationUnstructured": "Coffee Shop Payment"
                }
            ],
            "pending": []
        }
    }