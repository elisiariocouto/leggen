"""Tests for accounts API endpoints."""

from unittest.mock import patch

import pytest

from leggen.repositories import AccountRepository, BalanceRepository


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

        fastapi_app.dependency_overrides[AccountRepository] = lambda: mock_account_repo
        fastapi_app.dependency_overrides[BalanceRepository] = lambda: mock_balance_repo

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

        fastapi_app.dependency_overrides[AccountRepository] = lambda: mock_account_repo

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

        fastapi_app.dependency_overrides[AccountRepository] = lambda: mock_account_repo

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.put(
                "/api/v1/accounts/nonexistent",
                json={"display_name": "New Name"},
            )

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 404

    def test_delete_account_success(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_db_path,
        mock_account_repo,
    ):
        """Test successful deletion of an account."""
        mock_account_repo.delete_account.return_value = True

        fastapi_app.dependency_overrides[AccountRepository] = lambda: mock_account_repo

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.delete("/api/v1/accounts/test-account-123")

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] == "test-account-123"
        mock_account_repo.delete_account.assert_called_once_with(
            "test-account-123", True
        )

    def test_delete_account_not_found(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_db_path,
        mock_account_repo,
    ):
        """Test deleting a non-existent account."""
        mock_account_repo.delete_account.return_value = False

        fastapi_app.dependency_overrides[AccountRepository] = lambda: mock_account_repo

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.delete("/api/v1/accounts/nonexistent")

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 404

    def test_deleted_account_still_returned(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_db_path,
        mock_account_repo,
        mock_balance_repo,
    ):
        """Test that soft-deleted accounts still appear in GET /accounts."""
        mock_accounts = [
            {
                "id": "active-account",
                "institution_id": "REVOLUT_REVOLT21",
                "status": "READY",
                "iban": "LT313250081177977789",
                "name": "Active Account",
                "display_name": None,
                "created": "2024-02-13T23:56:00Z",
                "last_accessed": "2025-09-01T09:30:00Z",
            },
            {
                "id": "deleted-account",
                "institution_id": "REVOLUT_REVOLT21",
                "status": "DELETED",
                "iban": "LT313250081177977790",
                "name": "Deleted Account",
                "display_name": "My Old Account",
                "created": "2024-01-01T00:00:00Z",
                "last_accessed": "2025-06-01T00:00:00Z",
            },
        ]

        mock_account_repo.get_accounts.return_value = mock_accounts
        mock_balance_repo.get_balances.return_value = []

        fastapi_app.dependency_overrides[AccountRepository] = lambda: mock_account_repo
        fastapi_app.dependency_overrides[BalanceRepository] = lambda: mock_balance_repo

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/accounts")

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        statuses = {a["id"]: a["status"] for a in data}
        assert statuses["active-account"] == "READY"
        assert statuses["deleted-account"] == "DELETED"

    def test_delete_account_keep_data(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_db_path,
        mock_account_repo,
    ):
        """Test deleting an account while keeping transaction and balance data."""
        mock_account_repo.delete_account.return_value = True

        fastapi_app.dependency_overrides[AccountRepository] = lambda: mock_account_repo

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.delete(
                "/api/v1/accounts/test-account-123?delete_data=false"
            )

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] == "test-account-123"
        mock_account_repo.delete_account.assert_called_once_with(
            "test-account-123", False
        )
