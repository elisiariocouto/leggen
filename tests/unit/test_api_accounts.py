"""Tests for accounts API endpoints."""

from unittest.mock import patch

import pytest

from leggen.api.dependencies import (
    get_account_repository,
    get_balance_repository,
)


@pytest.mark.api
class TestAccountsAPI:
    """Test account-related API endpoints."""

    def test_get_all_accounts_success(
        self,
        fastapi_app,
        api_client,
        mock_config,
        sample_account_data,
        mock_db_path,
        mock_account_repo,
        mock_balance_repo,
    ):
        """Test successful retrieval of all accounts from database."""
        mock_accounts = [
            {
                "id": "test-account-123",
                "institution_id": "REVOLUT_REVOLT21",
                "status": "READY",
                "iban": "LT313250081177977789",
                "name": "Personal Account",
                "display_name": None,
                "created": "2024-02-13T23:56:00Z",
                "last_accessed": "2025-09-01T09:30:00Z",
            }
        ]

        mock_balances = [
            {
                "id": 1,
                "account_id": "test-account-123",
                "bank": "REVOLUT_REVOLT21",
                "status": "active",
                "iban": "LT313250081177977789",
                "amount": 100.50,
                "currency": "EUR",
                "type": "interimAvailable",
                "timestamp": "2025-09-01T09:30:00Z",
            }
        ]

        mock_account_repo.get_accounts.return_value = mock_accounts
        mock_balance_repo.get_balances.return_value = mock_balances

        fastapi_app.dependency_overrides[get_account_repository] = lambda: (
            mock_account_repo
        )
        fastapi_app.dependency_overrides[get_balance_repository] = lambda: (
            mock_balance_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/accounts")

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        account = data[0]
        assert account["id"] == "test-account-123"
        assert account["institution_id"] == "REVOLUT_REVOLT21"
        assert len(account["balances"]) == 1
        assert account["balances"][0]["amount"] == 100.50

    def test_update_account_display_name_success(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_db_path,
        mock_account_repo,
    ):
        """Test successful update of account display name."""
        mock_account = {
            "id": "test-account-123",
            "institution_id": "REVOLUT_REVOLT21",
            "status": "READY",
            "iban": "LT313250081177977789",
            "name": "Personal Account",
            "display_name": None,
            "created": "2024-02-13T23:56:00Z",
            "last_accessed": "2025-09-01T09:30:00Z",
        }

        mock_account_repo.get_account.return_value = mock_account
        mock_account_repo.persist.return_value = mock_account

        fastapi_app.dependency_overrides[get_account_repository] = lambda: (
            mock_account_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.put(
                "/api/v1/accounts/test-account-123",
                json={"display_name": "My Custom Account Name"},
            )

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-account-123"
        assert data["display_name"] == "My Custom Account Name"

    def test_update_account_not_found(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_db_path,
        mock_account_repo,
    ):
        """Test updating non-existent account."""
        mock_account_repo.get_account.return_value = None

        fastapi_app.dependency_overrides[get_account_repository] = lambda: (
            mock_account_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.put(
                "/api/v1/accounts/nonexistent",
                json={"display_name": "New Name"},
            )

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 404
